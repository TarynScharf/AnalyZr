import csv
import datetime
import json
import math
import os
import tkinter as tk

import cv2
import matplotlib
import numpy as np
import shapely
# import skimage.segmentation because else it
# says there's no segmentation module
#https://www.codegrepper.com/code-examples/python/AttributeError%3A+module+%27skimage%27+has+no+attribute+%27segmentation%27
import skimage.segmentation
from PIL import ImageTk
from PIL import Image
from scipy import ndimage

from src.model import ZirconSeparationUtils, zircon_measurement_utils
from src.model.composite_contour import CompositeContour
from src.model.drawing_objects.breakline import Breakline
from src.model.drawing_objects.contour import Contour
from src.model.drawing_objects.rectangle import RectangleType
from src.model.image_data import ImageData
from src.model.region_measurements import RegionMeasurement


class Model():
    def __init__(self):

        self.image_folder_path = None
        self.json_folder_path = None  # where json files are stored.


        self.maskPath = ''
        self.contours_by_group_tag = {}  # a list of all the polygon objects to turn into  binary masks
        self.deleted_contours = []  # in case of an undo
        self.Current_Image = 'TL'  # tracks which image type is displayed
        self.width = 0  # used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.height = 0  # used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.breaklines = []
        self.saveLocation = 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/_o.png'  # where the 1st binarised image will output to
        self.case = ''  # the function of the browse button. I.e. browse for capture, RL or TL
        self.img = None
        self.currentSpotNumber = tk.StringVar()
        self.image_iterator_current = None
        self.spotPointCount = 0

        self.text_label = ''  # label for duplicate grains and spot scales
        self.count = 0  # Used to put id's onto break  lines

        self.x0 = None
        self.y0 = None
        self.labelID = ''
        self.spotCount = 0
        self.rectangle = None

        self.jsonList = []

        self.unique_sample_numbers = {}  # a dictionary of all samples numbers of all images loaded for spot capture. Contains unique sample numbers only. Records spots per sample.
        self.sampleList = []  # a list of all sample numbers of all images loaded for spot capture. May contain duplicates.
        self.error_message_text = ''
        self.currentSample = None

        self.boundaryPoints = []  # This MUST be cleared every time the polygon is saved
        self.thisPoly = None  # This MUST be set back to NONE every time the polygon is saved
        self.polyCoords = []  # Coordinates of the polygon currently active. This MUST be set back to [] every time the polygon is saved
        self.coordID = []  # List of coordinate ID's for the polygon currently active. This MUST be set back to [] every time the polygon is saved
        self.Move = False  # Whether or not a move action can take place. Records true/false if an existing entity was selected
        self.all_contours = {}  # ID-coordinate dictionary of all polygons on the page


        self.threshold = None
        self.spotID = ''  # used when repositioning spots
        self.ProcessFolderFlag = False  # flag that tracks whether an entire folder of masks is to be processed
        self.currentMask = None  # if processing an entire mask folder, keep track of the current mask's file path

        self.current_image_index = 0 #incrementor that keeps track of where we are in the list of images when displaying them for data capture

    def DeleteObject(self, group_tag, coords):
        if 'line_' in group_tag: #breaklines don't get written to a json file
            x1 = coords[0]
            y1 = coords[1]
            x2 = coords[2]
            y2 = coords[3]
            self.breaklines.remove([(x1, y1), (x2, y2)])

        elif 'contour_' in group_tag:
            self.delete_contour(group_tag)

        elif 'extcont_' in group_tag:
            contour_coords = self.contours_by_group_tag[group_tag].paired_coordinates()
            polygon = shapely.Polygon(contour_coords)  # create a shapely polygon
            representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
            self.threshold = skimage.label(self.threshold, background=0, connectivity=None).astype('uint8')
            blob_label = self.threshold[int(representative_point.y),int(representative_point.x)]
            if int(blob_label)!=0:
                self.threshold[self.threshold==blob_label]=0
            self.delete_contour(group_tag)

        else:
            with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), errors='ignore') as jsonFile:  # open the json file for the image
                data = json.load(jsonFile)
            for i in range(0, len(data['regions'])):  # If the object already exists in the json
                if data['regions'][i]['id'] == group_tag:
                    data['regions'].pop(i)  # get rid of it. Don't read further (affects incrementor?)
                    break
            with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)  # rewrite the json without the object
            try:
                self.unique_sample_numbers[self.currentSample].discard(group_tag)
            except:
                pass

    def delete_contour(self, group_tag):
        self.deleted_contours.append(self.contours_by_group_tag[group_tag])  # store the last contour to be deleted
        del self.contours_by_group_tag[group_tag]

    def SavePolygon(self):
        x_list = []
        y_list = []
        polyCoords = []

        for point in self.all_contours[self.uniqueTag]:
            x_list.append(point[1])  # get a list of all the x-coords. This makes it easy to  get min and max x
            y_list.append(point[2])  # get a list of all the y-coords.This makes it easy to get min and max y
            polyCoords.append({"x": point[1], "y": point[2]})  # get a list of each coord pair. This makes it easy to write the poly to the json file
        # Get the new bounding box for the polygon
        top = min(y_list)  # y increases downwards
        left = min(x_list)  # x increases to the right
        height = abs(max(y_list) - min(y_list))
        width = abs(max(x_list) - min(x_list))
        boundingBox = {"height": height, "width": width, "left": left, "top": top}

        with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)
            anyMatch = False
            for region in data['regions']:
                if region['id'] == self.uniqueTag:  # If the polygon already exists in the jSON
                    region["boundingBox"] = boundingBox
                    region["points"] = polyCoords

                else:  # if it's newly digitised and does not yet exist in the json file, and it's a polygon
                    newRegion = {"id": self.uniqueTag, "type": self.Type, "tags": ["RL"], "boundingBox": boundingBox,
                                 "points": polyCoords}
                    data['regions'].append(newRegion)

        with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)
        self.uniqueTag = None
        self.groupTag = None


    def add_new_contour(self, contour):
        self.all_contours[contour.unique_tag] = contour
        return contour

    def SaveBreakChanges(self,RLPath, TLPath, new_boundary = None):
        updatedMask = self.convert_contours_to_mask_image(self.height, self.width, self.contours_by_group_tag.values())

        if new_boundary != None: # if the user has digitised a new grain boundary manually
            points = np.array(new_boundary.paired_coordinates(),'int32')
            updatedMask = cv2.fillPoly(updatedMask,[points], color=(255,255,255))


        for breakline in self.breaklines:
            updatedMask = cv2.line(updatedMask, (int(breakline.x0), int(breakline.y0)), (int(breakline.x1),int(breakline.y1)), (0,0,0),2)
        self.breaklines = []

        self.threshold = updatedMask

        updatedMask[updatedMask > 0] = 255
        labelim = skimage.measure.label(updatedMask, background=0, connectivity=None)
        self.threshold = labelim.astype('uint8')

        if TLPath != '' and self.Current_Image=='TL':
            original_Image = cv2.imread(TLPath)

        elif RLPath != '' and self.Current_Image=='RL':
            original_Image = cv2.imread(RLPath)

        image_pill = Image.fromarray(original_Image)
        self.img = ImageTk.PhotoImage(image=image_pill)
        contours = self.extract_contours_from_image('extcont')

        return image_pill, contours


    def extract_contours_from_image(self,prefix,filter_fn = None):
        # paint the contours on
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        count_contour = 0
        self.contours_by_group_tag.clear()
        for i in range(len(contoursFinal)):
            if len(contoursFinal[i]) < 3:
                continue

            if filter_fn is not None and not filter_fn(contoursFinal[i]):
                continue

            coordinate_pairs = np.squeeze(contoursFinal[i])
            groupID = prefix+"_" + str(count_contour)
            polygon = Contour(groupID, coordinate_pairs)
            self.contours_by_group_tag[polygon.group_tag] = polygon
            count_contour += 1


        return list(self.contours_by_group_tag.values())


    def update_spot_in_json_file(self,spotID, x0,y0):
        fileLocation = self.json_folder_path.get()

        for path, folder, files in os.walk(fileLocation):
            for name in files:
                if name == self.jsonName:  # find the json file that relates to the pdf page (image) under consideration
                    with open(os.path.join(fileLocation, self.jsonName), errors='ignore') as jsonFile:
                        data = json.load(jsonFile)
                    for region in data['regions']:
                        t_regionID = self.File_Location.get().split('/')[-1].split('_')
                        regionID = '_'.join(t_regionID[4:]).replace('.png', '')
                        if region['id'] == regionID:
                            imageTop = region['boundingBox']['top']  # find out the starting point (top left) of the photo under consideration
                            imageLeft = region['boundingBox']['left']
                            imageWidth = region['boundingBox']['width']
                            imageHeight = region['boundingBox']['height']
                        if region['id'] == spotID and region['type'] == 'POINT':
                            x = x0 + imageLeft
                            y = y0 + imageTop
                            newPoints = [{"x": x, "y": y}]
                            region["points"] = newPoints
                        elif region['id'] == spotID and region['type'] == 'RECTANGLE':
                            left_x = x0 - (region['boundingBox']['width'] / 2) + imageLeft
                            right_x = x0 + (region['boundingBox']['width'] / 2) + imageLeft
                            top_y = y0 - (region['boundingBox']['height'] / 2) + imageTop
                            bottom_y = y0 + (region['boundingBox']['height'] / 2) + imageTop
                            newPoints = [{"x": left_x, "y": top_y}, {"x": right_x, "y": top_y}, {"x": right_x, "y": bottom_y}, {"x": left_x, "y": bottom_y}]
                            region["boundingBox"] = {
                                "height": region["boundingBox"]['height'],
                                "width": region["boundingBox"]['width'],
                                "left": left_x,
                                "top": top_y
                            }
                            region["points"] = newPoints

                    with open(os.path.join(fileLocation, self.jsonName), 'w', errors='ignore') as updatedFile:
                        json.dump(data, updatedFile, indent=4)

    def save_drawing_object_to_json(self, object):

        with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        newRegion = object.to_json_data()
        data['regions'].append(newRegion)

        with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)


    def update_spot_in_json(self, spot, previous_group_tag):
        with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)
            anyMatch = False
            for region in data['regions']:  # If the spot already exists in the jSON
                if region['id'] == previous_group_tag:
                    region['id'] = spot.group_tag
                    anyMatch = True

            #if anyMatch == False and Type == "POINT":  # if it's newly digitised and does not yet exist in the json file, and it's a point
            if anyMatch == False:
                data['regions'].append(spot.to_json_data())

            '''if anyMatch == False and Type == "RECTANGLE":  # if it's newly digitised and does not yet exist in the json file, and it's a rectangle
                height = abs(self.rectStart_y - self.updatedY)
                width = abs(self.rectStart_x - self.updatedX)

                if self.rectStart_x < self.updatedX:  # x increases left to right
                    left = self.rectStart_x
                    right = self.updatedX
                else:
                    left = self.updatedX
                    right = self.rectStart_x

                if self.rectStart_y < self.updatedY:  # y increases top to bottom
                    top = self.rectStart_y
                    bottom = self.updatedY
                else:
                    top = self.updatedY
                    bottom = self.rectStart_y

                newRegion = {"id": userText, "type": self.Type, "tags": ["SPOT"],
                             "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                             "points": [{"x": left, "y": top}, {"x": right, "y": top}, {"x": right, "y": bottom},
                                        {"x": left, "y": bottom}]}
                data['regions'].append(newRegion)'''

        with open(os.path.join(self.json_folder_path, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)

    def insert_new_breakline_to_pairslist(self,breakline):
        self.breaklines.append(breakline)

    def set_json_folder_path(self,path):
        self.json_folder_path.set(path)

    def load_mask_from_file(self,path):
        self.threshold = cv2.imread(path)[:, :, 0]
        self.threshold[self.threshold > 0] = 255
        jsonName = '_'.join(path.split('/')[-1].split('_')[:3]) + '.json'
        sampleid = jsonName.split('_')[0]
        if len(path.split('/')[-1].split('_')) > 2:
            regionID = path.split('/')[-1].split('_')[-1].replace('.png', '')
        else:
            regionID = ""

        if self.json_folder_path is None:
            return None

        with open(os.path.join(self.json_folder_path, jsonName), errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        # if regionID in data["regions"]:
        for region in data["regions"]:
            if region["id"] == regionID:
                return region

    def load_current_mask(self):
        self.threshold = cv2.imread(self.currentMask)[:, :, 0]

    def undo_delete_contour(self):
        if len(self.deleted_contours)==0:
            return None
        contour_to_restore = self.deleted_contours.pop(-1)
        self.contours_by_group_tag[contour_to_restore.group_tag] = contour_to_restore
        return contour_to_restore

    def check_for_images_and_jsons(self, image_folder_path, json_folder_path):
        has_images = False
        missing_json_files = []
        for path, folders, files in os.walk(image_folder_path):
            for name in files:
                if os.path.splitext(name)[1] == '.png':  # check for images
                    has_images = True
                    json_file = os.path.splitext(name)[0] + '.json'
                    has_json = self.does_json_exist(os.path.join(json_folder_path, json_file))
                    if not has_json:
                        missing_json_files.append(name)
        return has_images, missing_json_files

    def does_json_exist(self, json_file):
        return os.path.exists(json_file)


    def write_json_file(self,file):
        file_extension = os.path.splitext(file)[-1]
        path  = os.path.join(self.json_folder_path.get(), file)
        img = cv2.imread(path)[:,:,0]
        json_name = os.path.splitext(file)[0]+".json"
        data = {"asset": {
                    "format": file_extension,
                    "id": hash(file),
                    "name": file,
                    "path": path,
                    "size": {
                            "width":img.shape[1],
                            "height":img.shape[0]
                            },

                    },
                "regions":[]
               }

        with open(os.path.join(self.json_folder_path.get(), json_name), 'w', errors='ignore') as new_json:
            json.dump(data, new_json, indent=4)

    def read_sampleID_and_spots_from_json(self):
        # Get a list of unique sample ID's and the spots associated with them.
        for path, folders, files in os.walk(self.json_folder_path):
            for name in files:
                if os.path.splitext(name)[1] == '.json':
                    with open(os.path.join(self.json_folder_path, name), errors='ignore') as jsonFile:
                        data = json.load(jsonFile)
                    if not name in self.jsonList:
                        self.jsonList.append([name, data['asset'][
                            'name']])  # add the image name to the list of json files, as jsons and images have same name
                        sampleID = data['asset']['name'].split("_")[0]
                        if sampleID not in self.unique_sample_numbers:  # create a dictionary with unique sample numbers only
                            self.unique_sample_numbers[sampleID] = set()
                            self.sampleList.append(sampleID)
                            for region in data[
                                'regions']:  # everytime we find a json with a unique sample number, don't forget to get the spots listed in that json
                                self.unique_sample_numbers[sampleID].add(region['id'])
                        else:  # you might find jsons with existing sample numbers. They may also contains spots, record those spots.
                            for region in data['regions']:
                                self.unique_sample_numbers[sampleID].add(region['id'])

        self.sampleList.sort()

    def write_to_csv(self,filepath):
        colArray = ['sampleid', 'image_id', 'grain_number', 'grain_centroid', 'grain_spots', 'area',
                    'equivalent_diameter', 'perimeter', 'minor_axis_length', 'major_axis_length',
                    'solidity', 'convex_area', 'formFactor', 'roundness', 'compactness', 'aspectRatio', 'minFeret',
                    'maxFeret', 'contour', 'image_dimensions', 'mask_image']

        with open(filepath, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(colArray)

            for row in self.dfShapeRounded.itertuples(False):
                data = []
                if row[4] != ' ':
                    spots = row[4].split(',')
                    for spot in spots:
                        data = []
                        for x in range(len(row)):
                            if x != 4:
                                data.append(row[x])
                            else:
                                data.append(spot)
                        csv_writer.writerow(data)

                else:
                    data = []
                    for i in range(len(row)):
                        data.append(row[i])
                    csv_writer.writerow(data)

    def push_shape_measurements_to_database(self):
        # push the shape descriptors to the shape_descriptor table
        connection = pyodbc.connect(
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:/Users/20023951/Documents/PhD/GSWA/GSWA_2019Geochron/DATABASES/Test.mdb')  # Set up a connection string
        colArray = 'sampleid, image_id, grain_number,grain_centroid, grain_spots, area, equivalent_diameter, perimeter, minor_axis_length,major_axis_length, solidity, convex_area, formFactor,roundness, compactness, aspectRatio, minFeret, maxFeret, contour, image_dimensions,mask_image'
        cursor = connection.cursor()
        if self.jsonName == '':
            self.error_message_text = 'Shapes have not been measured'
            self.open_error_message_popup_window()
            return
        elif self.File_Location.get() != '':
            maskName = self.File_Location.get().split('/')[-1]
            t_regionID = maskName.split('_')
            regionID = '_'.join(t_regionID[4:]).replace('.png', '')
        elif self.currentMask is not None:
            maskName = self.currentMask.split('/')[-1]
            t_regionID = maskName.split('_')
            regionID = '_'.join(t_regionID[4:]).replace('.png', '')
        queryStatement = "Select * from shape_descriptors where image_id = '" + regionID + "'"

        cursor.execute(queryStatement)
        results = cursor.fetchall()

        if len(results) == 0:
            for row in self.dfShapeRounded.itertuples(False):
                valuesString = ''

                for i in range(len(row)):
                    if i < len(row) - 1:
                        if i == 18 or i == 4 or i == 19 or i == 3 or i == 1:
                            valuesString = valuesString + "'" + str(row[i]) + "',"
                        else:
                            valuesString = valuesString + str(row[i]) + ','

                    if i == len(row) - 1:
                        valuesString = valuesString + "'" + str(row[i]) + "'"

                insertStatement = '''INSERT INTO shape_descriptors(''' + colArray + ''') VALUES(''' + valuesString + ''')'''

                cursor.execute(insertStatement)
                cursor.commit()
            cursor.close()
            connection.close()
            print('Insert complete: ', regionID)
        else:
            cursor.close()
            connection.close()
            print('Sample already in DB: ', regionID)

    def write_mask_to_png(self,fileRL,fileTL,maskPath):

        self.threshold[self.threshold > 0] = 255

        jsonName = ''
        regionID = ''

        if fileRL != '':
            fileName = fileRL.split('/')[-1]
            jsonName = '_'.join(fileName.split('_')[:3]) + '.json'
            t_regionID = fileName.split('_')
            regionID = '_'.join(t_regionID[4:]).replace('.png', '')

        elif self.File_Location.get() != '':
            fileName = self.File_Location.get().split('/')[-1]
            jsonName = '_'.join(fileName.split('_')[:2])

        maskPath = os.path.join(maskPath, fileName)
        if self.json_folder_path is None or self.json_folder_path == '':
            self.error_message_text = 'JSON file location has not been set'
            self.open_error_message_popup_window()
            return
        else:
            with open(os.path.join(self.json_folder_path, jsonName), errors='ignore') as jsonFile:
                data = json.load(jsonFile)
            for region in data['regions']:
                if region['id'] == regionID:
                    region["RL_Path"] = fileRL
                    region["TL_Path"] = fileTL
                    region["Mask_Path"] = maskPath

            with open(os.path.join(self.json_folder_path, jsonName), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)

        cv2.imwrite(maskPath, self.threshold)

    def next_image(self):
        if self.current_image_index < len(self.jsonList)-1:
            self.current_image_index += 1

    def previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1

    def get_current_image_for_data_capture (self):
        #This is for cycling through images associated with json files when capturing spots
        self.image_iterator_current = self.jsonList[self.current_image_index]
        im = self.image_iterator_current[1]
        jf = self.image_iterator_current[0]

        self.currentSample = im.split("_")[0]
        fileName = os.path.join(self.image_folder_path, im)
        image = Image.open(fileName)
        json_file_path = os.path.join(self.json_folder_path, jf)

        with open(json_file_path, errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        image_data = ImageData.fromJSONData(data,json_file_path)
        return image, image_data

    def get_region_and_sample_id(self, mask_file_path,ProcessFolderFlag,RLPath):
        if mask_file_path != '':  # if we're processing a single mask image
            fPath = mask_file_path
        elif ProcessFolderFlag == True:  # if we are processing an entire folder of masks
            fPath = self.currentMask
        else:  # if we are processing an image we have just binarised
            fPath = RLPath

        jsonName = '_'.join(fPath.split('/')[-1].split('_')[:3]) + '.json'
        sampleid = jsonName.split('_')[0]
        t_regionID = fPath.split('/')[-1].split('_')
        regionID = '_'.join(t_regionID[4:]).replace('.png', '')

        return sampleid, regionID,jsonName

    def preprocess_image_for_measurement(self, mask_file_path):
        if mask_file_path != '' and self.threshold is None:
            self.threshold = cv2.imread(mask_file_path)[:, :, 0]
            self.width = self.threshold.shape[1]
            self.height = self.threshold.shape[0]
        image_remove = ZirconSeparationUtils.removeSmallObjects(self.threshold,15)  # remove small objects below a threshold size (max object size/15)
        image_clear = ZirconSeparationUtils.clear_border(labels=image_remove, bgval=0,buffer_size=1)  # remove objects that touch the image boundary
        image_clear_uint8 = image_clear.astype('uint8')

        return image_clear_uint8

    def read_spots_unwanted_scale_from_json(self,json_file_path,regionID):
        imageDimensions = ''  # this will record the XY dimensions of the cropped image, so that the contours can be redrawn on a blank image in the event that the cropped image  file is ever lost
        spot = False
        spotList = []
        dupList = []
        for path, folder, files in os.walk(json_file_path):
            for name in files:
                if name == self.jsonName:  # find the json file that relates to the pdf page (image) under consideration
                    scaleFlag = False
                    spotList = []
                    dupList = []
                    with open(os.path.join(json_file_path, self.jsonName), errors='ignore') as jsonFile:
                        data = json.load(jsonFile)

                    for region in data['regions']:
                        if regionID == "":  # if the photo  in question does not comprise subregions (i.e. not a photo collage)
                            imageTop = 0  # find out the starting point (top left) of the photo under consideration
                            imageLeft = 0
                            imageWidth = data["asset"]["size"]["width"]
                            imageHeight = data["asset"]["size"]['height']
                            imageDimensions = str(imageTop) + ',' + str(imageLeft) + ',' + str(
                                imageTop + imageWidth) + ',' + str(
                                imageLeft + imageHeight)  # record those photo dimensions for use later
                        elif region['id'] == regionID:  # if the photo in question is a subregion of the original image
                            imageTop = region['boundingBox'][
                                'top']  # find out the starting point (top left) of the photo under consideration
                            imageLeft = region['boundingBox']['left']
                            imageWidth = region['boundingBox']['width']
                            imageHeight = region['boundingBox']['height']
                            imageDimensions = str(imageTop) + ',' + str(imageLeft) + ',' + str(
                                imageTop + region['boundingBox']['width']) + ',' + str(
                                imageLeft + region['boundingBox'][
                                    'height'])  # record those photo dimensions for use later
                        if region['tags'][0] == 'SPOT' and region[
                            'type'] == 'POINT':  # this will look for all spots in the pdf page, regardless of whether or not they are actually on the cropped image under consideration
                            spot = True
                            x = region['points'][0]['x']
                            y = region['points'][0]['y']
                            spotID = region['id']
                            newX = x - imageLeft
                            newY = y - imageTop
                            # print('spotID: ', spotID, ' | x: ', x, ' | y: ', y, ' | newX: ', newX, ' | newY: ', newY)
                            if x >= imageLeft:
                                if x <= imageLeft + imageWidth:
                                    if y >= imageTop:
                                        if y <= imageTop + imageHeight:
                                            spotList.append([newX, newY, spotID])
                        if region[
                            'type'] == 'SCALE':  # this will look for all scales (there should only be 1) on the pdf page, regardless of whether or not they are actually on the cropped image under consideration
                            delta_x = abs(region['points'][0]['x'] - region['points'][1][
                                'x'])  # diff in x between THIS node and other nodes
                            delta_y = abs(region['points'][0]['y'] - region['points'][1][
                                'y'])  # diff in y between THIS node and other nodes
                            distance = math.sqrt(
                                (delta_x ** 2) + (delta_y ** 2))  # pixel distance, equivalent to 100 microns
                            scaleFlag = True
                            micPix = 100 / distance
                        if region['type'] == 'RECTANGLE' and region['tags'][
                            0] == 'SPOT':  # this will look for all rectanglular scales on the pdf page, regardless of whether or not they are actually on the cropped image under consideration
                            spot = True
                            x = region['boundingBox']['left'] + (region['boundingBox']['width'] / 2)
                            y = region['boundingBox']['top'] + (region['boundingBox']['height'] / 2)
                            spotID = region['id']
                            newX = x - imageLeft
                            newY = y - imageTop
                            if x >= imageLeft:
                                if x <= imageLeft + imageWidth:
                                    if y >= imageTop:
                                        if y <= imageTop + imageHeight:
                                            spotList.append([newX, newY, spotID])
                            # ('rectangle scale detected')
                            scaleFlag = True
                            micPix = 30 / ZirconSeparationUtils.getScale(name, path, 'SPOT')
                            # print('micron per pixel: ', micPix)
                        if region['type'] == 'RECTANGLE' and region['tags'][0] == RectangleType.DUPLICATE:
                            x = region['boundingBox']['left'] + (region['boundingBox']['width'] / 2)
                            y = region['boundingBox']['top'] + (region['boundingBox']['height'] / 2)
                            newX = x - imageLeft
                            newY = y - imageTop
                            if x >= imageLeft:
                                if x <= imageLeft + imageWidth:
                                    if y >= imageTop:
                                        if y <= imageTop + imageHeight:
                                            dupList.append([newX, newY])
                    if spot == False:
                        print('No spot in image')

                    if scaleFlag == False or micPix < 0:
                        scale = ZirconSeparationUtils.getScale(name, path, 'SPOT')
                        if scale == -1:
                            self.error_message_text = 'No scale available in sample'
                            self.open_error_message_popup_window()
                            return
                        else:
                            micPix = 30 / scale

        return spotList,dupList,micPix,imageDimensions

    def remove_unwanted_objects_from_binary_image(self,objects_to_remove):
        for unwanted_object in objects_to_remove:
            label = self.threshold[int(unwanted_object[1]), int(unwanted_object[0])]
            if label != 0:
                self.threshold[self.threshold == label] = 0

    def find_spots_in_region(self,label,contoursFinal,spotList):
        spots = []
        for contour in contoursFinal:
            polygon = shapely.Polygon(np.squeeze(contour))  # create a shapely polygon
            representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
            # get the region label at the representative point
            region_label = self.threshold[int(representative_point.y), int(representative_point.x)]
            if region_label == label:  # is this boundary around the region in question?
                boundary = matplotlib.path.Path(np.squeeze(contour), closed=True)
                for spot in spotList:
                    spotInside = boundary.contains_point([spot[0], spot[1]])
                    if spotInside == True:
                        # a grain may have more than 1 spot associated with it. Find all spots associated with the grain
                        spots.append(spot[2])

                return ','.join(spots),contour
        return '',None

    def create_measurement_table(self,sampleid,regionID,imageDimensions,micPix, mask_file_path):
        self.contours_by_group_tag = {}
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE,
                                                         cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE, cv2.RETR_EXTERNAL
        props = skimage.regionprops(self.threshold)

        measurements = []

        for x in range(0, len(props)):
            # Convex image is good enough because it'll give us the max points and min edges for maxFeret and minFeret
            maxFeret, minFeret = zircon_measurement_utils.feret_diameter(props[x].convex_image)
            spot_list,contour = self.find_spots_in_region(props[x].label)
            measurement = RegionMeasurement(
                    sampleid = sampleid,
                    image_id = regionID,
                    grain_number = props[x].label,
                    centroid = props[x].centroid,
                    grainspot = spot_list,
                    area = props[x].area * (micPix ** 2),
                    equivalent_diameter = props[x].equivalent_diameter * micPix,
                    perimeter = props[x].perimeter * micPix,
                    minor_axis_length = props[x].minor_axis_length * micPix,
                    major_axis_length = props[x].major_axis_length * micPix,
                    solidity = props[x].solidity,
                    convex_area = props[x].convex_area * (micPix ** 2),
                    maxFeret = maxFeret * micPix,
                    minFeret = minFeret * micPix,
                    contour = contour,
                    image_dimensions =imageDimensions,
                    mask_image =mask_file_path)
            measurements.append(measurement)

        return measurements

    def create_labeled_image(self,region_measurements, TLPath, RLPath):
        if self.Current_Image == 'TL' and TLPath != '':
            img_to_display = cv2.imread(TLPath)
        elif self.Current_Image == 'RL' and RLPath != '':
            img_to_display = cv2.imread(RLPath)
        else:
            self.threshold[self.threshold > 0] = 255
            img_to_display = np.stack((self.threshold,) * 3, axis=-1)

        # cv2.imwrite('C:/Users/20023951/Documents/PhD/Reporting/Paper1_ZirconSeparationUtility/CaseStudy/CaseStudy_MaduraShelf/mask_img.jpg', img_to_display)
        for measurement in region_measurements:
            # img_to_display = cv2.circle(img_to_display, (int(centroid_List[i][1]), int(centroid_List[i][0])), 3, (0, 0, 255), 2)
            grain_centroid = measurement.grain_centroid
            cv2.putText(img_to_display, str(measurement.grain_number),
                        (int(grain_centroid[1] - 2), int(grain_centroid[0] - 2)), cv2.FONT_HERSHEY_DUPLEX, 0.3,
                        (0, 0, 255))

        return img_to_display

    def MeasureShapes(self, mask_file_path,TLPath, RLPath,processFolderFlag):
        self.jsonName = ''
        sampleid,regionID,self.jsonName = self.get_region_and_sample_id(mask_file_path,processFolderFlag,RLPath)
        self.preprocess_image_for_measurement(mask_file_path)

        json_file_path = self.json_folder_path.get()  # 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/t2_inv1_files'
        self.contours_by_group_tag={}

        spotList, dupList, micPix, imageDimensions = self.read_spots_unwanted_scale_from_json(json_file_path,regionID)

        self.remove_unwanted_objects_from_binary_image(dupList)

        region_measurements = self.create_measurement_table(sampleid,regionID,imageDimensions,micPix,mask_file_path)

        labeled_image = self.create_labeled_image(region_measurements,TLPath, RLPath)

        #for duplicate in dupList:
            #img_to_display = cv2.circle(img_to_display, (int(duplicate[0]), int(duplicate[1])), 1, (255, 255, 255), 1)
            #cv2.putText(img_to_display, 'Duplicate', (int(duplicate[0]) + 5, int(duplicate[1]) + 5), cv2.FONT_HERSHEY_DUPLEX,0.5, (255, 255, 255))

        #cv2.imwrite('C:/Users/20023951/Documents/PhD/Reporting/Paper1_ZirconSeparationUtility/CaseStudy/CaseStudy_MaduraShelf/labeled_mask.jpg',img_to_display)

        image_pill = Image.fromarray(labeled_image)
        self.view.display_image(image_pill)
        self.extract_contours_from_image("extcont")
        self.view.display_spots_during_measurement(spotList)

        self.display_measurement_table(region_measurements)

    def display_measurement_table(self,region_measurements):
        '''
        data = {'sampleid': sampleid_List,
                'image_id': regionid_List,
                'grain_number': label_List,
                'grain_centroid': centroid_List,
                'grainspot': spots_per_grain_List,
                'area': area_List,
                'equivalent_diameter': equivalent_diameter_List,
                'perimeter': perimeter_List,
                'minor_axis_length': minor_axis_length_List,
                'major_axis_length': major_axis_length_List,
                'solidity': solidity_List,
                'convex_area': convex_area_List,
                'formFactor': formFactor_List,
                'roundness': roundness_List,
                'compactness': compactness_List,
                'aspectRatio': aspectRatio_List,
                'minFeret': minFeret_List,
                'maxFeret': maxFeret_List,
                'contour': contour_List,
                'image_dimensions': imDimensions_List,
                'mask_image': maskImage_List
                }
        # Show me the table!
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        dfShape = pd.DataFrame(data)
        self.dfShapeRounded = dfShape.round(decimals=2)  # And I only want to see 2 decimal places
        print(self.dfShapeRounded) '''

    def binariseImages(self,RLPath, TLPath,rlVar,tlVar):
        self.breaklines == []
        self.contours_by_group_tag = {}
        self.deleted_contours = []
        fileRL = RLPath
        fileTL = TLPath

        if fileRL != '' and rlVar == 1:
            # Read in the files
            self.Current_Image = 'RL'
            img = cv2.imread(fileRL)
            self.width = img.shape[1]
            self.height = img.shape[0]

            # Process RL image:
            grayRL = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            smoothImgRL1 = cv2.bilateralFilter(grayRL, 75, 15, 75)
            smoothImgRL2 = cv2.bilateralFilter(smoothImgRL1, 75, 15, 75)
            otsuImgRL = cv2.threshold(smoothImgRL2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            fillRL = ndimage.binary_fill_holes(otsuImgRL).astype(int)
            fillRL_uint8 = fillRL.astype('uint8')
            fillRL_uint8[fillRL_uint8 > 0] = 255

        if fileTL != '' and tlVar== 1:
            # Read in the files
            imgTL = cv2.imread(fileTL)
            self.width = imgTL.shape[1]
            self.height = imgTL.shape[0]
            self.Current_Image = 'TL'

            # Process TL image:
            grayTL = cv2.cvtColor(imgTL, cv2.COLOR_BGR2GRAY)
            smoothImgTL1 = cv2.bilateralFilter(grayTL, 75, 15, 75)
            smoothImgTL2 = cv2.bilateralFilter(smoothImgTL1, 75, 15, 75)
            otsuImgTL = cv2.threshold(smoothImgTL2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            otsuInvTL = cv2.bitwise_not(otsuImgTL)
            otsuInvTL_uint8 = otsuInvTL.astype('uint8')
            otsuInvTL_uint8[otsuInvTL_uint8 > 0] = 255

        if fileRL != '' and fileTL != '' and rlVar == 1 and tlVar == 1:
            # Add the images together:
            self.Current_Image = 'TL'
            self.threshold = cv2.add(otsuInvTL_uint8, fillRL_uint8)
            imCopy = cv2.imread(fileTL)  # import image as RGB for plotting contours in colour
        elif fileRL != '' and rlVar ==1 and tlVar ==0:
            self.Current_Image = 'RL'
            self.threshold = fillRL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image
            imCopy = cv2.imread(fileRL)  # import image as RGB for plotting contours in colour
        elif fileTL != '' and tlVar ==1  and rlVar ==0:
            self.Current_Image = 'TL'
            self.threshold = otsuInvTL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image
            imCopy = cv2.imread(fileTL)
        elif fileTL != '' and fileRL != '' and tlVar ==1  and rlVar ==0:
            self.Current_Image = 'TL'
            self.threshold = otsuInvTL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image
            imCopy = cv2.imread(fileTL)

        # Once the image is binarised, get the contours
        self.erode_small_artifacts(self.threshold)
        self.width = self.threshold.shape[1]
        self.height = self.threshold.shape[0]
        image_pill = Image.fromarray(imCopy)


        def filter_polygon_by_area(contour):
            area = cv2.contourArea(contour, False)
            return area>=50

        contours = self.extract_contours_from_image('contour',filter_polygon_by_area)

        return image_pill, contours, self.width, self.height

    def convert_contours_to_mask_image(self,height,width, contourList):
        mask = np.zeros((height, width), dtype=np.uint8)
        for contour in contourList:
            newXY = contour.inverted_paired_coordinates() # skimage takes x,y in opposite order
            contMask = skimage.draw.polygon2mask((mask.shape[0], mask.shape[1]), newXY)
            skimage.segmentation.expand_labels(contMask,1)
            mask = mask + contMask
            mask[mask == 2] = 0
        return mask

    def erode_small_artifacts(self,mask):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2, 2))  # this large structuring element is designed to  remove bubble rims
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        opening[opening == 1] = 255
        opening_uint8 = opening.astype('uint8')
        self.threshold = opening_uint8

    def set_source_folder_paths(self, image_folder_path, json_folder_path):
        self.image_folder_path = image_folder_path
        self.json_folder_path = json_folder_path

    def get_current_sample_index(self):
        return self.sampleList.index(self.currentSample)

    def get_sample_count(self):
        return len(self.sampleList)

    def add_new_spot(self, spot):
        self.check_spot_id_is_unique(spot.group_tag)
        self.unique_sample_numbers[self.currentSample].add(spot.group_tag)
        self.save_drawing_object_to_json(spot)

    def update_spot_id(self, spot, new_ID):
        self.check_spot_id_is_unique(new_ID)
        previous_group_tag = spot.group_tag
        spot.group_tag = new_ID
        self.update_spot_in_json(spot, previous_group_tag)

    def check_spot_id_is_unique(self,ID):
        if ID in self.unique_sample_numbers[self.currentSample]:
            raise Exception('Spot number already captured for PDF: ' + str(self.currentSample))

    def get_current_image_contours(self):
        return self.contours_by_group_tag

    def separate(self,TLPath, RLPath):
        def filter_polygon_by_area(contour):
            area = cv2.contourArea(contour, False)
            return area>=50

        reconstructed_points = [] #for testing
        self.threshold = self.convert_contours_to_mask_image(self.height,self.width, self.contours_by_group_tag.values())

        contours, hierarchy = cv2.findContours(self.threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)  # get the new contours of the eroded masks
        hierarchy = np.squeeze(hierarchy)

        composite_contour_list = []
        for i in range(len(contours)):
            cnt = np.squeeze(contours[i]).tolist()
            composite_contour = CompositeContour(np.squeeze(contours[i]),i)
            composite_contour_list.append(composite_contour)

            if hierarchy.ndim == 1:
                composite_contour.has_parent = hierarchy[3] != -1
            else:
                composite_contour.has_parent = hierarchy[i][3] != -1

            if len(cnt) < 3: #if it is a straight line or a point, it is not a closed contour and thus not of interest
                composite_contour.keep_contour = False
                continue

            get_coefficients_result = ZirconSeparationUtils.get_efd_parameters_for_simplified_contour(composite_contour.original_points, composite_contour.has_parent, filter_polygon_by_area)
            if get_coefficients_result is None:
                composite_contour.keep_contour = False
                continue
            composite_contour.coefficients, composite_contour.locus, composite_contour.reconstructed_points = get_coefficients_result



            composite_contour.curvature_values, composite_contour.cumulative_distance = ZirconSeparationUtils.calculateK(composite_contour.reconstructed_points, composite_contour.coefficients) #composite_contour.reconstructed_points
            curvature_maxima_length_positions, curvature_maxima_values, curvature_maxima_x, curvature_maxima_y, non_maxima_curvature = ZirconSeparationUtils.FindCurvatureMaxima(composite_contour.curvature_values,composite_contour.cumulative_distance,composite_contour.reconstructed_points)
            node_curvature_values, node_distance_values, node_x, node_y = ZirconSeparationUtils.IdentifyContactPoints(curvature_maxima_length_positions, curvature_maxima_values, curvature_maxima_x, curvature_maxima_y, non_maxima_curvature)

            if node_curvature_values != []:
                composite_contour.max_curvature_values = node_curvature_values
                composite_contour.max_curvature_distance = node_distance_values
                #create_curvature_distance_plot(composite_contour)
            else:
                composite_contour.keep_contour = False

            if node_x !=[] and node_y !=[]:
                composite_contour.max_curvature_coordinates = list(zip(node_x,node_y))
            else:
                composite_contour.keep_contour = False


        groups = ZirconSeparationUtils.FindNestedContours(hierarchy)

        if TLPath != '':
            image_to_show = cv2.imread(TLPath)
            is_image_binary = False
        elif RLPath!='':
            image_to_show = cv2.imread(RLPath)
            is_image_binary = False
        else:
            image_to_show = self.threshold
            is_image_binary = True

        # now link all nodes within the groups:
        count = 0
        for group in groups:
            # get the contours that are relevant to the group in question:
            contour_group = []
            for index in group:
                for contour in composite_contour_list:
                    if contour.index == index and contour.keep_contour == True:  # watch out, what if the parent contour is removed?
                        contour_group.append(contour)
                        #composite_contour_list.remove(contour)  # if it's added to a group to be processed, remove it from the main group so that we don't have to include it in future loops
            if contour_group == []:
                continue
            pairs = ZirconSeparationUtils.linkNodes(contour_group)
            for ((x0,y0), (x1,y1)) in pairs:
                breakline = Breakline(x0,y0,x1,y1,'line_' + str(count))
                count += 1
                self.breaklines.append(breakline)

        return composite_contour_list, image_to_show, is_image_binary, self.breaklines

