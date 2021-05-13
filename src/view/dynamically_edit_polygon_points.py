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
        self.allPolys[self.groupTag] = coordList
        self.PointMove()
    else:
        self.error_message_text = 'Select a polygon to edit'
        self.open_error_message_popup_window()


def InsertPoint(self):
    self.myCanvas.unbind("<Button-1>")
    self.myCanvas.bind("<Button-1>", self.StartInsertPoint)


def StartInsertPoint(self, addEvent):
    if self.uniqueTag == None:
        self.error_message_text = 'Select a polygon to edit'
        self.open_error_message_popup_window()
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
    for point in self.allPolys[self.uniqueTag]:
        delta_x = abs(self.x0 - point[1])
        delta_y = abs(self.y0 - point[2])
        tot_diff = delta_x + delta_y
        diffList.append(tot_diff)
    min_diff = min(diffList)  # find the closest point in the polygon
    incr = diffList.index(min_diff)  # find the position of this closest point in the polyon array

    # find out if the new point lies left or right of this closest point, so we know where to insert the new point in the polygon coordinate array
    # There is an assumption that the polygon is always digitised anticlockwise. This isn't great.
    closestX = self.allPolys[self.uniqueTag][incr][1]
    closestY = self.allPolys[self.uniqueTag][incr][2]
    try:
        nextX = self.allPolys[self.uniqueTag][incr + 1][1]
        nextY = self.allPolys[self.uniqueTag][incr + 1][2]
    except:
        # if incr+1 goes beyond the list length, then look at the first point in the list
        nextX = self.allPolys[self.uniqueTag][0][1]
        nextY = self.allPolys[self.uniqueTag][0][2]

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
    self.allPolys[self.uniqueTag].insert(insertIncr, [p, self.x0, self.y0])
    for points in self.allPolys[self.uniqueTag]:
        coords.append([points[1], points[2]])
    self.myCanvas.create_polygon(coords, fill='', outline='red', width=1, tags=(self.groupTag, self.uniqueTag))
    # self.SavePolygon()

