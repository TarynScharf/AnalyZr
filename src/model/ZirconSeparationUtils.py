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
from src.model.json_data import JsonData


def getScale(json_file_path, tag):
    sampleid = JsonData.get_sample_id_from_file_path(json_file_path)
    json_folder_path = FileUtils.get_folder(json_file_path)

    spot_length_list = []
    scale_length_list=[]
    for  path, folder, files in os.walk(json_folder_path):
        for name in files:
            sample = name.split('_')[0]
            ext =os.path.splitext(name)[1]
            if sample == sampleid and ext == '.json':
                with open(os.path.join(json_folder_path, name), errors='ignore') as jFile:
                    data = json.load(jFile)
                for region in data['regions']:
                    if region['type'] == 'RECTANGLE' and region['tags'][0]==tag:
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
    #cv2.imwrite('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/test/labelim.png', labelim)
    areaList = []
    for x in range (0,len(props)):
        areaList.append(props[x].area)

    areaList.sort(reverse=True)
    if len(areaList)>0:
        maxArea = areaList[0]
        min_size = maxArea/factor
        #print('min_size', min_size)
        remSmall = remove_small_objects(labelim,min_size, in_place=False)
        #cv2.imwrite('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/test/remSmall.png', remSmall)
    
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

def get_efd_parameters_for_simplified_contour(contour, has_parent, filter_fn, ORDER_FACTOR =0.2):
    #Takes an object of type CompositeContour. It uses the ComplexContour.original_points.
    #return: updated CompositeContour object
    #if has_parent ==True:
    ##    factor = 1
    #else:
    #    factor = ORDER_FACTOR

    number_of_points = len(contour)

    if len(contour)<50:
        ORDER_FACTOR= 1
    elif len(contour) < 500:
        ORDER_FACTOR=0.2
    else:
        ORDER_FACTOR=0.2

    order = int(number_of_points*ORDER_FACTOR)
    #reconstructed_points = simplify(contour, has_parent) ### for testing must remove
    if order ==0:
        return None
    if filter_fn is not None and not filter_fn(contour):
        return None

    coefficients = calcEFD(contour,order)
    locus = calculate_locus(contour)
    reconstructed_points = pyefd.reconstruct_contour(coefficients, locus, order + 1).astype('int')  # simplify (contour,has_parent)
    reconstructed_points_without_duplicates = remove_duplicate_points(reconstructed_points)
    if len(reconstructed_points_without_duplicates)<2:
        return None

    return coefficients,locus, reconstructed_points_without_duplicates


def remove_duplicate_points(reconstructed_points):
    nonduplicate_points = []
    prev_x = None
    prev_y = None
    for x,y in reconstructed_points:
        if x != prev_x or y != prev_y:
            nonduplicate_points.append((x,y))
        prev_x = x
        prev_y = y

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
 
def linkNodes(contour_group):

    usedNodes=[]
    distList = []
    nearestList=[]
    
    if len(contour_group) > 1: #if it's a family of nested contours
        for contour in contour_group[1:]: #skip the first contour, which is the parent
            theseNodes = list(contour.max_curvature_coordinates)
            thoseNodes = []
            for other_contour in contour_group:
                if other_contour != contour: #skip theseNodes and focus on thoseNodes
                    nodes = list(other_contour.max_curvature_coordinates)
                    for n in nodes:
                        thoseNodes.append(n) #these are all the nodes from all the other contours

            #Now compare the distance between every node in the internal contour under consideration, 
            #and every other contour node. Find the closest.
            if theseNodes ==[] and thoseNodes ==[]:
                continue #if there are no nodes, consider the next contour in the group. This should be impossible though, because it's already been screened for above
            for node1 in theseNodes:
                thisX = node1[0]
                thisY = node1[1]
                for node2 in thoseNodes:
                    thatX = node2[0]
                    thatY = node2[1]
                    diff_x = (thisX-thatX)**2
                    diff_y = (thisY-thatY)**2
                    distance = math.sqrt(diff_x + diff_y)
                    distList.append([node1, node2, distance])

        #when that's done, get the pairs in the parent contour, between the parent contour
        parent_nodes = []
        #parent_contour_length = cv2.arcLength(np.float32(contour_group[0].reconstructed_points), True)

        theseNodes = list(contour_group[0].max_curvature_coordinates)
        for thisNode in theseNodes:
            if not thisNode in usedNodes:
                thisX = thisNode[0]
                thisY = thisNode[1]
                for thatNode in theseNodes:
                    if thatNode != thisNode and not thatNode in usedNodes:
                        thatX = thatNode[0]
                        thatY = thatNode[1]
                        diff_x = (thisX-thatX)**2
                        diff_y = (thisY-thatY)**2
                        distance = math.sqrt(diff_x + diff_y)
                        pair_distance = Find_Inter_Point_Distance(thisNode, thatNode, contour_group[0])
                        #pair_distance_radiants = (2 * np.pi) * (pair_distance / parent_contour_length)
                        #if pair_distance_radiants < critical_distance:
                        #    continue
                        distList.append([thisNode, thatNode, distance])

        distList = np.array(distList)
        sortDistList = sorted(distList,key = lambda x:x[2],reverse = False)

        for entry in sortDistList:
            pair1= entry[0]
            pair2 = entry[1]
            if not pair1 in usedNodes and not pair2 in usedNodes:
                if [pair1, pair2] not in nearestList:
                    flag = 0
                    allInsideParent, someInsideParent = InsidePolygon(pair1, pair2, contour_group[0].reconstructed_points)
                    if allInsideParent == False: #firstly, is the polyline inside the parent contour?
                        flag = 1
                    for i in range(1,len(contour_group)):
                        allInsideChild,someInsideChild = InsidePolygon(pair1, pair2, contour_group[i].reconstructed_points)
                        if allInsideChild == True or someInsideChild == True: #secondly, does it go inside an internal hole?
                            flag = 1

                    if flag == 0: #if it is a potential  node  pair, check  that it doesn't cut across any pre-existing node pairs
                        test_string = LineString([pair1,pair2])
                        for pair in nearestList:
                            pair_string = LineString(pair)
                            crosses = pair_string.crosses(test_string)
                            if crosses == True:
                                flag = 1

                    if flag == 0: #if everything checks out ok, save the node pair
                        nearestList.append([pair1,pair2])
                        usedNodes.append(pair1)
                        usedNodes.append(pair2)

        nearestList = filter_pairs_with_length_to_volume_ratio(nearestList, contour_group)

    if len(contour_group) ==1: #if the group  only contains 1 contour

        #critical_distance = (2 * np.pi / len(contour_group[0].max_curvature_coordinates)) ** (2 / 3)  # From Metbatsion and Paliwal 2011
        #parent_contour_length = cv2.arcLength(np.float32(contour_group[0].reconstructed_points), True)

        usedNodes=[]
        distList = []
        nearestList=[]

        theseNodes = list(contour_group[0].max_curvature_coordinates)

        for thisNode in theseNodes:
            if not thisNode in usedNodes:
                thisX = thisNode[0]
                thisY = thisNode[1]
                for thatNode in theseNodes:
                    if thatNode != thisNode and not thatNode in usedNodes:
                        thatX = thatNode[0]
                        thatY = thatNode[1]
                        diff_x = (thisX-thatX)**2
                        diff_y = (thisY-thatY)**2
                        distance = math.sqrt(diff_x + diff_y)
                        distList.append([thisNode, thatNode, distance])

        distList = np.array(distList)
        sortDistList = sorted(distList,key = lambda x:x[2],reverse = False)
        for entry in sortDistList:
            pair1= entry[0]
            pair2 = entry[1]
            if not pair1 in usedNodes and not pair2 in usedNodes:
                if [pair1, pair2] not in nearestList:
                    flag = 0
                    allInsideParent, someInsideParent = InsidePolygon(pair1, pair2, contour_group[0].reconstructed_points) #np.squeeze(contours[contour_group[0]]))
                    if allInsideParent == False:
                        continue
                    else:
                        test_string = LineString([pair1, pair2])
                        for pair in nearestList:
                            pair_string = LineString(pair)
                            crosses = pair_string.crosses(test_string)
                            if crosses == True:
                                flag = 1

                        pair_distance = Find_Inter_Point_Distance(pair1, pair2,contour_group[0])

                        if flag == 0:  # if everything checks out ok, save the node pair
                            nearestList.append([pair1, pair2])
                            usedNodes.append(pair1)
                            usedNodes.append(pair2)

        nearestList = filter_pairs_with_length_to_volume_ratio(nearestList,contour_group)

    return nearestList

def close_contour(contour):
    contour_copy = np.copy(contour)
    closed_contour = np.insert(contour_copy, len(contour_copy), contour_copy[0], 0)
    return closed_contour

def calculate_locus(contour):
    """Calculate the :math:`A_0` and :math:`C_0` coefficients of the elliptic Fourier series.

    :param numpy.ndarray contour: A contour array of size ``[M x 2]``.
    :return: The :math:`A_0` and :math:`C_0` coefficients.
    :rtype: tuple

    """
    contour = close_contour(contour)
    dxy = np.diff(contour, axis=0)
    dt = np.sqrt((dxy ** 2).sum(axis=1))
    t = np.concatenate([([0.]), np.cumsum(dt)])
    T = t[-1]

    xi = np.cumsum(dxy[:, 0]) - (dxy[:, 0] / dt) * t[1:]
    A0 = (1 / T) * np.sum(((dxy[:, 0] / (2 * dt)) * np.diff(t ** 2)) + xi * dt)
    delta = np.cumsum(dxy[:, 1]) - (dxy[:, 1] / dt) * t[1:]
    C0 = (1 / T) * np.sum(((dxy[:, 1] / (2 * dt)) * np.diff(t ** 2)) + delta * dt)

    # A0 and CO relate to the first point of the contour array as origin.
    # Adding those values to the coefficients to make them relate to true origin.
    return contour[0, 0] + A0, contour[0, 1] + C0

def calcEFD(contour, order):
    input_contour = close_contour(contour)
    dxy = np.diff(input_contour,axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
    t = np.cumsum(dt)
    T = t[-1]  # total  displacement is the last cumulative value in t

    phi = (2 * np.pi * t) / T
    orders = np.arange(1, order + 1)
    consts = T / (2 * orders * orders * np.pi * np.pi)
    phi = phi * orders.reshape((order, -1))
    d_cos_phi = np.cos(phi) - np.cos(np.roll(phi, 1,
                                             axis=1))  # why does first cos term consider all phi, including the leading zero, but second cos cuts off the leading zero?
    d_sin_phi = np.sin(phi) - np.sin(np.roll(phi, 1,
                                             axis=1))  # why does first sin term consider all phi, including the leading zero, but second sin cuts off the leading zero?

    a = consts * np.sum((dxy[:, 0] / dt) * d_cos_phi, axis=1)
    b = consts * np.sum((dxy[:, 0] / dt) * d_sin_phi, axis=1)
    c = consts * np.sum((dxy[:, 1] / dt) * d_cos_phi, axis=1)
    d = consts * np.sum((dxy[:, 1] / dt) * d_sin_phi, axis=1)

    coeffs = np.concatenate(  # coeffs is an array of orders (i.e. rows) x [a, b, c, d] i.e. columns
        [
            a.reshape((order, 1)),
            b.reshape((order, 1)),
            c.reshape((order, 1)),
            d.reshape((order, 1)),
        ],
        axis=1,
    )
    return coeffs

def calculateK(con, coef):
    input_contour = np.insert(con, len(con), con[0], 0)
    dxy = np.diff(input_contour, axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
    t = np.cumsum(dt)
    t = np.roll(t, shift=1)
    T = t[-1]  # total  displacement is the last cumulative value in t

    pi = np.pi #pi = 180 degrees
    T_radians = pi*2
    r = (np.pi*2)/T #radian equivalent of one unit of contour length
    t_radians = r*t
    all_K = []
    
    for cumulative_displacement in t:
        dx = []
        dy = []
        ddx = []
        ddy = []
        n = 0

        for harmonic in coef:
            #print('harmonic: ', harmonic)
            n +=1

            d_theta = (2 * pi * n) / T
            theta = (2 * pi * n * cumulative_displacement) / T
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            a = harmonic[0]
            b = harmonic[1]
            c = harmonic[2]
            d = harmonic[3] 

            dx_per_harmonic = -a*sin_theta*d_theta + b*cos_theta*d_theta
            dy_per_harmonic = -c*sin_theta*d_theta + d*cos_theta*d_theta
            ddx_per_harmonic = -a*cos_theta*(d_theta**2) - b*sin_theta*(d_theta**2)
            ddy_per_harmonic = -c*cos_theta*(d_theta**2) - d*sin_theta*(d_theta**2)
            
            dx.append(dx_per_harmonic)
            dy.append(dy_per_harmonic)
            ddx.append(ddx_per_harmonic)
            ddy.append(ddy_per_harmonic)
        
        sum_dx = np.sum(dx)
        sum_dy = np.sum(dy)
        sum_ddx = np.sum(ddx)
        sum_ddy = np.sum(ddy)
        
        K = ((sum_ddy*sum_dx) - (sum_dy*sum_ddx))/((sum_dx**2 +sum_dy**2)**(3/2))
        all_K.append(K)


    return all_K,  t_radians

def FindCurvatureMaxima(curvature_values,cumulative_distance,contour_points):
    #plot(contour1 = contour_points)
    k_maxima_values = []
    k_maxima_length_positions = []
    k_maxima_x = []
    k_maxima_y = []
    non_maxima_k = []
    k_cutoff = 80
    #test_plot_points=[]
    curvature_absolute_values = [abs(value) for value in curvature_values]
    abs_percentile = np.percentile(curvature_absolute_values,k_cutoff)
    percentile = np.percentile(curvature_values,k_cutoff)

    if max(curvature_values)<0: #we're interested in postive curvature(k) values only
        pass
    else:
        for i in range(len(curvature_values)):  #for each curvature value in the list
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
                    #point_test = [[contour_points[i][0],contour_points[i][1]]]
                    #plot(point_test)
                    if abs(thisK) >= abs_percentile and thisK > percentile:
                        k_maxima_length_positions.append(cumulative_distance[i]) #get the cumulative distance along the contour at which the k occurs
                        k_maxima_values.append(thisK)  #get the k maxima
                        k_maxima_x.append(contour_points[i][0])  # get the x value associated with the k
                        k_maxima_y.append(contour_points[i][1])  # get the y value associated with the k
                        #test_plot_points.append([contour_points[i][0],contour_points[i][1]])
                    else:
                        non_maxima_k.append(thisK)  # all k values that aren't maxima
                elif thisK==prevK and prevK>prev2K:
                    if abs(thisK) >= abs_percentile and thisK > percentile:
                        k_maxima_length_positions.append(cumulative_distance[i]) #get the cumulative distance along the contour at which the k occurs
                        k_maxima_values.append(thisK)  #get the k maxima
                        k_maxima_x.append(contour_points[i][0])  # get the x value associated with the k
                        k_maxima_y.append(contour_points[i][1])  # get the y value associated with the k
                        #test_plot_points.append([contour_points[i][0],contour_points[i][1]])
                    else:
                        non_maxima_k.append(thisK)  # all k values that aren't maxima

    #plot(test_plot_points)
    return k_maxima_length_positions, k_maxima_values, k_maxima_x, k_maxima_y, non_maxima_k

def IdentifyContactPoints(k_maxima_length_positions, k_maxima_values, k_maxima_x, k_maxima_y, non_maxima_k):
    #k = curvature

    max_k = max(non_maxima_k,default = 0)
    maxima_to_remove = []
    '''for k in k_maxima_values:
        if k < 1.5*max_k:
            iterator = k_maxima_values.index(k)
            maxima_to_remove.append(iterator)'''

    contact_point_k_values = []
    contact_point_length_positions = []
    contact_point_x = []
    contact_point_y = []

    for i in range(len(k_maxima_y)):
        if i in maxima_to_remove:
            pass
        else:
            contact_point_k_values.append(k_maxima_values[i])
            contact_point_length_positions.append(k_maxima_length_positions[i])
            contact_point_x.append(k_maxima_x[i])
            contact_point_y.append(k_maxima_y[i])

    return contact_point_k_values, contact_point_length_positions, contact_point_x, contact_point_y

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

def plot(points = [],contour1 = [], contour2= []):
    imgTL = cv2.imread("C:/Users/20023951/Documents/PhD/GSWA/test_masks/189937_spots_p1_RL_Zbx-wowp74.png")
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

def filter_pairs_with_length_to_volume_ratio(pairs,contour_group,threshold=0.8):

    sorted_distance_pairs_list = sorted(pairs, key=lambda x: calculate_distance_between_points(x[0],x[1]), reverse=False)
    filtered_pairs=[]
    for distance_pair in sorted_distance_pairs_list:
        contour1, contour2,contour2_initialised, contour2_finalised = slice_contour_by_point_pair(np.asarray(distance_pair[0]),np.asarray(distance_pair[1]), contour_group[0].reconstructed_points)

        if contour1 ==[] or contour2 == []: #this happens if two nodes are adjacent to one another on the same contour
            if contour2_initialised == True and contour2_finalised == True: #this happens if both nodes exist on the parent contour
                continue
            else: # this happens if one or both nodes exist on child contours
                filtered_pairs.append([distance_pair[0], distance_pair[1]]) #by default, accept node pairs that are child-child or parent-child. No filtering is applied to these.
        else:
            if contour2_initialised == True and contour2_finalised == True: #if both nodes are on the parent contour, apply filter to decide whether the points are kept
                #when both nodes exist on the parent contour, and the subcontours (contour1 and contour2 produced by splitting the parent contour with the node pair) both contain points
                try:
                    contour1_area = math.sqrt(cv2.contourArea(np.array(contour1)))
                    contour2_area = math.sqrt(cv2.contourArea(np.array(contour2)))
                    distance = calculate_distance_between_points(distance_pair[0], distance_pair[1])
                    length_volume_ratio = distance/(min(contour1_area, contour2_area))
                    if length_volume_ratio>threshold:
                        continue
                except:
                    continue

            filtered_pairs.append([distance_pair[0],distance_pair[1]])

    return filtered_pairs

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







