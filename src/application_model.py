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
        updatedMask = self.convert_contours_to_mask_image()

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
