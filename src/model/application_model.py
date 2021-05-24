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

from src.model import ZirconSeparationUtils, zircon_measurement_utils, FileUtils
from src.model.composite_contour import CompositeContour
from src.model.drawing_objects.breakline import Breakline
from src.model.drawing_objects.contour import Contour
from src.model.drawing_objects.rectangle import RectangleType, Rectangle
from src.model.drawing_objects.scale import Scale
from src.model.drawing_objects.spot import Spot
from src.model.image_data import ImageData
from src.model.image_type import ImageType
from src.model.json_data import JsonData
from src.model.region_measurements import RegionMeasurement


class Model():
    def __init__(self):

        self.image_folder_path = None
        self.json_folder_path = None  # where json files are stored.

        self.rl_path = None
        self.tl_path = None
        self.binarise_rl_image = None
        self.binarise_tl_image = None

        self.Current_Image = None

        self.mask_path = None
        self.contours_by_group_tag = {}  # a list of all the polygon objects to turn into  binary masks
        self.deleted_contours = []  # in case of an undo
        #self.Current_Image = 'TL'  # tracks which image type is displayed
        self.width = 0  # used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.height = 0  # used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.breaklines = []
        self.saveLocation = 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/_o.png'  # where the 1st binarised image will output to
        self.case = ''  # the function of the browse button. I.e. browse for capture, RL or TL
        self.img = None
        self.currentSpotNumber = tk.StringVar()
        self.image_iterator_current = None
        self.spotPointCount = 0
        self.spots_in_measured_image = None
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
            polygon = shapely.geometry.Polygon(contour_coords)  # create a shapely polygon
            representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
            self.threshold = skimage.measure.label(self.threshold, background=0, connectivity=None).astype('uint8')
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

    def SaveBreakChanges(self,new_boundary = None):
        updatedMask = self.convert_contours_to_mask_image(self.height, self.width, self.contours_by_group_tag.values())

        # if the user has digitised a new grain boundary manually, draw it on the mask image
        if new_boundary != None:
            points = np.array(new_boundary.paired_coordinates(),'int32')
            updatedMask = cv2.fillPoly(updatedMask,[points], color=(255,255,255))

        #draw breaklines on the image to divide touching grains
        for breakline in self.breaklines:
            updatedMask = cv2.line(updatedMask, (int(breakline.x0), int(breakline.y0)), (int(breakline.x1),int(breakline.y1)), (0,0,0),2)
        self.breaklines = []

        #label each grain uniquely
        updatedMask[updatedMask > 0] = 255
        labelim = skimage.measure.label(updatedMask, background=0, connectivity=None)
        self.threshold = labelim.astype('uint8')

        image_to_display = self.Current_Image
        image_pill = Image.fromarray(image_to_display)
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

    def update_spot_in_json_file(self,spot):
        fileLocation = self.json_folder_path
        if self.mask_path:
            file_path = self.mask_path
        elif self.rl_path:
            file_path = self.rl_path
        elif self.tl_path:
            file_path = self.tl_path
        t_regionID = file_path.split('/')[-1].split('_')
        regionID = '_'.join(t_regionID[4:]).replace('.png', '')

        for path, folder, files in os.walk(fileLocation):
            for name in files:
                if name == self.json_file_name:  # find the json file that relates to the pdf page (image) under consideration
                    with open(os.path.join(fileLocation, self.json_file_name), errors='ignore') as jsonFile:
                        data = json.load(jsonFile)

                    region_top, region_left, _, _ = self.get_region_dimensions_from_json(data, regionID)
                    for region in data['regions']:
                        if region['id'] == spot.group_tag and region['type'] == 'POINT':
                            x = spot.x0 + region_left
                            y = spot.y0 + region_top
                            newPoints = [{"x": x, "y": y}]
                            region["points"] = newPoints

                    with open(os.path.join(fileLocation, self.json_file_name), 'w', errors='ignore') as updatedFile:
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

    def load_mask_from_file(self, mask_path):
        if mask_path == '':
            raise ValueError('No mask image has been selected')

        # the rl and tl variables must be set to none and repopulated from the file paths read from the json file
        #else old values will still be in memory if the json is not found
        self.rl_path = None
        self.tl_path = None
        self.rl_image = None
        self.tl_image = None

        self.threshold = cv2.imread(mask_path)[:, :, 0]
        self.threshold[self.threshold > 0] = 255

        jsonName = '_'.join(mask_path.split('/')[-1].split('_')[:3]) + '.json'
        sampleid = jsonName.split('_')[0]
        if len(mask_path.split('/')[-1].split('_')) > 2:
            regionID = mask_path.split('/')[-1].split('_')[-1].replace('.png', '')
        else:
            regionID = ""

        if self.json_folder_path is None:
            raise ValueError('No json folder path has been set')

        with open(os.path.join(self.json_folder_path, jsonName), errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        this_region = None
        for region in data["regions"]:
            if region["id"] == regionID:
                this_region = region
                break
        self.rl_path = this_region["RL_Path"] if "RL_Path" in this_region else ''
        self.tl_path = this_region["TL_Path"] if "TL_Path" in this_region else ''
        self.mask_path = this_region["Mask_Path"] if "Mask_Path" in region else ''
        self.set_current_image(ImageType.MASK)

    def get_threshold_image(self):
        threshold_image = Image.fromarray(self.threshold)
        return threshold_image

    def load_current_mask(self):
        self.threshold = cv2.imread(self.currentMask)[:, :, 0]

    def undo_delete_contour(self):
        if len(self.deleted_contours)==0:
            return None
        contour_to_restore = self.deleted_contours.pop(-1)
        self.contours_by_group_tag[contour_to_restore.group_tag] = contour_to_restore
        return contour_to_restore

    def check_for_images_and_jsons(self, image_folder_path, json_folder_path, data_capture_image_type):
        has_images = False
        missing_json_files = []
        for path, folders, files in os.walk(image_folder_path):
            for name in files:
                extension = os.path.splitext(name)[1]
                # check for images
                if extension.lower() == '.png' and self.is_file_name_of_image_type(name,data_capture_image_type):
                    has_images = True
                    json_file = os.path.splitext(name)[0] + '.json'
                    has_json = self.does_json_exist(os.path.join(json_folder_path, json_file))
                    if not has_json:
                        json_path = os.path.join(path,name)
                        missing_json_files.append(json_path)
        return has_images, missing_json_files

    def does_json_exist(self, json_file):
        return os.path.exists(json_file)

    def is_file_name_of_image_type(self, file_name:str, image_type):
        pattern = image_type.file_pattern()
        if image_type == ImageType.COLLAGE:
            return True
        return file_name.endswith("_" + pattern) or ("_" + pattern + "_") in file_name

    def create_new_json_file(self, data_capture_image_path, image_type):
        image = cv2.imread(data_capture_image_path)[:,:,0]
        image_width = image.shape[1]
        image_height = image.shape[0]

        data = JsonData(data_capture_image_path,image_type,image_width, image_height)
        # If we're creating a new json path then the data-capture image is not a collage
        # and therefore we add a single region to the json file that encompasses the whole image.
        data.add_first_image_region()
        data.save_all()

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
        if self.json_file_name == '':
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

    def set_mask_path(self, mask_path):
        self.mask_path = mask_path

    def write_mask_to_png(self, mask_file_path):
        self.threshold[self.threshold > 0] = 255
        cv2.imwrite(mask_file_path, self.threshold)

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

        image_data = JsonData.load_all(json_file_path)
        return image, image_data

    def preprocess_image_for_measurement(self, mask_file_path):
        if mask_file_path != '':
            self.threshold = cv2.imread(mask_file_path)[:, :, 0]
            self.width = self.threshold.shape[1]
            self.height = self.threshold.shape[0]
        image_remove = ZirconSeparationUtils.removeSmallObjects(self.threshold,15)  # remove small objects below a threshold size (max object size/15)
        image_clear = skimage.segmentation.clear_border(labels=image_remove, bgval=0,buffer_size=1)  # remove objects that touch the image boundary
        image_clear_uint8 = image_clear.astype('uint8')

        return image_clear_uint8

    def read_spots_unwanted_scale_from_json(self,json_data, json_file_path,regionID):
        spotList = []
        regions_to_remove_from_mask_image = []
        region_object = json_data.get_image_region(regionID)

        region_top = region_object.y0
        region_bottom = region_object.y1
        region_left = region_object.x0
        region_right = region_object.x1

        #This gets written to the output so that someone can regenerate the
        #contour image at a later point, if the original mask is lost
        region_dimension_string = f'{region_top},{region_left},{region_right},{region_bottom}'

        for spot in json_data.spots:
            # this will look for all spots in the pdf page, regardless of whether or not they are actually on the cropped image under consideration
            if spot.x0 >= region_left and spot.x0 <= region_right and spot.y0 >= region_top and spot.y0 <= region_bottom:
                # If the image is a crop from a larger image (e.g. A4 collage of photos)
                # and the spots were captured on the larger image
                # the display coordinages on the cropped image must be calculated
                spot.x0 -= region_left
                spot.y0 -= region_top
                spotList.append(spot)

        for unwanted_object in json_data.unwanted_objects:
            centroid_x, centroid_y = unwanted_object.get_centroid()
            if centroid_x >= region_left and centroid_x <= region_right and centroid_y >= region_top and centroid_y <= region_bottom:
                    unwanted_object.translate_coordinates(-region_left, -region_top)
                    regions_to_remove_from_mask_image.append(unwanted_object)

        if json_data.scale is not None:
            scale_in_real_world_distance = 100 / json_data.scale.get_length()
        elif len(json_data.spot_areas)>0:
            average_scale = ZirconSeparationUtils.getScale(json_file_path, 'SPOT')
            if average_scale is not None:
                scale_in_real_world_distance = 30 / average_scale
            else:
                raise ValueError('No scale available in sample')
        else:
            raise ValueError('No scale available in sample')

        return spotList,regions_to_remove_from_mask_image,scale_in_real_world_distance,region_dimension_string

    def get_region_dimensions_from_json(self, data, regionID):
        if regionID == "":  # if the photo  in question does not comprise subregions (i.e. not a photo collage)
            imageTop = 0  # find out the starting point (top left) of the photo under consideration
            imageLeft = 0
            imageWidth = data["asset"]["size"]["width"]
            imageHeight = data["asset"]["size"]['height']
            return imageTop, imageLeft, imageWidth, imageHeight

        for region in data['regions']:
            if region['id'] == regionID:  # if the photo in question is a subregion of the original image
                # find out the starting point (top left) of the photo under consideration
                imageTop = region['boundingBox']['top']
                imageLeft = region['boundingBox']['left']
                imageWidth = region['boundingBox']['width']
                imageHeight = region['boundingBox']['height']
                return imageTop, imageLeft, imageWidth, imageHeight

        return None

    def remove_unwanted_objects_from_binary_image(self,objects_to_remove):
        for unwanted_object in objects_to_remove:
            x,y = unwanted_object.get_centroid()
            label = self.threshold[int(x), int(y)]
            if label != 0:
                self.threshold[self.threshold == label] = 0

    def find_spots_in_region(self,label,spotList,contoursFinal):
        spots = []
        for contour in contoursFinal:
            polygon = shapely.geometry.Polygon(np.squeeze(contour))  # create a shapely polygon
            representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
            # get the region label at the representative point
            region_label = self.threshold[int(representative_point.y), int(representative_point.x)]
            if region_label == label:  # is this boundary around the region in question?
                boundary = matplotlib.path.Path(np.squeeze(contour), closed=True)
                for spot in spotList:
                    spotInside = boundary.contains_point([spot.x0, spot.y0])
                    if spotInside == True:
                        # a grain may have more than 1 spot associated with it. Find all spots associated with the grain
                        spots.append(spot)

                return spots,contour
        return spots,None

    def create_measurement_table(self,sampleid,regionID,imageDimensions,micPix, mask_file_path,all_spots):
        self.contours_by_group_tag = {}
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE,
                                                         cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE, cv2.RETR_EXTERNAL
        props = skimage.measure.regionprops(self.threshold,)

        measurements = []

        for x in range(0, len(props)):
            # Convex image is good enough because it'll give us the max points and min edges for maxFeret and minFeret
            maxFeret, minFeret = zircon_measurement_utils.feret_diameter(props[x].convex_image)
            spots_in_region,contour = self.find_spots_in_region(props[x].label,all_spots,contoursFinal)


            measurement = RegionMeasurement(
                    sampleid = sampleid,
                    image_id = regionID,
                    grain_number = props[x].label,
                    grain_centroid = props[x].centroid,
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
            if len(spots_in_region)==0:
                measurements.append(measurement)
            else:
                for spot in spots_in_region:
                    spot_measurement = measurement.copy()
                    spot_measurement.grainspot = spot.group_tag
                    measurements.append(spot_measurement)

        return measurements

    def create_labeled_image(self,region_measurements):
        image_to_display = self.Current_Image.copy()

        # cv2.imwrite('C:/Users/20023951/Documents/PhD/Reporting/Paper1_ZirconSeparationUtility/CaseStudy/CaseStudy_MaduraShelf/mask_img.jpg', img_to_display)
        for measurement in region_measurements:
            # img_to_display = cv2.circle(img_to_display, (int(centroid_List[i][1]), int(centroid_List[i][0])), 3, (0, 0, 255), 2)
            grain_centroid = measurement.grain_centroid
            cv2.putText(image_to_display, str(measurement.grain_number),
                        (int(grain_centroid[1] - 2), int(grain_centroid[0] - 2)), cv2.FONT_HERSHEY_DUPLEX, 0.3,
                        (0, 0, 255))

        return image_to_display

    def measure_shapes(self, mask_path, processFolderFlag):
        if self.json_folder_path is None:
            raise ValueError('No json folder path selected')

        json_file_path,region_id,sample_id = self.get_json_path_and_region_id_and_sample_id_for_measurement(mask_path)
        data = JsonData.load_all(json_file_path)

        self.spots_in_measured_image = None
        self.contours_by_group_tag={}

        self.preprocess_image_for_measurement(mask_path)

        spotList, regions_to_remove_from_mask_image, scale_in_real_world_units, imageDimensions = self.read_spots_unwanted_scale_from_json(data,json_file_path,region_id)
        self.spots_in_measured_image = spotList
        self.remove_unwanted_objects_from_binary_image(regions_to_remove_from_mask_image)

        region_measurements = self.create_measurement_table(sample_id,region_id,imageDimensions,scale_in_real_world_units,mask_path,spotList)

        labeled_image = self.create_labeled_image(region_measurements)

        image_to_display = Image.fromarray(labeled_image)
        contours = self.extract_contours_from_image("extcont")

        return image_to_display, contours, spotList,region_measurements

    def binariseImages(self):
        self.breaklines == []
        self.contours_by_group_tag = {}
        self.deleted_contours = []

        if self.binarise_rl_image == 1:
            self.rl_image = cv2.imread(self.rl_path)
            if self.rl_image is None:
                raise ValueError('No reflected light image selected')
            self.Current_Image = self.rl_image

            grayRL = cv2.cvtColor(self.rl_image, cv2.COLOR_BGR2GRAY)
            smoothImgRL1 = cv2.bilateralFilter(grayRL, 75, 15, 75)
            smoothImgRL2 = cv2.bilateralFilter(smoothImgRL1, 75, 15, 75)
            otsuImgRL = cv2.threshold(smoothImgRL2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            fillRL = ndimage.binary_fill_holes(otsuImgRL).astype(int)
            fillRL_uint8 = fillRL.astype('uint8')
            fillRL_uint8[fillRL_uint8 > 0] = 255

        if self.binarise_tl_image == 1:
            self.tl_image = cv2.imread(self.tl_path)
            if self.tl_image is None:
                raise ValueError('No transmitted light image selected')
            self.Current_Image = self.tl_image

            grayTL = cv2.cvtColor(self.tl_image, cv2.COLOR_BGR2GRAY)
            smoothImgTL1 = cv2.bilateralFilter(grayTL, 75, 15, 75)
            smoothImgTL2 = cv2.bilateralFilter(smoothImgTL1, 75, 15, 75)
            otsuImgTL = cv2.threshold(smoothImgTL2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            otsuInvTL = cv2.bitwise_not(otsuImgTL)
            otsuInvTL_uint8 = otsuInvTL.astype('uint8')
            otsuInvTL_uint8[otsuInvTL_uint8 > 0] = 255

        if self.binarise_rl_image == 0 and self.binarise_tl_image == 0:
            raise ValueError('Select image to binarise')

        elif self.binarise_rl_image == 1 and self.binarise_tl_image == 1:
            self.threshold = cv2.add(otsuInvTL_uint8, fillRL_uint8)

        elif self.binarise_rl_image ==1 and self.binarise_tl_image ==0:
            self.threshold = fillRL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image

        elif self.binarise_tl_image ==1  and self.binarise_rl_image ==0:
            self.threshold = otsuInvTL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image

        # Once the image is binarised, get the contours
        self.erode_small_artifacts(self.threshold)
        self.width = self.threshold.shape[1]
        self.height = self.threshold.shape[0]
        image_pill = Image.fromarray(self.tl_image if self.binarise_tl_image else self.rl_image)

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
        self.set_json_folder_path(json_folder_path)

    def set_json_folder_path(self,json_folder_path):
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
        return list(self.contours_by_group_tag.values())

    def separate(self):
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

        if self.tl_path != '':
            image_to_show = self.tl_image
            is_image_binary = False
        elif self.rl_path:
            image_to_show = self.rl_image
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

    def set_rl_tl_paths_and_usage(self,rl_path, tl_path,binarise_rl_image, binarise_tl_image):
        self.rl_path = rl_path
        self.tl_path = tl_path
        self.binarise_rl_image = binarise_rl_image
        self.binarise_tl_image = binarise_tl_image

    def set_current_image(self,image_type):
        if image_type == ImageType.TL:
            self.Current_Image = self.tl_image
        elif image_type == ImageType.RL:
            self.Current_Image = self.rl_image
        elif image_type == ImageType.MASK:
            image = self.threshold.copy()
            image[image > 0] = 255
            self.Current_Image = np.stack((image,) * 3, axis=-1)
        else:
            raise Exception('Unknown image type '+str(image_type))
        return  Image.fromarray(self.Current_Image)

    def find_spot_in_measured_image_by_unique_tag(self, unique_tag):
        for spot in self.spots_in_measured_image:
            if spot.unique_tag == unique_tag:
                return spot
        return None

    def get_json_path_and_region_id_and_sample_id_for_measurement(self, mask_path):
        if mask_path != '':
            image_type = ImageType.MASK
            path = mask_path
        elif self.rl_path:
            image_type = ImageType.RL
            path = self.rl_path
        elif self.tl_path:
            image_type = ImageType.TL
            path= self.tl_path
        else:
            raise ValueError('No binarisation images found')

        json_file_name = JsonData.get_json_file_name_from_path(image_type, path)
        region_id = JsonData.get_region_id_from_file_path(image_type,path)
        json_file_path = os.path.join(self.json_folder_path,json_file_name)

        sample_id = JsonData.get_sample_id_from_file_path(path)

        return json_file_path, region_id,sample_id