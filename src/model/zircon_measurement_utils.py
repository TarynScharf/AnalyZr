import cv2
import numpy as np
from scipy.spatial.distance import pdist
from skimage.measure import find_contours
from skimage.util import pad


def calcFormula(pt1, pt2):
    m = (pt2[0] - pt1[0]) / (pt2[1] - pt1[1])
    c = pt[0] - m * pt[1]
    return m, c


def feret_diameter(blob):  # adapted from here: https://github.com/scikit-image/scikit-image/blob/332adb877c11a03e7406942a143ea745c50e2d2a/skimage/measure/_regionprops.py
    padBlob = pad(blob, pad_width=(5, 5), mode='constant', constant_values=0)
    contours = find_contours(padBlob, 0.5, fully_connected='high')
    u8 = padBlob.astype(np.uint8)
    contoursCV, heirarchy = cv2.findContours(u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    copyBlob = np.float32(padBlob)
    cv2.drawContours(copyBlob, contoursCV, -1, (255, 255, 255), 1)

    contours = find_contours(padBlob, 0.5, fully_connected='high')
    distances = pdist(np.vstack(contours))
    maxFeret = np.max(distances)
    # Get min Feret Diameter
    coordinates = np.array(contours)
    coordsF32 = coordinates.astype(np.float32)
    box = cv2.minAreaRect(coordsF32)  # returned: (x,y), (w,h), angle
    # print(box)
    width = box[1][0]
    minFeret = 0
    height = box[1][1]
    if width > height:
        minFeret = height
    else:
        minFeret = width
    rect = cv2.boxPoints(box)

    return maxFeret, minFeret
