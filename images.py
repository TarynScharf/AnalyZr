import cv2
from matplotlib import pyplot as plt
import skimage
from skimage.segmentation import clear_border
from skimage.measure import label
from skimage.morphology import remove_small_objects, binary_erosion, binary_dilation,binary_opening
from skimage.measure import regionprops
from skimage.morphology import disk #https://scikit-image.org/docs/stable/auto_examples/numpy_operations/plot_structuring_elements.html#sphx-glr-auto-examples-numpy-operations-plot-structuring-elements-py
import os
import cv2
import numpy as np
from matplotlib import pyplot as plt
import copy
import imageio

from scipy import ndimage
from scipy.stats import skew, kurtosis
from shapely.geometry import Polygon
from images import *


def smooth(img):
    bilateralFilter = cv2.bilateralFilter(img, 75, 15, 75)
    return bilateralFilter


def toGrey(img):
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return grey


def t(img, threshold=80):
    thresh = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    return thresh[1]


def at(img, block_size=13, c=11):
    thresh = adaptiveThreshold = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                                       block_size, c)
    return thresh


def otsu(img):
    binaryThreshold = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binaryThreshold[1]


def testExists(path):
    if not os.path.exists(path):
        print('Path does not exist: ' + str(path))
        print('Creating folder:  ' + str(path))
        os.makedirs(path)


def getFilesOnly(path):
    filesList = []
    notFilesList = []
    for name in os.listdir(path):
        if os.path.isfile(os.path.join(path, name)):
            if not name == 'desktop.ini':
                filesList.append(name)
        else:
            notFilesList.append(name)
    return filesList, notFilesList


def processRL(img):
    import skimage
    from skimage.segmentation import clear_border
    from skimage.measure import label
    from skimage.morphology import remove_small_objects, binary_erosion, binary_dilation
    from skimage.morphology import \
        disk  # https://scikit-image.org/docs/stable/auto_examples/numpy_operations/plot_structuring_elements.html#sphx-glr-auto-examples-numpy-operations-plot-structuring-elements-py

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    smoothImg = smooth(lab)

    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(30, 30))
    claheImg = clahe.apply(smoothImg[:, :, 0])

    otsuImg = otsu(claheImg)
    otsuInv = cv2.bitwise_not(otsuImg)

    dilate = binary_dilation(otsuInv, disk(1))
    fill = ndimage.binary_fill_holes(dilate).astype(int)
    clearBorder = clear_border(fill)
    labelim = label(clearBorder)

    erode = binary_erosion(labelim, disk(4))
    remSmall = remove_small_objects(erode, min_size=500, in_place=False)
    labelIm2 = label(remSmall)

    return labelIm2


def plot(img, title):
    fig = plt.figure(figsize=(8, 8), dpi=200)
    fig.subplots_adjust(wspace=0.03, hspace=0.03)
    plt.subplot(1, 1, 1)
    plt.title(title)
    plt.axis('off')
    plt.imshow(img)


def removeSmallObjects(img, factor=6):
    from skimage.morphology import remove_small_objects, binary_erosion, binary_dilation, binary_opening
    from skimage.measure import regionprops
    from skimage.measure import label
    labelim = label(img)
    props = regionprops(labelim)
    areaList = []
    for x in range(0, len(props)):
        areaList.append(props[x].area)

    areaList.sort(reverse=True)
    print(areaList)
    if len(areaList) > 0:
        maxArea = areaList[0]
        print(maxArea)
        min_size = maxArea / factor
        print('min_size', min_size)
        remSmall = remove_small_objects(labelim, min_size, in_place=False)

    return remSmall

def binarise(fileTL,fileRL,saveLocation,dpi):
    # Read in the files
    imgTL = cv2.imread(fileTL)
    img = cv2.imread(fileRL)
    #plot(img, 'Original RL Image')
    #plot(imgTL, 'Original TL Image')

    # Process RL image:
    grayRL = toGrey(img)
    smoothImgRL1 = smooth(grayRL)
    smoothImgRL2 = smooth(smoothImgRL1)
    #plot(smoothImgRL2, 'Smoothed RL Image')

    otsuImgRL = otsu(smoothImgRL2)
    #plot(otsuImgRL, 'otsuImg RL Threshold')

    fillRL = ndimage.binary_fill_holes(otsuImgRL).astype(int)
    fillRL_uint8 = fillRL.astype('uint8')  # fillRL.astype('uint8')
    fillRL_uint8[fillRL_uint8 > 0] = 255
    #plot(fillRL_uint8, 'Holes Filled 1')

    # Process TL image:
    grayTL = toGrey(imgTL)
    smoothImgTL1 = smooth(grayTL)
    smoothImgTL2 = smooth(smoothImgTL1)
    #plot(smoothImgTL2, 'Smoothed TL Image')

    otsuImgTL = otsu(smoothImgTL2)
    otsuInvTL = cv2.bitwise_not(otsuImgTL)
    otsuInvTL_uint8 = otsuInvTL.astype('uint8')
    otsuInvTL_uint8[otsuInvTL_uint8 > 0] = 255
    #plot(otsuInvTL_uint8, 'otsuInvTL Threshold')

    # Add the images together:
    addImg = cv2.add(otsuInvTL_uint8, fillRL_uint8)
    #plot(addImg, 'fillRL(otsu) + TLotsuInv ')


    # Once the image is binarised, get the contours
    imCopy = cv2.imread(fileTL)  # import image as RGB for plotting contours in colour
    contours, hierarchy = cv2.findContours(addImg, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE, cv2.RETR_EXTERNAL
    #cv2.drawContours(imCopy, contours, -1, color=(100, 0, 0),thickness=1)  # draw the contours on the colour image that was imported.This lets me see the contours in colour.
    #plot(imCopy, 'Contours')

    # Convert contours to a mask image
    mask = np.zeros((imCopy.shape[0], imCopy.shape[1]), dtype=np.uint8)
    areaList = []
    for cnt in contours:
        if len(cnt) < 3: #i.e. if the contour is a two-point line
            pass
        else:
            contArea = cv2.contourArea(cnt, False)
            if contArea == 0: #ignore contours that aren't closed polygons
                pass
            elif contArea < 50: #ignore small contour areas. This value should be optimised somehow.
                pass
            else:
                areaList.append(contArea)
                squeeze = np.squeeze(cnt)
                x, y = zip(*squeeze)
                newXY = list(zip(y, x))
                contMask = skimage.draw.polygon2mask((imCopy.shape[0], imCopy.shape[1]), newXY)
                mask = mask + contMask
                mask[mask == 2] = 0
    #plot(mask, 'Mask Img')

    #The images can have artifacts like bubble rims. This should remove them.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    opening[opening == 1] = 255 #ensure that the values in the binarised image range from 0-255
    opening_uint8 = opening.astype('uint8')
    height, width = opening_uint8.shape

    fig = plt.figure(figsize=(float(width / dpi), float(height / dpi)))
    plt.imshow(opening_uint8, cmap='Greys_r')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.axis('off')
    plt.savefig(saveLocation, bbox_inches=None, dpi=dpi, pad_inches=0)



