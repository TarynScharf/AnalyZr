def EditPolygon(self):
    self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
    self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
    self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
    self.myCanvas.bind("<Button-1>", self.SelectPolygon)


def SelectPolygon(self, selectEvent):
    thisObj = selectEvent.widget.find_withtag('current')[0]
    uniqueTag = self.myCanvas.gettags(thisObj)[1]

    if 'poly' in uniqueTag:
        self.uniqueTag = uniqueTag
        self.groupTag = self.myCanvas.gettags(thisObj)[0]
        self.myCanvas.bind("<Button-1>", self.InsertPoint)
    elif 'contour_' or 'extcont_' in uniqueTag:
        self.uniqueTag = uniqueTag
        self.groupTag = self.myCanvas.gettags(thisObj)[0]
        contour_coords = self.myCanvas.coords(self.uniqueTag)
        coordList = []
        for x in range(0, len(contour_coords), 2):
            x0 = contour_coords[x] - 3
            y0 = contour_coords[x + 1] - 3
            x1 = x0 + 3
            y1 = y0 + 3
            coordID = 'p' + str(datetime.datetime.now())
            coordList.append([coordID, contour_coords[x], contour_coords[x + 1]])
            self.myCanvas.create_oval(x0, y0, x1, y1, fill='white', activefill='yellow', activeoutline='yellow', outline='grey', width=2, tags=(self.groupTag, coordID))
        self.all_contours[self.groupTag] = coordList
        self.RepositionObject()
    else:
        error_message_text = 'Select a polygon to edit'
        self.view.open_error_message_popup_window(error_message_text)


def InsertPoint(self):
    self.myCanvas.unbind("<Button-1>")
    self.myCanvas.bind("<Button-1>", self.StartInsertPoint)


def StartInsertPoint(self, addEvent):
    if self.uniqueTag == None:
        error_message_text = 'Select a polygon to edit'
        self.view.open_error_message_popup_window(error_message_text)
        return
    delta_x = None  # used to calculate displacement
    delta_y = None  # used to calculate displacement
    tot_diff = None  # used to calculate displacement
    insertIncr = None  # where to insert the new point coordinates in the self.allPolys[thispoly] list
    diffList = []  # used to hold the displacement of the new point relative to all existing points, so that the closest  point can be determined
    coords = []  # used to hold the coordinates of the final polygon, for drawing purposes

    self.x0 = self.myCanvas.canvasx(addEvent.x)
    self.y0 = self.myCanvas.canvasy(addEvent.y)

    # Find the nearest point in the polygon array:
    for point in self.all_contours[self.uniqueTag]:
        delta_x = abs(self.x0 - point[1])
        delta_y = abs(self.y0 - point[2])
        tot_diff = delta_x + delta_y
        diffList.append(tot_diff)
    min_diff = min(diffList)  # find the closest point in the polygon
    incr = diffList.index(min_diff)  # find the position of this closest point in the polyon array

    # find out if the new point lies left or right of this closest point, so we know where to insert the new point in the polygon coordinate array
    # There is an assumption that the polygon is always digitised anticlockwise. This isn't great.
    closestX = self.all_contours[self.uniqueTag][incr][1]
    closestY = self.all_contours[self.uniqueTag][incr][2]
    try:
        nextX = self.all_contours[self.uniqueTag][incr + 1][1]
        nextY = self.all_contours[self.uniqueTag][incr + 1][2]
    except:
        # if incr+1 goes beyond the list length, then look at the first point in the list
        nextX = self.all_contours[self.uniqueTag][0][1]
        nextY = self.all_contours[self.uniqueTag][0][2]

    firstRight = None  # bool -  is the new point right of the closest existing point
    secondRight = None  # bool - is the new point right of the next(in direction of incrementor) point

    # Find positioning of new point in the polygon array
    if self.x0 > closestX:  # x increases to the right, so increase incrementor
        firstRight = True
        if self.x0 > nextX:
            secondRight = True
        elif self.x0 < nextX:
            secondRight = False
        else:
            # self.x0 == nextX
            insertIncr = incr + 1
    elif self.x0 < closestX:
        firstRight = False
        if self.x0 > nextX:
            secondRight = True
        elif self.x0 < nextY:
            secondRight = False
        else:
            insertIncr = incr + 1
    elif self.x0 == closestX:
        # print('I')
        if self.y0 == closestY:
            return  # duplicate point, do nothing
        else:
            # print('J')
            insertIncr = incr + 1

    if insertIncr == None:
        if firstRight == True and secondRight == True:
            insertIncr = incr
        elif firstRight == False and secondRight == False:
            insertIncr = incr
        elif firstRight == True and secondRight == False:
            insertIncr = incr + 1
        elif firstRight == False and secondRight == True:
            insertIncr = incr + 1
    p = 'pt' + str(datetime.datetime.now())
    self.myCanvas.delete(self.uniqueTag)  # delete pre-existing poly
    self.myCanvas.create_oval(self.x0 - 3, self.y0 - 3, self.x0 + 3, self.y0 + 3, fill='white', activefill='yellow',
                              activeoutline='yellow', outline='grey',
                              width=2, tags=(self.groupTag, p))  # draw the newly inserted point
    # redraw the new polygon
    self.all_contours[self.uniqueTag].insert(insertIncr, [p, self.x0, self.y0])
    for points in self.all_contours[self.uniqueTag]:
        coords.append([points[1], points[2]])
    self.myCanvas.create_polygon(coords, fill='', outline='red', width=1, tags=(self.groupTag, self.uniqueTag))
    # self.SavePolygon()

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


"""
if region['tags'][0] == 'RL' and region['type'] == 'POLYGON':
    polyCoords = []  # used locally to draw the polygon
    self.spotCount += 1
    self.allPolys = {}  # used globally to track all polygons and associated points on the page. Set to empty each time a new page is loaded.
    groupID = 'boundary' + str(datetime.datetime.now())  # group polygon and points
    uniqueID = region['id']  # unique identifies polygon
    idCoordList = []  # gathers point ID, x and y for each point, to be saved to global dictionary
    for point in region['points']:
        x0 = point['x']
        y0 = point['y']
        xy = [x0, y0]
        coordID = 'p' + str(datetime.datetime.now())  # uniquely identifies point
        polyCoords.append(xy)
        idCoordList.append([coordID, x0, y0])
        # self.myCanvas.create_oval(x0-4, y0-4, x0+4, y0+4, fill='white',activefill = 'yellow', activeoutline='yellow', outline='grey', width=2,tags = (groupID, coordID))
"""


def UpdatePointMove(self, moveEvent):
    if self.Move == False:
        return

    self.x0 = self.myCanvas.canvasx(moveEvent.x)
    self.y0 = self.myCanvas.canvasy(moveEvent.y)

    # delete the pre-existing point then redraw in the new position
    self.myCanvas.delete(self.unique_tag)
    self.myCanvas.create_oval(self.x0 - 6, self.y0 - 6, self.x0 + 6, self.y0 + 6, fill='lightgreen',
                              activefill='yellow', activeoutline='yellow', outline='green',
                              width=2, tags=(self.groupID, self.unique_tag))

    xyList = []  # used locally to draw the  polygon with  updated xy
    # get all items with the same group tag. This will include all ovals and the polygon
    all_IDs = self.myCanvas.find_withtag(self.groupID)
    for ID in all_IDs:
        uniqueID = self.myCanvas.gettags(ID)[1]  # get the unique ID of each entity that shares the group ID
        if "poly" in uniqueID or 'contour_' in uniqueID:  # test whether it's a polygon
            # find the point that was clicked on and update it's xy coords
            for i in range(len(self.allPolys[uniqueID])):
                if self.allPolys[uniqueID][i][0] == self.unique_tag:
                    self.allPolys[uniqueID][i][1] = self.x0
                    self.allPolys[uniqueID][i][2] = self.y0
            for point in self.allPolys[uniqueID]:
                xyList.append(point[1])
                xyList.append(point[2])
            groupID = self.myCanvas.gettags(uniqueID)[0]  # find the group tag
            if len(self.allPolys[uniqueID]) > 2:
                self.myCanvas.delete(uniqueID)  # delete pre-existing poly and redraw with new coordinates
                self.myCanvas.create_polygon(xyList, fill='', outline='red', activeoutline='yellow', width=1,
                                             tags=(groupID, uniqueID))
            elif len(self.allPolys[uniqueID]) == 2:
                self.myCanvas.create_line(xyList, fill='red', activeoutline='yellow', tags=(groupID, uniqueID))
            else:
                pass
        if 'spotno' in uniqueID:  # if its a label on a spot
            self.myCanvas.delete(uniqueID)
            self.myCanvas.create_text(self.x0 - 10, self.y0 - 10, fill='green', text=self.spotID, tags=(self.groupID, uniqueID))
            self.spotID = uniqueID.split('_')[1]
