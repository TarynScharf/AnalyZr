'''import cv2  # this is going to read my image and give me contours
import numpy as np
from pyefd import elliptic_fourier_descriptors
from pyefd import reconstruct_contour as rc
import pyefd
import matplotlib
import matplotlib.pyplot as plt  # This will let me visualise my image
import seaborn as sns
from sklearn.decomposition import PCA as sklearnPCA
from scipy.stats import skew, kurtosis
import math

def calcEFD(input_contour, order):
    dxy = np.diff(input_contour,axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
    t = np.concatenate([([0.]), np.cumsum(dt)])  # add a 0 onto the cumulative displacement, to represent starting point with no displacement
    T = t[-1]  # total  displacement is the last cumulative value in t

    phi = (2 * np.pi * t) / T
    orders = np.arange(1, order + 1)
    consts = T / (2 * orders * orders * np.pi * np.pi)
    phi = phi * orders.reshape((order, -1))
    d_cos_phi = np.cos(phi[:, 1:]) - np.cos(phi[:,:-1])
    d_sin_phi = np.sin(phi[:, 1:]) - np.sin(phi[:,:-1])
    cos_phi = (dxy[:, 0] / dt) * d_cos_phi
    a = consts * np.sum(cos_phi, axis=1)
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
    dxy = np.diff(con,axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
    t = np.concatenate([([0.]), np.cumsum(dt)])  # add a 0 onto the cumulative displacement, I assume to represent starting point with no displacement
    T = t[-1]  # total  displacement is the last cumulative value in t

    pi = np.pi  # pi = 180 degrees
    T_radians = pi * 2
    r = (np.pi * 2) / T  # radian equivalent of one unit of contour length
    t_radians = r * t
    all_K = []

    for cumulative_displacement in t:
        dx = []
        dy = []
        ddx = []
        ddy = []
        n = 0

        for harmonic in coef:
            n += 1
            a = harmonic[0]
            b = harmonic[1]
            c = harmonic[2]
            d = harmonic[3]
            nt = n * (cumulative_displacement * r)
            theta = (2 * pi * nt) / T_radians
            d_theta = (2 * pi * n) / T_radians

            dx_per_harmonic = -a * np.sin(theta) * d_theta + b * np.cos(theta) * d_theta
            dy_per_harmonic = -c * np.sin(theta) * d_theta + d * np.cos(theta) * d_theta
            ddx_per_harmonic = -a * np.cos(theta) * (d_theta ** 2) - b * np.sin(theta) * (d_theta ** 2)
            ddy_per_harmonic = -c * np.cos(theta) * (d_theta ** 2) - d * np.sin(theta) * (d_theta ** 2)

            dx.append(dx_per_harmonic)
            dy.append(dy_per_harmonic)
            ddx.append(ddx_per_harmonic)
            ddy.append(ddy_per_harmonic)

        sum_dx = np.sum(dx)
        sum_dy = np.sum(dy)
        sum_ddx = np.sum(ddx)
        sum_ddy = np.sum(ddy)

        K = ((sum_ddy * sum_dx) - (sum_dy * sum_ddx)) / ((sum_dx ** 2 + sum_dy ** 2) ** (3 / 2))
        all_K.append(K)

    p50 = np.percentile(all_K, 50)
    offset = []
    for kVal in all_K:
        diff = abs(kVal - p50)
        offset.append(diff)

    return all_K, t_radians, offset


def createCoordList(nodesXCoords, nodesYCoords):  # Create a list of x,y coordinates of each  node on the boundary
    # takes a list of x coordinates, and a list of y coordinates 1 x M
    # returns a list of coordinates pairs, M x 2
    coordList = []
    for a in zip(nodesXCoords, nodesYCoords):
        coordList.append(list(a))
    return coordList


def InsidePolygon(coord1, coord2, polygon):
    # find which polylines cut through the polygon

    x1 = coord1[0]
    y1 = coord1[1]
    x2 = coord2[0]
    y2 = coord2[1]

    xDist = abs(x1 - x2)
    xInc = xDist / 100
    yDist = abs(y1 - y2)
    yInc = yDist / 100

    if x1 < x2:
        xpoint = x1 + xInc
        if y1 < y2:
            ypoint = y1 + yInc
        else:
            ypoint = y1 - yInc
    else:
        xpoint = x2 + xInc
        if y2 < y1:
            ypoint = y2 + yInc
        else:
            ypoint = y2 - yInc

    points = []

    for i in range(98):  # let's calculate a few points along the straight-line path between the two nodes, and check that they all lie within the polygon.
        points.append([xpoint, ypoint])

        if x1 < x2:
            xpoint = xpoint + xInc
            if y1 < y2:
                ypoint = ypoint + yInc
            else:
                ypoint = ypoint - yInc
        else:
            xpoint = xpoint + xInc
            if y2 < y1:
                ypoint = ypoint + yInc
            else:
                ypoint = ypoint - yInc

    # now check if all the points in the array are inside the polygon.
    # I intensionally did not include the points on the edges.
    # boundary = matplotlib.path.Path(_reconstructionList[0], closed = True) #let's use the outer most boundary in all  cases. This was originally designed for a single boundary. This might have to be changed for nested boundaries
    boundary = matplotlib.path.Path(polygon, closed=True)
    insidePoly = boundary.contains_points(points, radius=0.1)
    allPoints = False
    somePoints = False
    if all(item == True for item in insidePoly):
        allPoints = True
    if any(item == True for item in insidePoly):
        somePoints = True
    return allPoints, somePoints


def determineQuadrant(point, contour):
    x1 = point[0]
    y1 = point[1]

    # get the vector of the point:
    iterator = contour.index(point)

    L = iterator - 2
    # R = iterator + 2

    # deal with cases where the points are on the ends of the contours, Contours are closed.
    if L < 0:
        L = len(contour) - L
    if L > len(contour):
        L = L - len(contour)

    # if R < 0:
    #    R = len(contour)-R
    # if R> len(contour):
    #    R =R-len(contour)

    pL = contour[L]
    # pR = contour[R]
    # startX = pL[0] + (pR[0]-pL[0])/2
    # startY = pL[1] + (pR[1]-pL[1])/2
    startX = pL[0]
    startY = pL[1]
    deltaX = x1 - startX
    deltaY = y1 - startY

    # determine quadrant
    quadrant = 0
    if deltaX >= 0:
        if deltaY >= 0:
            quadrant = 1  # 0-90
        else:
            quadrant = 2  # 270-360
    else:
        if deltaY >= 0:
            quadrant = -2  # 90-180
        else:
            quadrant = -1  # 180-270
    return quadrant


def linkNodes(contourList, xNodes, yNodes):
    # firstly, get rid of contours without nodes
    updatedContourList = []
    for index1 in contourList:
        if xNodes[index1] and yNodes[index1] != [-99999]:
            updatedContourList.append(index1)
    # Now find the closest nodes.
    # Prioritise internal contours, and connect them to other contours
    usedNodes = []
    coordPairs = []
    distList = []
    nearestList = []

    if len(updatedContourList) > 1:
        for index2 in updatedContourList[1:]:  # skip the first contour, which is the parent
            theseNodes = list(zip(xNodes[index2], yNodes[index2]))
            thoseNodes = []
            for i in range(len(updatedContourList)):
                if updatedContourList[i] != index2:  # skip theseNodes and focus on thoseNodes
                    nodes = list(zip(xNodes[updatedContourList[i]], yNodes[updatedContourList[i]]))
                    for n in nodes:
                        thoseNodes.append(n)  # these are all the nodes from all the other contours
            # Now compare the distance between every node in the internal contour under consideration,
            # and every other contour node. Find the closest.
            if theseNodes != [] and thoseNodes != []:
                for node1 in theseNodes:
                    thisX = node1[0]
                    thisY = node1[1]
                    for node2 in thoseNodes:
                        # print('node2: ', node2)
                        thatX = node2[0]
                        thatY = node2[1]
                        diff_x = (thisX - thatX) ** 2
                        diff_y = (thisY - thatY) ** 2
                        distance = math.sqrt(diff_x + diff_y)
                        distList.append([node1, node2, distance])
        # when that's done, get the pairs in the parent contour, between the parent contour
        theseNodes = list(zip(xNodes[updatedContourList[0]], yNodes[updatedContourList[0]]))
        for thisNode in theseNodes:
            if not thisNode in usedNodes:
                partnerCoord = []
                thisX = thisNode[0]
                thisY = thisNode[1]
                for thatNode in theseNodes:
                    if thatNode != thisNode and not thatNode in usedNodes:
                        thatX = thatNode[0]
                        thatY = thatNode[1]
                        diff_x = (thisX - thatX) ** 2
                        diff_y = (thisY - thatY) ** 2
                        distance = math.sqrt(diff_x + diff_y)
                        distList.append([thisNode, thatNode, distance])
        distList = np.array(distList)
        sortDistList = sorted(distList, key=lambda x: x[2], reverse=False)

        for entry in sortDistList:
            pair1 = entry[0]
            pair2 = entry[1]

            if not pair1 in usedNodes and not pair2 in usedNodes:
                if [pair1, pair2] not in nearestList:
                    flag = 0
                    allInsideParent, someInsideParent = InsidePolygon(pair1, pair2, simplifyList[
                        updatedContourList[0]])  # np.squeeze(contours[updatedContourList[0]]))
                    if allInsideParent == False:
                        flag = 1

                    for i in range(1, len(updatedContourList)):
                        allInsideChild, someInsideChild = InsidePolygon(pair1, pair2, simplifyList[
                            updatedContourList[i]])  # np.squeeze(contours[updatedContourList[i]]))

                        if allInsideChild == True or someInsideChild == True:
                            flag = 1

                    if flag == 0:

                        nearestList.append([pair1, pair2])
                        usedNodes.append(pair1)
                        usedNodes.append(pair2)


    if len(updatedContourList) == 1:
        usedNodes = []
        coordPairs = []
        distList = []
        nearestList = []
        theseNodes = list(zip(xNodes[updatedContourList[0]], yNodes[updatedContourList[0]]))
        for thisNode in theseNodes:
            if not thisNode in usedNodes:
                partnerCoord = []
                thisX = thisNode[0]
                thisY = thisNode[1]
                for thatNode in theseNodes:
                    if thatNode != thisNode and not thatNode in usedNodes:
                        thatX = thatNode[0]
                        thatY = thatNode[1]
                        diff_x = (thisX - thatX) ** 2
                        diff_y = (thisY - thatY) ** 2
                        distance = math.sqrt(diff_x + diff_y)
                        distList.append([thisNode, thatNode, distance])
        distList = np.array(distList)
        sortDistList = sorted(distList, key=lambda x: x[2], reverse=False)

        for entry in sortDistList:
            pair1 = entry[0]
            pair2 = entry[1]
            if not pair1 in usedNodes and not pair2 in usedNodes:
                if [pair1, pair2] not in nearestList:
                    allInsideParent, someInsideParent = InsidePolygon(pair1, pair2, simplifyList[
                        updatedContourList[0]])  # np.squeeze(contours[updatedContourList[0]]))
                    if allInsideParent == False:
                        pass
                    else:
                        nearestList.append([pair1, pair2])
                        usedNodes.append(pair1)
                        usedNodes.append(pair2)
    return nearestList


def RemoveDuplicates(nodePairs):
    # get rid of duplicate polylines:
    thisX = None
    thisY = None
    indexList = []
    for pair in nodePairs:
        duplicate = [pair[1], pair[0]]
        if duplicate in nodePairs:
            nodePairs.remove(duplicate)
    return nodePairs


def TestOuterNodes(nodePairs, coordinateList, allBoundaries):
    # this tests whether any nodes on the outer boundary, that are connected to each other, are also connected to nodes on the inner boundary.
    # This removes the unwanted links on the outer boundary
    # First make a single list of all the nodes index values
    nodeList = []
    for pair in nodePairs:
        nodeList.append(pair[0])
        nodeList.append(pair[1])

    # Check if there are duplicated values
    if len(nodeList) == len(set(nodeList)):
        return nodePairs  # i.e. no node is duplicated across the node pairs
    else:
        dupList = set()
        for node in nodeList:
            nodeCount = nodeList.count(node)  # find the nodes that occur more than once
            if nodeCount > 1:
                dupList.add(node)  # Record the duplicated nodes

        elemRemove = []
        for dup in dupList:
            for pair in nodePairs:
                if dup in pair:  # find any node pair that contains the duplicate node
                    coord1 = coordinateList[pair[0]]
                    coord2 = coordinateList[pair[1]]

                    if coord1 in allBoundaries[0] and coord2 in allBoundaries[
                        0]:  # check if both nodes in the pair lie on the parent boundary
                        if pair not in elemRemove:
                            elemRemove.append(pair)  # if so, record this node pair for removal
        for elem in elemRemove:
            nodePairs.remove(
                elem)  # remove node pairs from the parent boundary, if the node is already in use in another node pair

        return nodePairs


def findNearestNode(boundaryList, _reconstructionList, nested):
    coordList = []
    for b in boundaryList:
        for node in b:
            coordList.append(node)  # if it consists of nested contours, append them to make one list of nodes

    for i in range(len(coordList)):  # for each node in my list of nodes....
        thisNode = i  # save the index of THIS node
        partnerNode = None
        shortestDistance = 1000000000000000  # initiate to a very large number
        for j in range(len(coordList)):  # compare it to every other nodes in the list...
            if j != thisNode:  # ...but skip itself.
                delta_x = coordList[i][0] - coordList[j][0]  # diff in x between THIS node and other nodes
                delta_y = coordList[i][1] - coordList[j][1]  # diff in y between THIS node and other nodes
                distance = math.sqrt(
                    (delta_x ** 2) + (delta_y ** 2))  # total straight line distance between THIS node and other nodes
                if distance < shortestDistance:
                    if nested:  # if this is a case of nested contours....
                        thisCoord = coordList[i]
                        partnerCoord = coordList[j]

                        for z in range(0, len(_reconstructionList)):  # for all boundaries
                            if z == 0:  # consider the parent (external boundary)
                                if (thisCoord in _reconstructionList[z]) and (partnerCoord in _reconstructionList[z]):  # if both nodes lie on the parent boundary
                                    allInside, someInside = InsidePolygon(thisCoord, partnerCoord, _reconstructionList[z])  # pass both coordinates and the parent boundary for testing
                                    if allInside:  # if both nodes are on the external boundary, the entire connecting line must lie within the external boundary
                                        shortestDistance = distance  # save the shortest distance eachtime. In the end, the last retained value is the shortest distance
                                        partnerNode = j  # save the index of the nearest node each time. In the end, the last retained value is the nearest node to this node.
                                    else:
                                        pass  # if the connecting line travels through a hole, or outside of the external boundary, do not use the node pair

                            else:  # consider the internal boundaries
                                if (thisCoord in _reconstructionList[z]) and (partnerCoord in _reconstructionList[z]):
                                    pass  # if both nodes are from the same internal boundary, don't use the node pair
                                elif (thisCoord in _reconstructionList[z]) or (partnerCoord in _reconstructionList[z]):  # if either node is in an internal boundary, but both are not in the same internal boundary
                                    allInside, someInside = InsidePolygon(thisCoord, partnerCoord, _reconstructionList[z])  # True/False: all or any part of the connecting line lies inside the internal boundary
                                    if allInside or someInside:  # for nested boundaries, you don't want any part of the connecting line to lie within an internal boundary (i.e. a hole)
                                        pass  # if the connecting line travels through a hole (i.e inside an internal boundary), do not use the node pair
                                    else:
                                        shortestDistance = distance  # save the shortest distance eachtime. In the end, the last retained value is the shortest distance
                                        partnerNode = j  # save the index of the nearest node each time. In the end, the last retained value is the nearest node to this node.
                                elif (thisCoord not in _reconstructionList[z]) and (
                                        partnerCoord not in _reconstructionList[z]):
                                    pass
                                else:
                                    pass
                    else:
                        thisCoord = coordList[i]
                        partnerCoord = coordList[j]
                        allInside, someInside = InsidePolygon(thisCoord, partnerCoord, _reconstructionList[0])  # if it's not nested, there's only one boundary to consider
                        if allInside:  # for a stand alone boundary, you  want the whole connecting line to lie within the single boundary
                            shortestDistance = distance  # save the shortest distance eachtime. In the end, the last retained value is the shortest distance
                            partnerNode = j  # save the index of the nearest node each time. In the end, the last retained value is the nearest node to this node.
                        else:
                            pass  # if the connecting line travels through a hold (i.e inside an internal boundary), do not use the node pair
        if (thisNode != None) and (partnerNode != None):
            nodePairs.append([thisNode, partnerNode])
    noDuplicates = RemoveDuplicates(nodePairs)
    testOuter = TestOuterNodes(nodePairs, coordList, _reconstructionList)

    # Now remove any pairs that are too close together as measured along the length of the reconstruction polyline
    # This is useful if you don't want to cut off small protrusions.
    # During initial phases of binarisation, cutting off protrusions this way may be a helpful alternative to erosion/dilation sequences
    for reconBoundary in _reconstructionList:
        dxy = np.diff(reconBoundary,
                      axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
        dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
        t = np.concatenate([([0.]), np.cumsum(
            dt)])  # add a 0 onto the cumulative displacement, I assume to represent starting point with no displacement
        T = t[-1]  # total  displacement is the last cumulative value in t

        distFiltPairs = []
        for pair in testOuter:
            coords1 = coordList[pair[0]]  # coordinates of first point in the pair
            coords2 = coordList[pair[1]]  # coordinates of second points in the pair

            if coords1 in reconBoundary and coords2 in reconBoundary:
                coords_index = []
                coords_index.append(np.where(reconBoundary == coords1)[0][1])
                coords_index.append(np.where(reconBoundary == coords2)[0][1])
                coords_index.sort()  # Make sure to consider the nodes in the order as they occur as measured from the start of the polyline.

                dist1 = t[coords_index[0]]  # cumulative distance along polygon, of first point
                dist2 = t[coords_index[1]]  # cumulative distance along polygon, of second point
                delta_dist = dist2 - dist1

                if delta_dist <= T * 0.5:  # I'm taking a guess at the likely distance
                    pass
                else:
                    distFiltPairs.append(pair)
            else:
                pass

        if distFiltPairs == []:
            return testOuter, coordList
        else:
            return distFiltPairs, coordList


def simplify(poly, inside):
    if inside == True:
        factor = 1
    else:
        factor = 0.25

    count = int(len(poly) * factor)
    dxy = np.diff(poly,axis=0)  # get the incremental difference between each x and y for each point in the contour. If the contour isn't simplified, this looks to be a pixel-by-pixel change in X and Y.
    dt = np.sqrt((dxy ** 2).sum(axis=1))  # at each increment, calculate displacement, like pythagoras theorem
    t = np.concatenate([([0.]), np.cumsum(dt)])  # add a 0 onto the cumulative displacement, I assume to represent starting point with no displacement
    T = t[-1]  # total  displacement is the last cumulative value in t
    spacing = T / count
    newPoints = []

    for i in range(0, count):
        pDist = i * spacing  # point distance along polyline
        for j in range(len(poly)):
            prevDist = t[j - 1]
            dist = t[j]
            displacement = dist - prevDist
            x = None
            y = None

            if dist == pDist:
                newPoints.append(poly[j])
            elif prevDist < pDist and dist > pDist:
                diff = pDist - prevDist
                diffRatio = displacement / diff
                x = poly[j - 1][0] + (poly[j][0] - poly[j - 1][0]) / diffRatio
                y = poly[j - 1][1] + (poly[j][1] - poly[j - 1][1]) / diffRatio
                newPoints.append([x, y])

    return newPoints'''