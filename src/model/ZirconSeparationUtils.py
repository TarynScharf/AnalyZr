from datetime import datetime

import cv2
import json
import math
import matplotlib
import numpy as np
import os
import pyefd
from shapely.geometry import LineString

from matplotlib import pyplot as plt

from shapely.geometry  import Polygon

from skimage.morphology import remove_small_objects, binary_erosion, binary_dilation,binary_opening
from skimage.measure import regionprops
from skimage.measure import label

from statistics import mean

from src.model import FileUtils
from src.model.composite_contour import CompositeContour
from src.model.json_data import JsonData


def getScale(json_file_path, tag):
    sampleid = JsonData.get_sample_id_from_file_path(json_file_path)
    json_folder_path = FileUtils.get_folder(json_file_path)

    spot_length_list = []
    scale_length_list=[]
    for path, folder, files in os.walk(json_folder_path):
        for name in files:
            sample = name.split('_')[0]
            ext =os.path.splitext(name)[1]
            if sample == sampleid and ext == '.json':
                with open(os.path.join(json_folder_path, name), errors='ignore') as jFile:
                    data = json.load(jFile)
                for region in data['regions']:
                    if region['type'] == 'RECTANGLE':
                        #originally they were called SPOT. Later this was changed to SPOT AREA.
                        #This accomodates current and historical data
                        if region['tags'][0]==tag or region['tags'][0]=="SPOT AREA":
                            spot_length_list.append(region['boundingBox']['height'])
                            spot_length_list.append(region['boundingBox']['width'])
                    elif region['type']=="scale" and region['tags'][0]==tag:
                        scale_length_list.append(region['boundingBox']['height'])
    if len(spot_length_list)==0:
        return None

    aveLength = mean(spot_length_list)
    return aveLength

def removeSmallObjects(img, factor = 6):
    
    labelim = label(img, background=0, connectivity=None)
    props = regionprops(labelim)
    areaList = []
    for x in range (0,len(props)):
        areaList.append(props[x].area)

    areaList.sort(reverse=True)
    if len(areaList)>0:
        maxArea = areaList[0]
        min_size = maxArea/factor
        remSmall = remove_small_objects(labelim,min_size, in_place=False)
    
    return remSmall

def simplify(poly,inside, reduction_factor = 1):
    if inside ==True:
        factor = 1
    else:
        factor = reduction_factor
    input_contour = np.insert(poly, len(poly), poly[0], 0)
    count = int(len(poly)*factor)
    dxy = np.diff(input_contour, axis=0) #get the incremental difference between each x and y for each point in the contour.
    # If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1)) #at each increment, calculate displacement, like pythagoras theorem
    #t = np.cumsum(dt)
    t = np.concatenate([([0.]), np.cumsum(dt)]) #add a 0 onto the cumulative displacement, I assume to represent starting point with no displacement
    T = t[-1] #total  displacement is the last cumulative value in t 
    
    spacing = T/count #equidistance points in a polyline should have this spacing.
    newPoints = []

    #for i in range(0,count):

    for j in range(0,len(poly)):
        pDist = j * spacing  # ideal point distance along polyline
        if j ==0:
            newPoints.append(poly[j]) #keep the starting point of the polyline
            continue #this won't work for the first point, because j-1 = the full displacement of the entire polyline
        prevDist = t[j-1]
        dist = t[j]
        displacement = dist-prevDist

        x = None
        y = None

        if dist == pDist:
            newPoints.append(poly[j]) #this is an unlikely scenario
        elif prevDist <pDist and dist<pDist: #so if this point falls between the ideal spacing
            continue
        elif prevDist <pDist and dist>pDist: #so if this point falls between the ideal spacing

            diff = pDist-prevDist
            diffRatio = displacement/diff

            if poly[j-1][0] < poly[j][0]:
                x = poly[j-1][0] + (poly[j][0] -poly[j-1][0])/diffRatio
            elif poly[j-1][0] > poly[j][0]:
                x = poly[j - 1][0] - (poly[j][0] - poly[j - 1][0]) / diffRatio
            elif poly[j-1][0] == poly[j][0]:
                x = poly[j][0]

            if poly[j-1][1]<poly[j][1]:
                y = poly[j-1][1] + (poly[j][1] -poly[j-1][1])/diffRatio
            elif poly[j-1][1] > poly[j][1]:
                y = poly[j - 1][1] - (poly[j][1] - poly[j - 1][1]) / diffRatio
            elif poly[j-1][1] == poly[j][1]:
                y = poly[j][1]

            newPoints.append([x,y])

    return newPoints

def get_efd_parameters_for_simplified_contour(contour, has_parent, filter_fn,simplify, ORDER_FACTOR =0.2):
    assert not is_contour_closed(contour)

    #Takes an object of type CompositeContour. It uses the ComplexContour.original_points.
    #return: updated CompositeContour object

    number_of_points = len(contour)
    if len(contour) < 50:
        ORDER_FACTOR= 1

    order = int(number_of_points*ORDER_FACTOR)
    if order ==0:
        return None
    if filter_fn is not None and not filter_fn(contour):
        return None

    input_contour = ensure_contour_is_closed(contour)

    coefficients = pyefd.elliptic_fourier_descriptors(input_contour,order)
    closed_contour = ensure_contour_is_closed(contour)
    locus = pyefd.calculate_dc_coefficients(closed_contour)
    if simplify == True:
        reconstructed_points = pyefd.reconstruct_contour(coefficients, locus, number_of_points) # simplify (contour,has_parent)
    else:
        reconstructed_points = contour
    reconstructed_points_without_duplicates = remove_duplicate_points(reconstructed_points)
    if len(reconstructed_points_without_duplicates)<2:
        return None

    assert not is_contour_closed(reconstructed_points_without_duplicates)

    return coefficients,locus, reconstructed_points_without_duplicates

def remove_duplicate_points(reconstructed_points):
    nonduplicate_points = []
    prev= reconstructed_points[-1]
    for point in reconstructed_points:
        if not np.allclose(prev, point):
            nonduplicate_points.append(point)
        prev = point
    '''prev_y = reconstructed_points[-1][1]
    for x,y in reconstructed_points:
        if x != prev_x or y != prev_y:
            nonduplicate_points.append((x,y))
        prev_x = x
        prev_y = y'''

    return nonduplicate_points


def InsidePolygon(coord1, coord2, polygon):
    poly = Polygon(polygon)
    line = LineString([coord1,coord2])
    is_inside = poly.buffer(1).contains(line)

    is_partially_inside = line.crosses(poly)

    '''x1 = coord1[0]
    y1 = coord1[1]
    x2 = coord2[0]
    y2 = coord2[1]

    xDist = abs(x1-x2)
    xInc = xDist/4
    yDist = abs(y1-y2)
    yInc = yDist/4

    if x1<x2:
        xpoint = x1 + xInc
        if y1<y2:
            ypoint = y1+ yInc
        else:
            ypoint = y1-yInc
    else:
        xpoint = x2 + xInc
        if y2<y1:
            ypoint = y2 + yInc
        else:
            ypoint = y2-yInc


    points = []

   
    for i in range(2): #let's calculate a few points along the straight-line path between the two nodes, and check that they all lie within the polygon.
        points.append([xpoint,ypoint])
        
        if x1<x2:
            xpoint = xpoint + xInc
            if y1<y2:
                ypoint = ypoint+ yInc
            else:
                ypoint = ypoint-yInc
        else:
            xpoint = xpoint + xInc
            if y2<y1:
                ypoint = ypoint + yInc
            else:
                ypoint = ypoint-yInc
        
    #now check if all the points in the array are inside the polygon. 
    #I intensionally did not include the points on the edges.
    #boundary = matplotlib.path.Path(_reconstructionList[0], closed = True) #let's use the outer most boundary in all  cases. This was originally designed for a single boundary. This might have to be changed for nested boundaries
    boundary = matplotlib.path.Path(polygon, closed = True)
    insidePoly = boundary.contains_points(points, radius=0.1)
    allPoints = False
    somePoints = False
    if all(item == True for item in insidePoly):
        allPoints = True
    if any(item == True for item in insidePoly):
        somePoints = True
    #print('insidePoly: ', insidePoly)'''
    return is_inside, is_partially_inside #allPoints, somePoints

def determineQuadrant(point, contour):
    #print('cnt: ', contour)
    #print('point: ', point)
    x1 = point[0]
    y1 = point[1]
      
    #get the vector of the point:
    iterator = contour.index(point)
    
    #print('iterator: ', iterator)
    L = iterator -2
    #R = iterator + 2
    
    #deal with cases where the points are on the ends of the contours, Contours are closed.
    if L < 0:
        L = len(contour)-L
    if L> len(contour):
        L = L-len(contour)
    
    #if R < 0:
    #    R = len(contour)-R
    #if R> len(contour):
    #    R =R-len(contour) 

    pL = contour[L]
    #pR = contour[R]
    #startX = pL[0] + (pR[0]-pL[0])/2
    #startY = pL[1] + (pR[1]-pL[1])/2 
    startX = pL[0]
    startY = pL[1]
    deltaX = x1-startX
    deltaY = y1-startY
    
    #determine quadrant
    quadrant = 0
    if deltaX >=0:
        if deltaY>=0:
            quadrant = 1 #0-90
        else:
            quadrant = 2 #270-360
    else:
        if deltaY>=0:
            quadrant = -2 #90-180
        else:
            quadrant = -1 #180-270
    return quadrant

def calculate_theta(v1,v2):
    dot = np.dot(v1, v2)
    cross = np.cross(v1, v2)
    theta = np.arctan2(cross, dot) * 180 / np.pi
    return theta

def process_contour_group_for_node_pairs(contour_group):
    usedNodes = set()
    node_pairs = []
    distList_for_child_contours =[]

    if len(contour_group) > 1:
        # if it's a family of nested contours, preferentially link nodes on child contours
        distList_for_child_contours = find_node_pairs_in_child_contours(contour_group)
        #link_nodes(distList_for_child_contours, contour_group,usedNodes,node_pairs)

    distList_parent_contours = find_node_pairs_in_parent_contour(contour_group[0],usedNodes)
    distList = distList_for_child_contours + distList_parent_contours

    link_nodes(distList, contour_group,usedNodes,node_pairs)

    return node_pairs

def find_node_pairs_in_child_contours(contour_group):
    internode_distance_list=[]
    for i in range(0,len(contour_group)):
        contour1 = contour_group[i]
        contour1_nodes = list(contour1.max_curvature_coordinates)
        contour1_bisectors = list(contour1.max_bisectors)
        candidate_nodes = []
        candidate_bisectors = []
        for j in range(i+1, len(contour_group)):
            contour2 = contour_group[j]
            candidate_nodes += list(contour2.max_curvature_coordinates)
            candidate_bisectors += list(contour2.max_bisectors)

        # Now compare the distance between every node in the internal contour under consideration,
        # and every other contour node. Find the closest.
        if contour1_nodes == [] or candidate_nodes == []:
            continue  # if there are no nodes, consider the next contour in the group. This should be impossible though, because it's already been screened for above
        for i in range(len(contour1_nodes)):
            node1_x = contour1_nodes[i][0]
            node1_y = contour1_nodes[i][1]
            node1_bisector = contour1_bisectors[i]
            for j in range(len(candidate_nodes)):
                node2_x = candidate_nodes[j][0]
                node2_y = candidate_nodes[j][1]
                node2_bisector = candidate_bisectors[j]
                diff_x = (node1_x - node2_x) ** 2
                diff_y = (node1_y - node2_y) ** 2
                distance = math.sqrt(diff_x + diff_y)
                internode_distance_list.append([contour1_nodes[i], candidate_nodes[j], distance, node1_bisector, node2_bisector])
    return internode_distance_list

def find_node_pairs_in_parent_contour(contour,usedNodes):
    internode_distance_list=[]
    parent_nodes = list(contour.max_curvature_coordinates)
    parent_bisectors = list(contour.max_bisectors)
    for i in range(len(parent_nodes)):
        if parent_nodes[i] in usedNodes:
            continue
        node1_x = parent_nodes[i][0]
        node1_y = parent_nodes[i][1]
        node1_bisector = parent_bisectors[i]


        for j in range(i+1,len(parent_nodes)):

            if parent_nodes[j] not in usedNodes:
                node2_x = parent_nodes[j][0]
                node2_y = parent_nodes[j][1]
                node2_bisector = parent_bisectors[j]
                diff_x = (node1_x - node2_x) ** 2
                diff_y = (node1_y - node2_y) ** 2
                distance = math.sqrt(diff_x + diff_y)
                internode_distance_list.append([parent_nodes[i], parent_nodes[j], distance, node1_bisector, node2_bisector])

    return internode_distance_list

def link_nodes(distList,contour_group,usedNodes, node_pairs):
    MAXIMUM_ANGLE = 80

    sortDistList = sorted(distList, key=lambda x: x[2], reverse=False)

    for entry in sortDistList:
        node1 = entry[0]
        node2 = entry[1]

        if node1 in usedNodes or node2 in usedNodes:
            continue

        # if it is a potential  node  pair, check  that it doesn't cut across any pre-existing node pairs
        flag = 0
        test_breakline = LineString([node1, node2])
        for pair in node_pairs:
            pair_string = LineString(pair)
            if pair_string.crosses(test_breakline):
                flag = 1
                break
        if flag==1:
            continue

        # check that the angles of the break line and bisectors are acceptable
        bisector1 = entry[3]
        bisector2 = entry[4]
        theta1 = calculate_theta(bisector1, np.array(node2) - np.array(node1))
        theta2 = calculate_theta(bisector2, np.array(node1) - np.array(node2))

        if abs(theta1) > MAXIMUM_ANGLE or abs(theta2) > MAXIMUM_ANGLE:  # Angle is chosen emperically
            continue

        allInsideParent, someInsideParent = InsidePolygon(node1, node2, contour_group[0].reconstructed_points)
        if not allInsideParent:  # firstly, is the polyline inside the parent contour?
            continue

        for i in range(1, len(contour_group)):
            allInsideChild, someInsideChild = InsidePolygon(node1, node2, contour_group[i].reconstructed_points)
            if allInsideChild == True or someInsideChild == True:  # secondly, does it go inside an internal hole?
                flag = 1
                break

        if flag == 1:
            continue

        if not filter_pairs_with_length_to_volume_ratio(node1,node2, contour_group):
            continue

        node_pairs.append([node1, node2])
        usedNodes.add(node1)
        usedNodes.add(node2)

def is_contour_closed(contour):
    return contour[0][0] == contour[-1][0] and contour[0][1] == contour[-1][1]

def ensure_contour_is_closed(contour):
    if is_contour_closed(contour):
        return contour

    contour_copy = np.copy(contour)
    closed_contour = np.insert(contour_copy, len(contour_copy), contour_copy[0], 0)
    return closed_contour

def ensure_contour_is_open(contour):
    if not is_contour_closed(contour):
        return contour

    contour_copy = np.copy(contour)
    return contour_copy[:-1]

def calculate_curvature_and_find_maxima(i, contour, hierarchy, polygon_filter,simplify):
    cnt = np.squeeze(contour).tolist()
    composite_contour = CompositeContour(np.squeeze(contour), i)

    if hierarchy.ndim == 1:
        composite_contour.has_parent = hierarchy[3] != -1
    else:
        composite_contour.has_parent = hierarchy[i][3] != -1

    if len(cnt) < 3:  # if it is a straight line or a point, it is not a closed contour and thus not of interest
        composite_contour.keep_contour = False
        return composite_contour

    get_coefficients_result = get_efd_parameters_for_simplified_contour(composite_contour.original_points, composite_contour.has_parent, polygon_filter,simplify)

    if get_coefficients_result is None:
        composite_contour.keep_contour = False
        return composite_contour

    composite_contour.coefficients, composite_contour.locus, composite_contour.reconstructed_points = get_coefficients_result

    composite_contour.curvature_values, bisection_vectors= calculate_angle(composite_contour.reconstructed_points)

    curvature_maxima_values, curvature_maxima_x, curvature_maxima_y, non_maxima_curvature,maxima_bisectors= FindCurvatureMaxima(composite_contour.curvature_values, composite_contour.cumulative_distance,bisection_vectors,
        composite_contour.reconstructed_points)
    node_curvature_values, node_x, node_y,node_bisectors = IdentifyContactPoints(curvature_maxima_values, curvature_maxima_x, curvature_maxima_y,maxima_bisectors, non_maxima_curvature)

    composite_contour.max_curvature_values = node_curvature_values
    composite_contour.max_bisectors = node_bisectors
    composite_contour.max_curvature_coordinates = list(zip(node_x, node_y))

    if node_curvature_values == [] or node_x == [] or node_y == []:
        composite_contour.keep_contour = False


    return composite_contour

def calculate_angle(contour):
    contour = ensure_contour_is_open(contour)

    v1 = contour - np.roll(contour, shift=1, axis=0)
    v2 = np.roll(contour, shift=-1, axis=0) - contour
    #calculate angles
    thetas = []
    for i, (s1, s2) in enumerate(zip(v1,v2)):
        theta = calculate_theta(s1,s2)
        thetas.append(theta)

    v1_norm_2d=[]
    v2_norm_2d=[]
    v1_norm = np.linalg.norm(v1, axis=1)
    v2_norm = np.linalg.norm(v2, axis=1)
    for i in range(len(v1_norm)):
        v1_norm_2d.append([v1_norm[i],v1_norm[i]])
        v2_norm_2d.append([v2_norm[i], v2_norm[i]])

    v1_normalised = np.divide(v1,np.array(v1_norm_2d))

    v2_normalised = np.divide(v2, np.array(v2_norm_2d))

    v3 = v1_normalised + v2_normalised

    # rotate by 90 degrees clockwise
    bisection_vectors = np.flip(np.multiply(v3, np.array([-1, 1])), axis=1)

    return thetas,bisection_vectors

def calculateK(con, coef):
    """
    Note this has a subtle bug in it, where the K value sometimes gets shifted
    for long contours. Despite > 10 hours work we've been unable to track down
    why this occurs.
    """
    input_contour = ensure_contour_is_closed(con)
    dxy = np.diff(input_contour, axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
    t = np.cumsum(dt)
    T = t[-1]  # total  displacement is the last cumulative value in t
    t = np.roll(t, shift=1)

    all_K = []

    orders = np.arange(1, len(coef) + 1)
    d_theta = 2 * np.pi * orders / T

    for cumulative_displacement in t:
        theta = d_theta * cumulative_displacement
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        sin_theta_d_theta = sin_theta * d_theta
        cos_theta_d_theta = cos_theta * d_theta
        sin_theta_d_theta_sq = sin_theta_d_theta * d_theta
        cos_theta_d_theta_sq = cos_theta_d_theta * d_theta

        a = coef[:,0]
        b = coef[:,1]
        c = coef[:,2]
        d = coef[:,3]

        dxs = -a*sin_theta_d_theta + b*cos_theta_d_theta
        dys = -c*sin_theta_d_theta + d*cos_theta_d_theta
        ddxs = -a * cos_theta_d_theta_sq - b * sin_theta_d_theta_sq
        ddys = -c * cos_theta_d_theta_sq - d * sin_theta_d_theta_sq

        sum_dx = np.sum(dxs)
        sum_dy = np.sum(dys)
        sum_ddx = np.sum(ddxs)
        sum_ddy = np.sum(ddys)
        K = ((sum_ddy*sum_dx) - (sum_dy*sum_ddx))/((sum_dx**2 +sum_dy**2)**(3/2))
        all_K.append(K)

    return all_K

def FindCurvatureMaxima(curvature_values,cumulative_distance,bisector_vectors,contour_points):
    k_maxima_values = []
    k_maxima_bisectors = []
    k_maxima_x = []
    k_maxima_y = []
    non_maxima_k = []
    k_maxima_cumulative_distance=[]
    if len(curvature_values)<50:
        k_cutoff = 70
    elif len(curvature_values)<500:
        k_cutoff = 90
    else:
        k_cutoff = 90
    curvature_absolute_values = [abs(value) for value in curvature_values]
    abs_percentile = np.percentile(curvature_absolute_values,k_cutoff)
    percentile = np.percentile(curvature_values,k_cutoff)

    if max(curvature_values)<0:
        #we're interested in postive curvature(k) values only
        pass
    else:
        for i in range(len(curvature_values)):
            if i<len(curvature_values)-1:
                thisK = curvature_values[i]
                nextK = curvature_values[i+1]
                prevK = curvature_values[i-1]
                prev2K = curvature_absolute_values[i - 2]
            else:
                thisK = curvature_values[i]
                nextK = curvature_values[0]
                prevK = curvature_values[i - 1]
                prev2K = curvature_absolute_values[i - 2]

            if thisK > nextK:
                if thisK > prevK:
                    if abs(thisK) >= abs_percentile and thisK > percentile:
                        k_maxima_values.append(thisK)  #get the k maxima
                        k_maxima_bisectors.append(bisector_vectors[i])
                        k_maxima_x.append(contour_points[i][0])  # get the x value associated with the k
                        k_maxima_y.append(contour_points[i][1])  # get the y value associated with the k
                    else:
                        # all k values that aren't maxima
                        non_maxima_k.append(thisK)
                elif thisK==prevK and prevK>prev2K:
                    if abs(thisK) >= abs_percentile and thisK > percentile:
                        k_maxima_values.append(thisK)  #get the k maxima
                        k_maxima_bisectors.append(bisector_vectors[i])
                        k_maxima_x.append(contour_points[i][0])  # get the x value associated with the k
                        k_maxima_y.append(contour_points[i][1])  # get the y value associated with the k
                    else:
                        # all k values that aren't maxima
                        non_maxima_k.append(thisK)

    return k_maxima_values, k_maxima_x, k_maxima_y, non_maxima_k,k_maxima_bisectors

def IdentifyContactPoints(k_maxima_values, k_maxima_x, k_maxima_y,maxima_bisectors, non_maxima_k):
    max_k = max(non_maxima_k,default = 0)
    maxima_to_remove = []
    for k in k_maxima_values:
        if k < 1.5*max_k:
            iterator = k_maxima_values.index(k)
            maxima_to_remove.append(iterator)

    contact_point_k_values = []
    contact_point_x = []
    contact_point_y = []
    contact_point_bisector = []

    for i in range(len(k_maxima_y)):
        if i not in maxima_to_remove:
            contact_point_k_values.append(k_maxima_values[i])
            contact_point_x.append(k_maxima_x[i])
            contact_point_y.append(k_maxima_y[i])
            contact_point_bisector.append(maxima_bisectors[i])

    return contact_point_k_values, contact_point_x, contact_point_y,contact_point_bisector

def FindNestedContours(hierarchy):
    #groups contours together according to their nested structures.
    #returns a list of groupings
    #this groupings list allow the contact points of nested contours to be connected

    parents = set()
    singles = set()
    groups = []

    if hierarchy.ndim == 1:
        if hierarchy[2] == -1 and hierarchy[3] == -1:
            singles.add(0)
        elif hierarchy[2] != -1 and hierarchy[3] == -1:
            parents.add(0)
    else:
        for h in range(len(hierarchy)):  # i.e h is the index of the contours
            if hierarchy[h][2] == -1 and hierarchy[h][3] == -1:
                singles.add(h)
            elif hierarchy[h][2] != -1 and hierarchy[h][3] == -1:
                parents.add(h)

    #record single contours as a group on their own
    for s in singles:
        groups.append([s])

    # group all the nested contours together in a family of contours
    for p in parents:
        family = [p]
        count = 0
        for entry in hierarchy:
            if entry[3] == p:
                family.append(count)
            count += 1
        groups.append(family)

    return groups

def Find_Inter_Point_Distance(point1,point2,contour):
    index_point1 = None
    index_point2 = None
    for i,j in enumerate(contour.reconstructed_points):
        if j[0] == point1[0] and j[1]==point1[1]:
            index_point1 = i
        if j[0]==point2[0] and j[1] == point2[1]:
            index_point2 = i
    if index_point1 < index_point2:
        partial_contour = contour.reconstructed_points[index_point1:index_point2+1]
    else:
        partial_contour = contour.reconstructed_points[index_point2:index_point1 + 1]
    full_contour_distance =  cv2.arcLength(np.float32(contour.reconstructed_points),True)
    partial_contour_distance = cv2.arcLength(np.float32(partial_contour),False)
    remainder_distance = full_contour_distance - partial_contour_distance
    if partial_contour_distance <= remainder_distance:
        return partial_contour_distance
    else:
        return remainder_distance

def calculate_distance_between_points(point1,point2):
    diff_x = (point1[0] - point2[0]) ** 2
    diff_y = (point1[1] - point2[1]) ** 2
    distance = math.sqrt(diff_x + diff_y)
    return distance

def slice_contour_by_point_pair(point1, point2, contour):
    contour = ensure_contour_is_open(contour)

    start_contour2 = False
    end_contour2 = False
    contour1=[]
    contour2=[]
    for point in contour:
        comparison1 = point == point1
        comparison2 = point == point2
        if comparison1.all() or comparison2.all():
            if start_contour2 == False and end_contour2 == False:
                start_contour2 = True
            elif start_contour2 == True and end_contour2 == False:
                end_contour2 = True

            contour2.append(point) #both contours will have these points, as this is the boundary that separates them
            contour1.append(point)
            continue

        if start_contour2 == True and end_contour2==False:
            contour2.append(point)
        else:
            contour1.append(point)

    return contour1, contour2, start_contour2, end_contour2

def plot(imgTL,points = [],contour1 = [], contour2= []):

    plt.imshow(imgTL, cmap='Greys_r')
    matplotlib.use('TkAgg')
    dpi = 100

    #canvas = FigureCanvasAgg(fig)
    plt.margins(0, 0)
    plt.axis('off')
    plt.imshow(imgTL, cmap='Greys_r')
    if contour1!=[]:
        x1, y1 = zip(*contour1)
        plt.scatter(x1, y1,s=8)
        for i in range(len(contour1)):
            plt.text(contour1[i][0],contour1[i][1]+3,s=i, size=5,c='red')
    if contour2!=[]:
        x2,y2 = zip(*contour2)
        plt.scatter(x2,y2,s=8)
        for i in range(len(contour1)):
            plt.text(contour1[i][0],contour1[i][1]+3,3,s=1, size=5,c='red')
    if points!=[]:
        for point in points:
            plt.scatter(point[0], point[1],s=5)
    plt.show()

def filter_pairs_with_length_to_volume_ratio(node1, node2,contour_group,threshold=0.8):
    contour1, contour2, contour2_initialised, contour2_finalised = slice_contour_by_point_pair(np.asarray(node1), np.asarray(node2), contour_group[0].reconstructed_points)
    # This condition happens if two nodes are adjacent to one another on the same contour
    if contour1 ==[] or contour2 == []:
        # False - happens if both nodes exist on the parent contour
        # True -  happens if one or both nodes exist on child contours. By default, accept node pairs that are child-child or parent-child. No filtering is applied to these.
        return not (contour2_initialised and contour2_finalised)

    # if both nodes are on the parent contour, apply filter to decide whether the points are kept
    if contour2_initialised and contour2_finalised:
        #when both nodes exist on the parent contour, and the subcontours (contour1 and contour2 produced by splitting the parent contour with the node pair) both contain points
        try:
            contour1_area = math.sqrt(cv2.contourArea(np.array(contour1).astype('int')))
            contour2_area = math.sqrt(cv2.contourArea(np.array(contour2).astype('int')))
            distance = calculate_distance_between_points(node1, node2)
            length_volume_ratio = distance/(min(contour1_area, contour2_area))
            if length_volume_ratio>threshold:
                return False
        except:
            return False

    return True

def create_curvature_distance_plot(contour):
    #import seaborn as sns
    matplotlib.use('TkAgg')
    fig = plt.figure(figsize=(20, 20), dpi=300)
    ax = fig.add_subplot(1,1,1)
    all_kvalues = contour.curvature_values
    all_distance = contour.cumulative_distance
    max_k = contour.max_curvature_values
    max_distance = contour.max_curvature_distance

    #sns.lineplot(all_distance[1 :], all_kvalues[1 :])
    #sns.scatterplot(max_distance, max_k)
    plt.plot(all_distance[1 :], all_kvalues[1 :], c='black', linewidth = 1, zorder=1)
    plt.scatter(max_distance, max_k, c='red',edgecolors='black', s=50, zorder=2)
    ax.set_ylim(ymin=-0.2)
    ax.set_xlim(xmin=0)
    ax.set_ylabel('Curvature (K)')
    ax.set_xlabel('Distance (radians)')
    plt.grid()
    ax.set_axisbelow(True)
    plt.show()







