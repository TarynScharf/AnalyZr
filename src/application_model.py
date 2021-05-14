import tkinter as tk
class Model():
    def __init__(self):
        self.json_folder_path = tk.StringVar()
        self.json_folder_location = None  # where json files are stored.
        self.maskPath = ''
        self.contourList = {}  # a list of all the polygon objects to turn into  binary masks
        self.last_contour_deleted = {}  # this dictionary will hold the last contour deleted, incase of an undo
        self.Current_Image = 'TL'  # tracks which image type is displayed
        self.width = 0  # used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.height = 0  # used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.pairsList = []
        self.saveLocation = 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/_o.png'  # where the 1st binarised image will output to
        self.case = ''  # the function of the browse button. I.e. browse for capture, RL or TL
        self.folderPath = ''
        self.img = None
        self.currentSpotNumber = tk.StringVar()
        self.image_iterator_current = None
        self.spotPointCount = 0

        self.text_label = ''  # label for duplicate grains and spot scales
        self.new_boundary = None  # when a polygon is manually draw, it is saved to this variable.
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
        self.allPolys = {}  # ID-coordinate dictionary of all polygons on the page


        self.threshold = None
        self.spotID = ''  # used when repositioning spots
        self.ProcessFolderFlag = False  # flag that tracks whether an entire folder of masks is to be processed
        self.currentMask = None  # if processing an entire mask folder, keep track of the current mask's file path

    def DeleteObject(self, thisObjID,coords):
        if thisObjID == "Image":  # make sure you haven't selected the image
            return

        if 'line_' in thisObjID: #breaklines don't get written to a json file
            x1 = coords[0]
            y1 = coords[1]
            x2 = coords[2]
            y2 = coords[3]
            self.pairsList.remove([(x1,y1),(x2,y2)])

        elif 'contour_' in thisObjID:
            self.last_contour_deleted.clear()  # only keeps the last contour deleted
            self.last_contour_deleted[thisObjID] = self.contourList[thisObjID]  # store the last contour to be deleted
            del self.contourList[thisObjID]

        elif 'extcont_' in thisObjID:
            contour_coords = self.contourList[thisObjID].paired_coordinates()
            polygon = Polygon(contour_coords)  # create a shapely polygon
            representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
            self.threshold = label(self.threshold, background=0, connectivity=None).astype('uint8')
            blob_label = self.threshold[int(representative_point.y),int(representative_point.x)]
            if int(blob_label)!=0:
                self.threshold[self.threshold==blob_label]=0
            self.last_contour_deleted.clear() #only keeps the last contour deleted
            self.last_contour_deleted[thisObjID] = self.contourList[thisObjID] #store the last contour to be deleted
            del self.contourList[thisObjID]

        else:
            with open(os.path.join(self.folderPath, self.image_iterator_current[0]),errors='ignore') as jsonFile:  # open the json file for the image
                data = json.load(jsonFile)
            for i in range(0, len(data['regions'])):  # If the object already exists in the json
                if data['regions'][i]['id'] == thisObjID:
                    data['regions'].pop(i)  # get rid of it. Don't read further (affects incrementor?)
                    break
            with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)  # rewrite the json without the object
            try:
                self.unique_sample_numbers[self.currentSample].discard(thisObjID)
            except:
                pass

    def SavePolygon(self):
        x_list = []
        y_list = []
        polyCoords = []

        for point in self.allPolys[self.uniqueTag]:
            x_list.append(point[1])  # get a list of all the x-coords. This makes it easy to  get min and max x
            y_list.append(point[2])  # get a list of all the y-coords.This makes it easy to get min and max y
            polyCoords.append({"x": point[1], "y": point[2]})  # get a list of each coord pair. This makes it easy to write the poly to the json file
        # Get the new bounding box for the polygon
        top = min(y_list)  # y increases downwards
        left = min(x_list)  # x increases to the right
        height = abs(max(y_list) - min(y_list))
        width = abs(max(x_list) - min(x_list))
        boundingBox = {"height": height, "width": width, "left": left, "top": top}

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
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

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)
        self.uniqueTag = None
        self.groupTag = None

    def add_polygon_vertex(self, x0,y0,uniqueTag, groupTag):
        xy = [x0, y0]
        coordID = 'p' + str(datetime.datetime.now())  # each point gets its own unique id
        if uniqueTag not in self.allPolys:
            polygon = ContourPolygon(groupTag,uniqueTag)
            self.allPolys[uniqueTag] = polygon
        else:
            polygon = self.allPolys[uniqueTag]

        polygon.add_vertex(x0,y0,coordID)
        polygon.groupTag = groupTag
        polygon.uniqueTag = uniqueTag

        self.view.update_polygon(polygon)

    def complete_polygon(self, uniqueTag):
        polygon = self.allPolys[uniqueTag]
        self.new_boundary = polygon.paired_coordinates()
        self.SaveBreakChanges()

    def SaveBreakChanges(self):
        updatedMask = self.convert_contours_to_mask_image(self.height, self.width, self.contourList)

        if self.new_boundary != None: # if the user has digitised a new grain boundary manually
            points = np.array(self.new_boundary,'int32')
            updatedMask = cv2.fillPoly(updatedMask,[points], color=(255,255,255))
            self.new_boundary = None

        if self.pairsList != []:
            pairs = self.pairsList
            for p in pairs:
                x1 = p[0][0]
                y1 = p[0][1]
                x2 = p[1][0]
                y2 = p[1][1]
                updatedMask = cv2.line(updatedMask, (int(x1), int(y1)), (int(x2),int(y2)), (0,0,0),2)
            self.pairsList = []

        self.threshold = updatedMask

        updatedMask[updatedMask > 0] = 255
        labelim = label(updatedMask, background=0, connectivity=None)
        self.threshold = labelim.astype('uint8')

        if self.TLPath.get() != '' and self.Current_Image=='TL':
            original_Image = cv2.imread(self.TLPath.get())

        elif self.RLPath.get() != '' and self.Current_Image=='RL':
            original_Image = cv2.imread(self.RLPath.get())

        image_pill = Image.fromarray(original_Image)
        self.img = ImageTk.PhotoImage(image=image_pill)
        self.view.display_image(self.img)
        self.extract_contours_from_image('extcont')


    def extract_contours_from_image(self,prefix,filter_fn = None):
        # paint the contours on
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        count_contour = 0
        self.contourList.clear()
        for i in range(len(contoursFinal)):
            if len(contoursFinal[i]) < 3:
                continue

            if filter_fn is not None and not filter_fn(contoursFinal[i]):
                continue

            coordinate_pairs = np.squeeze(contoursFinal[i])
            groupID = prefix+"_" + str(count_contour)
            uniqueID = prefix+"_" + str(count_contour)
            polygon = ContourPolygon(groupID, uniqueID, coordinate_pairs)
            self.contourList[uniqueID] = polygon
            self.view.draw_polygon(polygon)
            count_contour += 1


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

    def save_rectangle_to_json(self,rectStart_x, rectStart_y, updatedX, updatedY, rectangleType, uniqueTag):

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        height = abs(rectStart_y - updatedY)
        width = abs(rectStart_x - updatedX)

        if rectStart_x < updatedX:  # x increases left to right
            left = rectStart_x
            right = updatedX
        else:
            left = updatedX
            right = rectStart_x

        if rectStart_y < updatedY:  # y increases top to bottom
            top = rectStart_y
            bottom = updatedY
        else:
            top = updatedY
            bottom = rectStart_y


        newRegion = {"id": uniqueTag, "type": "RECTANGLE", "tags": [rectangleType],
                     "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                     "points": [{"x": left, "y": top}, {"x": right, "y": top}, {"x": right, "y": bottom},
                                {"x": left, "y": bottom}]}
        data['regions'].append(newRegion)

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)


    def save_scale_to_json(self,uniqueTag,lineStart_x, lineStart_y, updatedX, updatedY):
        height = abs(lineStart_y - updatedY)
        width = abs(lineStart_x - updatedX)

        if lineStart_x < updatedX:  # x increases left to right
            left = lineStart_x
        else:
            left = updatedX

        if lineStart_y < updatedY:  # y increases top to bottom
            top = lineStart_y
        else:
            top = updatedY

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)
            newRegion = {"id": self.uniqueTag, "type": "SCALE", "tags": ["SCALE"],
                         "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                         "points": [{"x": lineStart_x, "y": lineStart_y},
                                    {"x":updatedX, "y":updatedY}]}
            data['regions'].append(newRegion)

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)


    def save_spot_to_json(self,thisSpotID,userText,x0,y0):
        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)
            anyMatch = False
            for region in data['regions']:  # If the spot already exists in the jSON
                if region['id'] == thisSpotID:
                    region['id'] = userText
                    anyMatch = True

            #if anyMatch == False and Type == "POINT":  # if it's newly digitised and does not yet exist in the json file, and it's a point
            if anyMatch == False:
                newRegion = {"id": userText, "type": "POINT", "tags": ["SPOT"],
                             "boundingBox": {"height": 5, "width": 5, "left": x0, "top": y0},
                             "points": [{"x": x0, "y": y0}]}
                data['regions'].append(newRegion)

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

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)

    def insert_new_breakline_to_pairslist(self, lineStart_x, lineStart_y, updatedX, updatedY):
        self.pairsList.append([(lineStart_x, lineStart_y), (updatedX, updatedY)])

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

        if self.json_folder_location is None:
            return None

        with open(os.path.join(self.json_folder_location, jsonName), errors='ignore') as jsonFile:
            data = json.load(jsonFile)

        # if regionID in data["regions"]:
        for region in data["regions"]:
            if region["id"] == regionID:
                return region

    def load_current_mask(self):
        self.threshold = cv2.imread(self.currentMask)[:, :, 0]

    def undo_delete_contour(self):
        dict_key = list(self.last_contour_deleted.keys())[0]
        self.contourList[dict_key] = self.last_contour_deleted[dict_key]
        self.last_contour_deleted.clear()
        if self.Current_Image== 'TL':
            self.Load_Image(1)
        elif self.Current_Image == 'RL':
            self.Load_Image(0)

    def check_for_images_and_jsons(self,folderPath):
        has_images = False
        missing_json_files = []
        for path, folders, files in os.walk(folderPath):
            for name in files:
                if os.path.splitext(name)[1] == '.png':  # check for images
                    has_images = True
                    json_file = os.path.splitext(name)[0] + '.json'
                    has_json = self.does_json_exist(os.path.join(folderPath, json_file))
                    if not has_json:
                        missing_json_files.append(name)
        return has_images, missing_json_files

    def does_json_exist(self, json_file):
        return os.path.exists(json_file)


    def write_json_file(self,file):
        file_extension = os.path.splitext(file)[-1]
        path  = os.path.join(self.image_folder_path.get(),file)
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

        with open(os.path.join(self.image_folder_path.get(),json_name), 'w', errors='ignore') as new_json:
            json.dump(data, new_json, indent=4)

    def read_sampleID_and_spots_from_json(self,folderPath):
        # Get a list of unique sample ID's and the spots associated with them.
        for path, folders, files in os.walk(folderPath):
            for name in files:
                if os.path.splitext(name)[1] == '.json':
                    with open(os.path.join(folderPath, name), errors='ignore') as jsonFile:
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
        if self.json_folder_location is None or self.json_folder_location == '':
            self.error_message_text = 'JSON file location has not been set'
            self.open_error_message_popup_window()
            return
        else:
            with open(os.path.join(self.json_folder_location, jsonName), errors='ignore') as jsonFile:
                data = json.load(jsonFile)
            for region in data['regions']:
                if region['id'] == regionID:
                    region["RL_Path"] = fileRL
                    region["TL_Path"] = fileTL
                    region["Mask_Path"] = maskPath

            with open(os.path.join(self.json_folder_location, jsonName), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)

        cv2.imwrite(maskPath, self.threshold)

    def get_region_and_sample_id(self, mask_file_path):
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
        image_remove = removeSmallObjects(self.threshold,15)  # remove small objects below a threshold size (max object size/15)
        image_clear = clear_border(labels=image_remove, bgval=0,buffer_size=1)  # remove objects that touch the image boundary
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
                            micPix = 30 / getScale(name, path, 'SPOT')
                            # print('micron per pixel: ', micPix)
                        if region['type'] == 'RECTANGLE' and region['tags'][0] == 'DUPLICATE':
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
                        scale = getScale(name, path, 'SPOT')
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
            polygon = Polygon(np.squeeze(contour))  # create a shapely polygon
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
        self.contourList = {}
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE,
                                                         cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE, cv2.RETR_EXTERNAL
        props = regionprops(self.threshold)

        measurements = []

        for x in range(0, len(props)):
            # Convex image is good enough because it'll give us the max points and min edges for maxFeret and minFeret
            maxFeret, minFeret = feret_diameter(props[x].convex_image)
            spot_list,contour = find_spots_in_region(props[x].label)
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
                    formFactor = (4 * math.pi * area) / (perimeter ** 2),
                    roundness = (4 * area) / (math.pi * (major_axis_length ** 2)),
                    compactness = (math.sqrt((4 / math.pi) * area) / major_axis_length),
                    aspectRatio = major_axis_length / minor_axis_length,
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

    def MeasureShapes(self, mask_file_path,TLPath, RLPath):
        self.jsonName = ''
        sampleid,regionID,self.jsonName = self.get_region_and_sample_id(mask_file_path)
        self.preprocess_image_for_measurement(mask_file_path)

        json_file_path = self.json_folder_path.get()  # 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/t2_inv1_files'
        self.contourList={}

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

        #self.display_measurement_table(region_measurements)

    def display_measurement_table(self,region_measurements):

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
        print(self.dfShapeRounded)

    def binariseImages(self,RLPath, TLPath,rlVar,tlVar):
        self.pairsList == []
        self.contourList = {}
        fileRL = self.RLPath.get()
        fileTL = self.TLPath.get()
        if fileRL != '' and self.rlVar.get() == 1:
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

        if fileTL != '' and self.tlVar.get() == 1:
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

        if fileRL != '' and fileTL != '' and self.rlVar.get() == 1 and self.tlVar.get() == 1:
            # Add the images together:
            self.Current_Image = 'TL'
            self.threshold = cv2.add(otsuInvTL_uint8, fillRL_uint8)
            imCopy = cv2.imread(fileTL)  # import image as RGB for plotting contours in colour
        elif fileRL != '' and self.rlVar.get() ==1 and self.tlVar.get() ==0:
            self.Current_Image = 'RL'
            self.threshold = fillRL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image
            imCopy = cv2.imread(fileRL)  # import image as RGB for plotting contours in colour
        elif fileTL != '' and self.tlVar.get() ==1  and self.rlVar.get() ==0:
            self.Current_Image = 'TL'
            self.threshold = otsuInvTL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image
            imCopy = cv2.imread(fileTL)
        elif fileTL != '' and fileRL != '' and self.tlVar.get() ==1  and self.rlVar.get() ==0:
            self.Current_Image = 'TL'
            self.threshold = otsuInvTL_uint8  # in some cases the tl and rl images are warped and can't fit ontop of  each other. I use the RL because of the spots captured on the RL image
            imCopy = cv2.imread(fileTL)

        # Once the image is binarised, get the contours
        self.erode_small_artifacts(self.threshold)
        image_pill = Image.fromarray(imCopy)
        self.drawing.display_image(image_pill)

        def filter_polygon_by_area(contour):
            area = cv2.contourArea(contour, False)
            return area>=50

        self.extract_contours_from_image('contour',filter_polygon_by_area)

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



