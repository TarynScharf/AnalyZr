import datetime
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

import matplotlib
import skimage
from skimage import segmentation
from skimage.segmentation import expand_labels
from PIL import ImageTk, Image
from matplotlib.backends.backend_agg import FigureCanvasAgg

from src.model.composite_contour import CompositeContour

matplotlib.use('Agg')
from src.model.measure_shape import *
from src.model.ZirconSeparationUtils import *


class Application:

    def __init__(self, master):
        self.master = master
        master.title("Zircon Shape Analysis")
        master.geometry('1600x3000')

        self.mainMenu = Menu(self.master)
        self.fileMenu = Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label="File", menu=self.fileMenu)

        self.imagesMenu = Menu(self.mainMenu, tearoff=0)
        self.imagesMenu.add_command(label="Load Images for Spot Capture", command=lambda: self.load_files_for_spot_capture())
        self.imagesMenu.add_command(label="Capture Analytical Spot [s]", command=self.PointDraw)
        self.imagesMenu.add_command(label="Capture Analytical Spot Size [a]", command=self.RectSpotDraw)
        self.imagesMenu.add_command(label="Mark Object for Deletion [d]", command=self.DupDraw)
        self.imagesMenu.add_command(label="Capture Scale [l]", command=self.DrawScale)
        self.imagesMenu.add_command(label="Move to Next Image [->]", command=self.NextImage)
        self.imagesMenu.add_command(label="Move to Previous Image [<-]", command=self.PrevImage)
        self.imagesMenu.insert_separator(1)
        self.imagesMenu.insert_separator(6)
        self.mainMenu.add_cascade(label="Data Capture", menu=self.imagesMenu)
        master.config(menu=self.mainMenu)

        self.binariseMenu = Menu(self.mainMenu, tearoff=0)
        self.binariseMenu.add_command(label="Load json Files", command=lambda: self.Browse('json'))
        self.binariseMenu.add_command(label="Image Segmentation Toolbox", command=self.browseImages)
        #self.binariseMenu.add_command(label="Grain Boundary Capture [p]", command=self.BoundaryDraw)
        #self.binariseMenu.add_command(label="Polygon Insert Point [i]", command=self.EditPolygon)
        #self.binariseMenu.add_command(label="Polygon Insert Point [m]", command=self.PointMove)
        self.binariseMenu.insert_separator(1)
        self.mainMenu.add_cascade(label="Segment Images", menu=self.binariseMenu)
        master.config(menu=self.mainMenu)

        # Two Frames. myFrame for the canvas, myMenuFrame for the buttons
        self.myMenuFrame = tk.Frame(master, width=1600, height=30)
        self.myMenuFrame.pack(fill='both')
        self.myFrame = tk.Frame(master, width=1600, height=3000)
        self.myFrame.pack(expand=True, fill='both')

        # Buttons
        #self.browseButton = Button(self.myMenuFrame, text="Load Images", command=lambda: self.Browse('capture'))
        #self.browseButton.grid(column=0, row=0, padx=5, pady=10)

        #self.nextImageButton = Button(self.myMenuFrame, text="Next Image", command=self.NextImage)
        #self.nextImageButton.grid(column=1, row=0, padx=5, pady=10)

        #self.prevImageButton = Button(self.myMenuFrame, text="Previous Image", command=self.PrevImage)
        #self.prevImageButton.grid(column=2, row=0, padx=5, pady=10)

        #self.spotCaptureButton = Button(self.myMenuFrame, text="Spot Capture", command=self.PointDraw)
        #self.spotCaptureButton.grid(column=3, row=0, padx=5, pady=10)

        #self.sizeCaptureButton = Button(self.myMenuFrame, text="Size Capture", command=self.RectSpotDraw)
        #self.sizeCaptureButton.grid(column=4, row=0, padx=5, pady=10)

        #self.duplicateCaptureButton = Button(self.myMenuFrame, text="Mark Duplicate", command=self.DupDraw)
        #self.duplicateCaptureButton.grid(column=5, row=0, padx=5, pady=10)

        # Image name, so  we know which image we're working on
        self.label = Label(self.myMenuFrame, text='')
        self.label.grid(column=1, row=0, padx=5, pady=10)

        self.myCanvas = Canvas(self.myFrame, bg="white")
        self.vScroll = Scrollbar(self.myFrame, orient='vertical', command=self.myCanvas.yview)
        self.hScroll = Scrollbar(self.myFrame, orient='horizontal', command=self.myCanvas.xview)
        self.vScroll.pack(side=RIGHT, fill=Y)
        self.hScroll.pack(side=BOTTOM, fill=X)
        self.myCanvas.configure(yscrollcommand=self.vScroll.set)
        self.myCanvas.configure(xscrollcommand=self.hScroll.set)
        self.myCanvas.bind("<Button-3>", self.DeleteObject)
        self.myCanvas.pack(side=LEFT, expand=True, fill=BOTH)

        # variables
        self.json_folder_path = tk.StringVar()
        self.last_contour_deleted={} #this dictionary will hold the last contour deleted, incase of an undo
        self.text_label = '' #label for duplicate grains and spot scales
        self.json_folder_location = None #where json files are stored.
        self.Current_Image = 'TL' #tracks which image type is displayed
        self.new_boundary = None # when a polygon is manually draw, it is saved to this variable.
        self.contourList = {}      #a list of all the contours to turn into  binary masks
        self.maskPath = ''
        self.width=0 #used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.height = 0 #used to set image dimensions on canvas, and in saved images. Ensures saved images have the same dimensions as input images. Important for relating spots to images, spatially.
        self.pairsList=[]
        self.count=0 #Used to put id's ontobreak  lines
        self.saveLocation = 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/_o.png'  # where the 1st binarised image will output to
        self.case = ''  # the function of the browse button. I.e. browse for capture, RL or TL
        self.folderPath = ''
        self.img = None
        self.image_iterator_current = None
        self.currentSpotNumber = tk.StringVar()
        self.spotPointCount = 0
        self.x0 = None
        self.y0 = None
        self.labelID = ''
        self.spotCount = 0
        self.rectangle = None
        self.Type = None
        self.imgCount = 0
        self.jsonList = []
        self.uniqueTag = None
        self.groupTag = None
        self.unique_sample_numbers = {} #a dictionary of all samples numbers of all images loaded for spot capture. Contains unique sample numbers only. Records spots per sample.
        self.sampleList = [] #a list of all sample numbers of all images loaded for spot capture. May contain duplicates.
        self.error_message_text = ''
        self.currentSample = None
        self.rectangleType = None
        self.boundaryPoints = []  # This MUST be cleared every time the polygon is saved
        self.thisPoly = None  # This MUST be set back to NONE every time the polygon is saved
        self.polyCoords = []  # Coordinates of the polygon currently active. This MUST be set back to [] every time the polygon is saved
        self.coordID = []  # List of coordinate ID's for the polygon currently active. This MUST be set back to [] every time the polygon is saved
        self.Move = False  # Whether or not a move action can take place. Records true/false if an existing entity was selected
        self.allPolys = {}  # ID-coordinate dictionary of all polygons on the page
        self.lineStart_y = None  # used for drawing a scale line
        self.lineStart_x = None  # used for drawing a scale line
        self.updatedX = None
        self.updatedY = None
        self.threshold = None
        self.spotID = '' #used when repositioning spots

        self.ProcessFolderFlag = False #flag that tracks whether an entire folder of masks is to be processed
        self.currentMask = None #if processing an entire mask folder, keep track of the current mask's file path


        # Global bindings (aka shortcuts)
        master.bind("s", lambda e: self.PointDraw())
        master.bind("a", lambda e: self.RectSpotDraw())
        master.bind("d", lambda e: self.DupDraw())
        master.bind("<Left>", lambda e: self.PrevImage())
        master.bind("<Right>", lambda e: self.NextImage())
        master.bind("<Escape>", lambda e: self.UnbindMouse())
        master.bind("p", lambda e: self.BoundaryDraw())
        master.bind("i", lambda e: self.EditPolygon())
        master.bind("m", lambda e: self.PointMove())
        master.bind("l", lambda e: self.DrawScale())

        self.myCanvas.bind_all("<MouseWheel>", self.ScrollWithMouseWheel)

    def DrawScale(self):
        #this allows the user to draw a two-point line to capture a length scale which exists in some of the images
        self.myCanvas.unbind("<Button-1>")  # unbind the spot digitisation
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<ButtonPress-1>", self.LineStart)
        self.myCanvas.bind("<B1-Motion>", self.LineDraw)
        self.myCanvas.bind("<ButtonRelease-1>", lambda e: self.Save())

    def LineStart(self, event):
        uniqueSuffix = 'scale'
        colour = 'red'
        uniqueCode = str(datetime.datetime.now())
        self.uniqueTag = uniqueSuffix + '_' + str(uniqueCode)
        self.lineStart_x = self.myCanvas.canvasx(event.x)
        self.lineStart_y = self.myCanvas.canvasy(event.y)
        self.scaleLine = self.myCanvas.create_line(self.lineStart_x, self.lineStart_y, self.lineStart_x + 1,
                                                   self.lineStart_y + 1, width=3, fill=colour, activefill='yellow',
                                                   tags=(self.uniqueTag))
        self.Type = 'SCALE'

    def LineDraw(self, moveEvent):
        #self.myCanvas.unbind("<ButtonPress-1>")
        self.updatedX = self.myCanvas.canvasx(moveEvent.x)
        self.updatedY = self.myCanvas.canvasy(moveEvent.y)
        self.myCanvas.coords(self.scaleLine, self.lineStart_x, self.lineStart_y, self.updatedX, self.updatedY)

    def ScrollWithMouseWheel(self, event):
        self.myCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def NextImage(self):
        self.imgCount += 1
        result = self.DisplayImages()
        if result == False:
            self.imgCount = self.imgCount - 1
            result = self.DisplayImages()

    def PrevImage(self):
        self.imgCount = self.imgCount - 1
        result = self.DisplayImages()
        if result == False:
            self.imgCount = self.imgCount + 1
            result = self.DisplayImages()

    def DupDraw(self):
        self.rectangleType = 'DUPLICATE'
        self.RectDraw()

    def BoundaryDraw(self):
        uniqueCode = str(datetime.datetime.now())
        self.myCanvas.unbind("<Button-1>")  # unbind the spot digitisation
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<ButtonPress-1>", self.PolyCoords)
        self.myCanvas.bind("<ButtonPress-2>", self.PolyComplete)
        self.groupTag = 'boundary' + uniqueCode  # polygon and points(ovals)will have the same group tag
        self.uniqueTag = 'poly' + uniqueCode  # only the polygon gets the unique id
        self.Type = "POLYGON"

    def PolyCoords(self, polyDrawEvent):
        self.x0 = self.myCanvas.canvasx(polyDrawEvent.x)
        self.y0 = self.myCanvas.canvasy(polyDrawEvent.y)
        xy = [self.x0, self.y0]
        coordID = 'p' + str(datetime.datetime.now())  # each point gets its own unique id
        if self.uniqueTag in self.allPolys:
            self.allPolys[self.uniqueTag].append([coordID, self.x0, self.y0])  # if the polygon exists, add extra points
        else:
            self.allPolys[self.uniqueTag] = [[coordID, self.x0,self.y0]]  # if this is the first point of a new poly, add the new poly and point to the dictionary
        coords = []  # used locally to collate all xy's
        points = self.allPolys[self.uniqueTag]
        for p in points:
            coords.append(p[1])
            coords.append(p[2])

        # Draw circle over vertex. Idea taken from:
        # https://stackoverflow.com/questions/51044836/tkinter-update-polygon-points-on-mouse-click
        # self.myCanvas.create_oval(self.x0-3, self.y0-3, self.x0+3, self.y0+3, fill='white',activefill = 'yellow', activeoutline='yellow',
        # outline='grey', width=1, tags = (self.groupTag, coordID))
        if len(self.allPolys[self.uniqueTag]) > 2:
            self.myCanvas.delete(self.uniqueTag)  # delete all pre-existing lines and redraw
            self.myCanvas.create_polygon(coords, fill='', outline='red', activeoutline='yellow', width=1,
                                         tags=(self.groupTag, self.uniqueTag))  # redraw,now includes the added point
        elif len(self.allPolys[self.uniqueTag]) == 2:
            self.myCanvas.delete(self.uniqueTag)  # delete all pre-existing lines and redraw
            self.myCanvas.create_line(coords, fill='red', activefill='yellow', width=1, tags=(
            self.groupTag, self.uniqueTag))  # if there are only two points, its a line not a polygon
        else:
            pass  # if there is only one point, don't draw any lines. A point will be drawn on the point as per line 159.

    def PolyComplete(self, event):
        self.myCanvas.unbind("<ButtonPress-2>") #unbind from polygon digitisation
        coords = []
        for coord in self.allPolys[self.uniqueTag]:
            coords.append([coord[1], coord[2]])
        self.new_boundary = coords
        self.SaveBreakChanges()

    def PointMove(self):
        self.myCanvas.bind("<Button-1>", self.StartPointMove)
        self.myCanvas.bind("<ButtonRelease-1>", self.FinishPointMove)

    def StartPointMove(self, moveEvent):
        thisObj = moveEvent.widget.find_withtag('current')[0]  # get the groupID of the entity
        self.thisObjID = self.myCanvas.gettags(thisObj)[1]  # This will make the unique point ID available in the next step:move. Because move doesn't click on a specific entity, there is no ID associated with 'current'
        self.groupID = self.myCanvas.gettags(thisObj)[0]
        self.myCanvas.bind("<B1-Motion>", self.UpdatePointMove)
        self.myCanvas.bind("<ButtonRelease-1>", self.FinishPointMove)
        self.Move = False
        if 'p' in self.thisObjID or 'spot' in self.thisObjID:  # Only points can be moved!
            self.Move = True

    def UpdatePointMove(self, moveEvent):
        if self.Move == False:
            return
        else:
            xyList = []  # used locally to draw the  polygon with  updated xy
            self.x0 = self.myCanvas.canvasx(moveEvent.x)
            self.y0 = self.myCanvas.canvasy(moveEvent.y)
            self.myCanvas.delete(self.thisObjID)  # delete the pre-existing point then redraw in the new position
            self.myCanvas.create_oval(self.x0 - 6, self.y0 - 6, self.x0 + 6, self.y0 + 6, fill='lightgreen',
                                      activefill='yellow', activeoutline='yellow', outline='green',
                                      width=2, tags=(self.groupID, self.thisObjID))
            all_IDs = self.myCanvas.find_withtag(
                self.groupID)  # get all items with the same group tag. This will include all ovals and the polygon
            for ID in all_IDs:
                uniqueID = self.myCanvas.gettags(ID)[1]  # get the unique ID of each entity that shares the group ID
                if "poly" in uniqueID or 'contour_' in uniqueID:  # test whether it's a polygon
                    for i in range(len(
                            self.allPolys[uniqueID])):  # find the point that was clicked on and update it's xy coords
                        if self.allPolys[uniqueID][i][0] == self.thisObjID:
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
                    self.myCanvas.create_text(self.x0 - 10, self.y0 - 10, fill='green', text=self.spotID,tags=(self.groupID, uniqueID))
                    self.spotID = uniqueID.split('_')[1]

    def FinishPointMove(self, moveEvent):
        self.myCanvas.unbind("<B1-Motion>")
        self.myCanvas.unbind("<ButtonRelease-1>")

        fileLocation = 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/t2_inv1_files'
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
                        if region['id'] == self.spotID and region['type']=='POINT':
                            x = self.x0+imageLeft
                            y = self.y0 +imageTop
                            newPoints = [{"x": x, "y": y}]
                            region["points"] = newPoints
                        elif region['id'] == self.spotID and region['type']=='RECTANGLE':
                            left_x=self.x0-(region['boundingBox']['width']/2)+ imageLeft
                            right_x=self.x0+(region['boundingBox']['width']/2) + imageLeft
                            top_y=self.y0-(region['boundingBox']['height']/2) +imageTop
                            bottom_y=self.y0+(region['boundingBox']['height']/2) +imageTop
                            newPoints = [{"x": left_x, "y": top_y},{"x": right_x, "y": top_y},{"x": right_x, "y": bottom_y},{"x": left_x, "y": bottom_y} ]
                            region["boundingBox"] ={
                                                        "height": region["boundingBox"]['height'],
                                                        "width": region["boundingBox"]['width'],
                                                        "left": left_x,
                                                        "top": top_y
                                                    }
                            region["points"] = newPoints

                    with open(os.path.join(fileLocation, self.jsonName), 'w', errors='ignore') as updatedFile:
                        json.dump(data, updatedFile, indent=4)
                    self.uniqueTag = None
                    self.groupTag = None
                    self.spotID = ''

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
            for x in range(0,len(contour_coords),2):
                x0 = contour_coords[x]-3
                y0=contour_coords[x+1]-3
                x1 = x0+3
                y1=y0+3
                coordID = 'p' + str(datetime.datetime.now())
                coordList.append([coordID,contour_coords[x],contour_coords[x+1]])
                self.myCanvas.create_oval(x0,y0,x1,y1,fill='white', activefill='yellow',activeoutline='yellow', outline='grey',width=2, tags=(self.groupTag, coordID))
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
            #print('I')
            if self.y0 == closestY:
                return  # duplicate point, do nothing
            else:
                #print('J')
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
        #self.SavePolygon()

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

    def RectSpotDraw(self):
        self.rectangleType = 'SPOT AREA'
        self.RectDraw()

    def RectDraw(self):
        self.myCanvas.unbind("<Button-1>")  # unbind the spot digitisation
        self.myCanvas.bind("<ButtonPress-1>", self.RectStartCoords)
        self.myCanvas.bind("<B1-Motion>", self.RectUpdateCoords)
        self.myCanvas.bind("<ButtonRelease-1>", self.RectFinalCoords)

    def RectStartCoords(self, event):
        groupSuffix = ''
        uniqueSuffix = ''
        colour = ''
        if self.rectangleType == 'DUPLICATE':
            groupSuffix = 'NewDup'
            uniqueSuffix = 'dupRect'
            colour = 'red'
            self.text_label = "Duplicate"
        if self.rectangleType == 'SPOT AREA':
            groupSuffix = 'NewSpot'
            uniqueSuffix = 'spotRect'
            colour = 'blue'
            self.text_label="spot area"

        self.spotPointCount += 1
        self.groupTag = groupSuffix + str(self.spotPointCount)
        self.uniqueTag = uniqueSuffix + str(self.spotPointCount)
        self.thisSpotID = self.groupTag
        self.rectStart_x = self.myCanvas.canvasx(event.x)
        self.rectStart_y = self.myCanvas.canvasy(event.y)
        self.rectangle = self.myCanvas.create_rectangle(self.rectStart_x, self.rectStart_y, self.rectStart_x + 1,
                                                        self.rectStart_y + 1, width=3, outline=colour,
                                                        activefill='yellow', activeoutline='yellow',
                                                        tags=(self.groupTag, self.uniqueTag))
        self.Type = 'RECTANGLE'

    def RectUpdateCoords(self, event):
        self.updatedX = self.myCanvas.canvasx(event.x)
        self.updatedY = self.myCanvas.canvasy(event.y)
        self.myCanvas.coords(self.rectangle, self.rectStart_x, self.rectStart_y, self.updatedX, self.updatedY)

    def RectFinalCoords(self, event):
        colour = ''
        if self.rectangleType == 'DUPLICATE':
            colour = 'red'
        if self.rectangleType == 'SPOT AREA':
            colour = 'blue'

        self.myCanvas.create_text(self.rectStart_x, self.rectStart_y - 15, text=self.text_label, fill=colour,font=("Helvetica", 12, "bold"), tags=self.groupTag)
        self.text_label=''
        if self.rectangleType == 'SPOT AREA':
            #self.onClickCreate()
            self.Save()
        if self.rectangleType == 'DUPLICATE':
            self.Save()

    def undo_delete_contour(self):
        dict_key = list(self.last_contour_deleted.keys())[0]
        self.contourList[dict_key] = self.last_contour_deleted[dict_key]
        self.last_contour_deleted.clear()
        if self.Current_Image== 'TL':
            self.Load_Image(1)
        elif self.Current_Image == 'RL':
            self.Load_Image(0)



    def DeleteObject(self, event):
        thisObj = event.widget.find_withtag('current')[0]  # get the object clicked on
        thisObjID = self.myCanvas.gettags(thisObj)[0]  # find the group tag for the object clicked on
        if thisObjID != "Image":  # make sure you haven't selected the image
            if 'line_' in thisObjID: #breaklines don't get written to a json file
                coords = self.myCanvas.coords(thisObjID)
                x1 = coords[0]
                y1 = coords[1]
                x2 = coords[2]
                y2 = coords[3]
                self.pairsList.remove([(x1,y1),(x2,y2)])
                self.myCanvas.delete(thisObjID)  # delete everything with the same groupID
            elif 'contour_' in thisObjID:
                self.last_contour_deleted.clear()  # only keeps the last contour deleted
                self.last_contour_deleted[thisObjID] = self.contourList[thisObjID]  # store the last contour to be deleted
                del self.contourList[thisObjID]
                self.myCanvas.delete(thisObjID)
            elif 'extcont_' in thisObjID:
                contour_coords = self.contourList[thisObjID]
                polygon = Polygon(contour_coords)  # create a shapely polygon
                representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
                self.threshold = label(self.threshold, background=0, connectivity=None).astype('uint8')
                blob_label = self.threshold[int(representative_point.y),int(representative_point.x)]
                if int(blob_label)!=0:
                    self.threshold[self.threshold==blob_label]=0
                self.last_contour_deleted.clear() #only keeps the last contour deleted
                self.last_contour_deleted[thisObjID] = self.contourList[thisObjID] #store the last contour to be deleted
                del self.contourList[thisObjID]
                self.myCanvas.delete(thisObjID)
            else:
                self.myCanvas.delete(thisObjID)  # delete everything with the same groupID
                with open(os.path.join(self.folderPath, self.image_iterator_current[0]),
                          errors='ignore') as jsonFile:  # open the json file for the image
                    data = json.load(jsonFile)

                for i in range(0, len(data['regions'])):  # If the object already exists in the json
                    if data['regions'][i]['id'] == thisObjID:
                        data['regions'].pop(i)  # get rid of it. Don't read further (affects incrementor?)
                        # print('Already exists in file')
                        break
                with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
                    json.dump(data, updatedFile, indent=4)  # rewrite the json without the object
                    # print('removed from json')
                try:
                    self.unique_sample_numbers[self.currentSample].discard(thisObjID)
                except:
                    pass
        else:
            pass

    def DigitisePoint(self, drawSpotEvent):
        self.x0 = self.myCanvas.canvasx(drawSpotEvent.x)
        self.y0 = self.myCanvas.canvasy(drawSpotEvent.y)
        x1 = self.x0 - 6
        x2 = self.x0 + 6
        y1 = self.y0 - 6
        y2 = self.y0 + 6
        self.spotPointCount += 1
        self.groupTag = 'NewSpot' + str(self.spotPointCount)
        self.uniqueTag = 'SpotOval' + str(self.spotPointCount)
        self.thisSpotID = self.groupTag
        self.currentSpotNumber.set(self.groupTag)
        self.myCanvas.create_oval(x1, y1, x2, y2, outline='blue', fill='blue', activefill='yellow',
                                  activeoutline='yellow', width=4, tags=(self.groupTag, self.uniqueTag))
        self.myCanvas.create_text(x1, y1 - 15, text=self.currentSpotNumber.get(), fill='blue',
                                  font=("Helvetica", 12, "bold"), tags=self.groupTag)
        self.onClickCreate()
        self.Type = 'POINT'

    def UnbindMouse(self):
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<Button-1>")  # unbind point digitisation

    def PointDraw(self):
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<Button-1>", self.DigitisePoint)

    def Browse(self, case):
        test = np.zeros((5, 5))
        if case == 'RL': #if browing for an RL image in the binarise menu
            filename = filedialog.askopenfilename(filetypes=[("all files", "*.*")])
            self.RLPath.set(filename)
            self.RLTextBox.delete(0, END)
            self.RLTextBox.insert(0, filename)
        elif case == 'TL': #if browsing for a TL image in the binarise menu
            filename = filedialog.askopenfilename(filetypes=[("all files", "*.*")])
            self.TLPath.set(filename)
            self.TLTextBox.delete(0, END)
            self.TLTextBox.insert(0, filename)

        elif case == 'Mask': #if browsing for a mask image in the binarise menu
            folderName = filedialog.askdirectory()
            self.MaskFolderLocation.set(folderName)
            self.MaskTextBox.delete(0, END)
            self.MaskTextBox.insert(0, folderName)

        elif case == 'Folder': #if browsing for a folder
            folderName = filedialog.askdirectory()
            self.Folder_Location.set(folderName)
            self.Folder_TextBox.delete(0, END)
            self.Folder_TextBox.insert(0, folderName)
        elif case == 'json':
            json_folder_name = filedialog.askdirectory()
            self.json_folder_location = json_folder_name
            self.json_folder_path.set(json_folder_name)
        elif case == 'capture': #if browsing for a folder of images for spot capture
            filename = filedialog.askdirectory()
            self.folderPath = filename
            self.image_folder_path.set(filename)
            if self.load_json_folder.get() == 0:
                self.json_folder_path.set(self.image_folder_path.get())

        elif case == 'File':
            filename = filedialog.askopenfilename(filetypes=[("all files", "*.*")])
            self.File_Location.set(filename)
            self.File_TextBox.delete(0, END)
            self.File_TextBox.insert(0, filename)
        else:
            print('Browse error. No case')

    def check_for_images_and_jsons(self):
        has_images = False
        missing_json_files = []
        for path, folders, files in os.walk(self.folderPath):
            for name in files:
                if os.path.splitext(name)[1] == '.png': #check for images
                    has_images = True
                    json_file = os.path.splitext(name)[0]+'.json'
                    has_json = self.does_json_exist(os.path.join(self.folderPath,json_file))
                    if not has_json:
                        missing_json_files.append(name)
        return has_images, missing_json_files

    def does_json_exist(self, json_file):
        return os.path.exists(json_file)

    def ok_cancel_create_json_files(self, list_of_json_files_to_create):
        self.ok_cancel_json_window = Toplevel(root)
        self.ok_cancel_json_window.title("Create missing json Files")
        self.ok_cancel_json_window.minsize(400,100)

        self.ok_cancel_json_text = Label(self.ok_cancel_json_window, text = "Json files are missing. Do you want to create them?")
        self.ok_cancel_json_text.grid(column = 0, row = 0)

        self.ok_create_jsons = Button(self.ok_cancel_json_window, text="OK", width=5,command=lambda: self.close_popup_window_and_create_jsons(self.ok_cancel_json_window,list_of_json_files_to_create))
        self.ok_create_jsons.grid(column=1, row=1, padx=2, pady=5)

        self.cancel_create_jsons = Button(self.ok_cancel_json_window, text="Cancel", width=8,command=lambda: self.close_window(self.ok_cancel_json_window))
        self.ok_create_jsons.grid(column=2, row=1, padx=2, pady=5)

    def close_popup_window_and_create_jsons(self,window, json_files_to_create):
        self.close_window(window)
        for file_name in json_files_to_create:
            self.write_json_file(file_name)

    def write_json_file(self,file):
        file_extension = os.path.splitext(file)[-1]
        path  = os.path.join(self.image_folder_path.get(),file)
        img = cv2.imread(path)[:,:,0]
        json_name = os.path.splitext(file)[0]+".json"
        data = {"asset": {
                    "format": file_extension,
                    "id": self.create_hash(file),
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


    def create_hash(self,item_to_hash):
        hash_code = hash(item_to_hash)
        return hash_code

    def GetImageInfo(self):
        #Does 3 things:
        # Check for images in the folder, returns error message if there are none.
        #checks if each image has a corresponding json file. Offers to create the ones that are missing.
        #loads the images for spot capture
        self.jsonList = []

        has_images,missing_json_files = self.check_for_images_and_jsons()

        if has_images == False:
            self.error_message_text = "The folder contains no images for data capture."
            self.open_error_message_popup_window()
            return

        if missing_json_files:
            if self.create_json_var.get() == 1:
                for file in missing_json_files:
                    self.write_json_file(file)
            else:
                self.ok_cancel_create_json_files(missing_json_files)

        # Get a list of unique sample ID's and the spots associated with them.
        for path, folders, files in os.walk(self.folderPath):
            for name in files:
                if os.path.splitext(name)[1] == '.json':
                    with open(os.path.join(self.folderPath, name), errors='ignore') as jsonFile:
                        data = json.load(jsonFile)
                    if not name in self.jsonList:
                        self.jsonList.append([name, data['asset']['name']]) #add the image name to the list of json files, as jsons and images have same name
                        sampleID = data['asset']['name'].split("_")[0]
                        if sampleID not in self.unique_sample_numbers:#create a dictionary with unique sample numbers only
                            self.unique_sample_numbers[sampleID]=set()
                            self.sampleList.append(sampleID)
                            for region in data['regions']: #everytime we find a json with a unique sample number, don't forget to get the spots listed in that json
                                self.unique_sample_numbers[sampleID].add(region['id'])
                        else: #you might find jsons with existing sample numbers. They may also contains spots, record those spots.
                            for region in data['regions']:
                                self.unique_sample_numbers[sampleID].add(region['id'])

        self.sampleList.sort()
        #self.uniqueSampleNumbers = {i: set() for i in self.list_of_sample_numbers} #this makes a set of the sample numbers, i.e. keeping unique sample numbers only, no duplicates

        # This is likely inefficient. First I  looped through to get all unique image ID's and create a dictionary. Then I loop through to add all sample ID's to the dictionary
       # for path, folders, files in os.walk(self.folderPath):
        #    for name in files:
         #       if os.path.splitext(name)[1] == '.json':
          #          with open(os.path.join(self.folderPath, name), errors='ignore') as jsonFile:
           #             data = json.load(jsonFile)
            #        pattern = r"_p[0-9]{1,2}.png"
             #       sample = re.sub(pattern, "", data['asset']['name'])
              #      for region in data['regions']:
               #         if region['tags'][0] == 'SPOT':
                #            self.uniqueSampleNumbers[sample].add(region['id'])
        #self.sampleList = list(self.list_of_sample_numbers)


    def open_error_message_popup_window(self):
        self.errorMessageWindow = Toplevel(root)
        self.errorMessageWindow.title("Error")
        self.errorMessageWindow.minsize(300, 100)
        self.errorLabel = Label(self.errorMessageWindow, text=self.error_message_text)
        self.errorLabel.grid(column=0, row=0)

    def Save(self):
        #if self.rectangleType == 'Duplicate':
        if self.Type == 'RECTANGLE':
            with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
                data = json.load(jsonFile)
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

            #Region = {"id": self.uniqueTag, "type": self.Type, "tags": ["DUPLICATE"],
            newRegion = {"id": self.uniqueTag, "type": self.Type, "tags": [self.rectangleType],
                         "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                         "points": [{"x": left, "y": top}, {"x": right, "y": top}, {"x": right, "y": bottom},
                                    {"x": left, "y": bottom}]}
            data['regions'].append(newRegion)

            with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)
            return None

        if self.Type == 'SCALE':
            height = 0
            width = 0
            left = 0
            right = 0
            top = 0
            bottom = 0

            height = abs(self.lineStart_y - self.updatedY)
            width = abs(self.lineStart_x - self.updatedX)

            if self.lineStart_x < self.updatedX:  # x increases left to right
                left = self.lineStart_x
                right = self.updatedX
            else:
                left = self.updatedX
                right = self.lineStart_x

            if self.lineStart_y < self.updatedY:  # y increases top to bottom
                top = self.lineStart_y
                bottom = self.updatedY
            else:
                top = self.updatedY
                bottom = self.lineStart_y

            with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
                data = json.load(jsonFile)
                newRegion = {"id": self.uniqueTag, "type": self.Type, "tags": ["SCALE"],
                             "boundingBox": {"height": height, "width": width, "left": left, "top": top},
                             "points": [{"x": self.lineStart_x, "y": self.lineStart_y},
                                        {"x": self.updatedX, "y": self.updatedY}]}
                data['regions'].append(newRegion)
            with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)

            self.scaleLine = None
            return None

        spotNo = self.currentSpotNumber.get()
        userText = spotNo.strip()

        try:
            testNum = float(userText)
        except:
            self.error_message_text = "Non-numeric spot number"
            self.open_error_message_popup_window()
            return None
        if userText in self.unique_sample_numbers[self.currentSample]:
            self.error_message_text = 'Spot number already captured for PDF: ' + str(self.currentSample)
            self.open_error_message_popup_window()
            return None
        if userText.isdecimal():
            self.error_message_text = 'Integers are not permitted'
            self.open_error_message_popup_window()
            return None
        else:
            self.unique_sample_numbers[self.currentSample].add(userText)
        height = 0
        width = 0
        left = 0
        right = 0
        top = 0
        bottom = 0

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), errors='ignore') as jsonFile:
            data = json.load(jsonFile)
            anyMatch = False
            for region in data['regions']:  # If the spot already exists in the jSON
                if region['id'] == self.thisSpotID:
                    region['id'] = userText
                    anyMatch = True

            if anyMatch == False and self.Type == "POINT":  # if it's newly digitised and does not yet exist in the json file, and it's a point
                newRegion = {"id": userText, "type": self.Type, "tags": ["SPOT"],
                             "boundingBox": {"height": 5, "width": 5, "left": self.x0, "top": self.y0},
                             "points": [{"x": self.x0, "y": self.y0}]}
                data['regions'].append(newRegion)

            if anyMatch == False and self.Type == "RECTANGLE":  # if it's newly digitised and does not yet exist in the json file, and it's a rectangle
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
                data['regions'].append(newRegion)

        with open(os.path.join(self.folderPath, self.image_iterator_current[0]), 'w', errors='ignore') as updatedFile:
            json.dump(data, updatedFile, indent=4)

        self.myCanvas.itemconfig(self.labelID, text=userText, state=tk.NORMAL, tags=userText)
        self.myCanvas.itemconfig(self.thisSpotID, tags=(userText, self.uniqueTag))
        self.currentSpotTextBox.delete(first=0, last=100)
        self.spotCaptureWindow.destroy()

    def onClickCreate(self):
        self.thisSpot = self.myCanvas.find_withtag(self.uniqueTag)[0]
        all_IDs = self.myCanvas.find_withtag(self.groupTag)
        for ID in all_IDs:
            if not ID == self.thisSpot:
                self.labelID = ID

        self.spotCaptureWindow = Toplevel(root)
        self.spotCaptureWindow.title("Capture Spot Number")
        self.spotCaptureWindow.minsize(300, 100)
        self.spotCaptureLabel = Label(self.spotCaptureWindow, text='Spot ID')
        self.spotCaptureLabel.grid(column=0, row=0)
        self.currentSpotNumber = tk.StringVar()
        self.currentSpotNumber.set('')
        self.currentSpotTextBox = Entry(self.spotCaptureWindow, width=20, textvariable=self.currentSpotNumber)
        self.currentSpotTextBox.grid(column=1, row=0)
        self.currentSpotTextBox.focus()
        self.saveSpotNo = Button(self.spotCaptureWindow, text='Save', command=self.Save)
        self.spotCaptureWindow.bind('<Return>', lambda e: self.Save())
        self.saveSpotNo.grid(column=0, row=1, pady=5)

    def load_files_for_spot_capture(self):
        self.browse_for_files_window = Toplevel(root)
        self.browse_for_files_window.title("Select Images for Spot Capture")
        self.browse_for_files_window.minsize(400,100)

        #browse for images
        self.image_folder_Label = Label(self.browse_for_files_window, text="Image Folder")
        self.image_folder_Label.grid(column=0, row=0)
        self.image_folder_path = tk.StringVar()
        self.image_folder_path.set('')
        self.image_folder_text_box = Entry(self.browse_for_files_window, width=150, textvariable=self.image_folder_path)
        self.image_folder_text_box.grid(column=1, row=0)
        self.browse_for_image_folder = Button(self.browse_for_files_window, text="...", width=5, command=lambda: self.Browse('capture'))
        self.browse_for_image_folder.grid(column=2, row=0, padx=2, pady=5)

        #browse for json files
        self.json_folder_Label = Label(self.browse_for_files_window, text="Json Folder")
        self.json_folder_Label.config(state=DISABLED)
        self.json_folder_Label.grid(column=0, row=2)
        self.json_folder_path = tk.StringVar()
        self.json_folder_path.set('')

        self.json_folder_text_box = Entry(self.browse_for_files_window, width=150, textvariable=self.json_folder_path)
        self.json_folder_text_box.config(state=DISABLED)
        self.json_folder_text_box.grid(column=1, row=2)

        self.browse_for_json_folder = Button(self.browse_for_files_window, text="...", width=5,command=lambda: self.Browse('json'))
        self.browse_for_json_folder.config(state=DISABLED)
        self.browse_for_json_folder.grid(column=2, row=2, padx=2, pady=5)

        self.create_json_var = IntVar()
        self.create_json_files_check_button = Checkbutton(self.browse_for_files_window,text='Generate json files if missing',variable=self.create_json_var)
        self.create_json_files_check_button.grid(column=0, row=3, padx=2, pady=5)

        self.load_json_folder = IntVar()
        self.load_json_folder_check_button = Checkbutton(self.browse_for_files_window, text='load jsons separately',variable=self.load_json_folder,command=lambda: self.activate_browse_for_json_folder())
        self.load_json_folder_check_button.grid(column=1, row=3, padx=2, pady=5)

        self.ok_load_files_for_capture = Button(self.browse_for_files_window, text="OK", width=5,command=lambda: self.load_files())
        self.ok_load_files_for_capture.grid(column=0, row=4, padx=2, pady=5)

        self.cancel_load_files_for_capture = Button(self.browse_for_files_window, text="Cancel", width=8,command=lambda: self.close_window(self.browse_for_files_window))
        self.cancel_load_files_for_capture.grid(column=1, row=4, padx=2, pady=5)


    def close_window(self,window):
            window.destroy()

    def load_files(self):
        self.GetImageInfo()
        self.DisplayImages()
        self.close_window(self.browse_for_files_window)

    def activate_browse_for_json_folder(self):
        if self.load_json_folder.get()==1:
            self.json_folder_Label.config(state=NORMAL)
            self.json_folder_text_box.config(state=NORMAL)
            self.browse_for_json_folder.config(state = NORMAL)
            self.json_folder_path.set("")

        elif self.load_json_folder.get()==0:
            self.json_folder_Label.config(state=DISABLED)
            self.json_folder_text_box.config(state=DISABLED)
            self.browse_for_json_folder.config(state=DISABLED)
            self.json_folder_path.set(self.image_folder_path.get())


    def browseImages(self):
        self.browseImagesWindow = Toplevel(root)
        self.browseImagesWindow.title("Select Images to Binarise")
        self.browseImagesWindow.minsize(400, 100)
        self.browseImagesWindow.attributes('-topmost', True)

        self.RL_Label = Label(self.browseImagesWindow, text="RL Image")
        self.RL_Label.grid(column=0, row=0)
        self.RLPath = tk.StringVar()
        self.RLPath.set('')
        self.RLTextBox = Entry(self.browseImagesWindow, width=150, textvariable=self.RLPath)
        self.RLTextBox.grid(column=1, row=0)
        self.browseRL = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('RL'))
        self.browseRL.grid(column=3, row=0, padx=2, pady=5)
        self.rlVar = IntVar()
        self.rlCheckButton = Checkbutton(self.browseImagesWindow, text= 'Binarise  RL',variable=self.rlVar)
        self.rlCheckButton.grid(column=4, row=0, padx=2, pady=5)
        self.Display_RL_Image_Button = Button(self.browseImagesWindow, text="Display", width=8, command=lambda: self.Load_Image(0))
        self.Display_RL_Image_Button.grid(column=5, row=0, padx=2, pady=5)

        self.TL_Label = Label(self.browseImagesWindow, text="TL Image")
        self.TL_Label.grid(column=0, row=1)
        self.TLPath = tk.StringVar()
        self.TLPath.set('')
        self.TLTextBox = Entry(self.browseImagesWindow, width=150, textvariable=self.TLPath)
        self.TLTextBox.grid(column=1, row=1)
        self.browseTL = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('TL'))
        self.browseTL.grid(column=3, row=1, padx=2, pady=5)
        self.tlVar = IntVar()
        self.tlCheckButton = Checkbutton(self.browseImagesWindow, text='Binarise  TL', variable=self.tlVar)
        self.tlCheckButton.grid(column=4, row=1, padx=2, pady=5)
        self.Display_TL_Image_Button = Button(self.browseImagesWindow, text="Display", width=8,
                                              command=lambda: self.Load_Image(1))
        self.Display_TL_Image_Button.grid(column=5, row=1, padx=2, pady=5)

        self.Mask_Label = Label(self.browseImagesWindow, text="Mask Save Location")
        self.Mask_Label.grid(column=0, row=2)
        self.MaskFolderLocation = tk.StringVar()
        self.MaskFolderLocation.set('')
        self.MaskTextBox = Entry(self.browseImagesWindow, width=100, textvariable=self.MaskFolderLocation)
        self.MaskTextBox.grid(column=1, row=2)
        self.browseMask = Button(self.browseImagesWindow, text="...",width = 5, command=lambda: self.Browse('Mask'))
        self.browseMask.grid(column=3, row=2, padx=2, pady=5)
        self.saveMask = Button(self.browseImagesWindow, text="Save Mask", command=lambda: self.SaveMask())
        self.saveMask.grid(column=4, row=2, padx=2, pady=5)

        self.Process_Image = Label(self.browseImagesWindow, text="Process Mask Image")
        self.Process_Image.grid(column=0, row=3)
        self.File_Location = tk.StringVar()
        self.File_Location.set('')
        self.File_TextBox = Entry(self.browseImagesWindow, width=100, textvariable=self.File_Location)
        self.File_TextBox.grid(column=1, row=3)
        self.Browse_File = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('File'))
        self.Browse_File.grid(column=3, row=3, padx=3, pady=5)
        self.Display_Mask = Button(self.browseImagesWindow, text="Display Mask", width=15, command=lambda: self.DisplayMask())
        self.Display_Mask.grid(column=4, row=3, padx=3, pady=5)


        self.Process_Folder = Label(self.browseImagesWindow, text="Process Mask Folder")
        self.Process_Folder.grid(column=0, row=4)
        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')
        self.Folder_TextBox = Entry(self.browseImagesWindow, width=100, textvariable=self.Folder_Location)
        self.Folder_TextBox.grid(column=1, row=4)
        self.Browse_Folder = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('Folder'))
        self.Browse_Folder.grid(column=3, row=4, padx=3, pady=5)
        self.Process_Folder = Button(self.browseImagesWindow, text="Process Folder", width=15,command=lambda: self.ProcessFolder())
        self.Process_Folder.grid(column=4, row=4, padx=3, pady=5)

        self.BinariseButton = Button(self.browseImagesWindow, text="Binarise", command=self.binariseImages)
        self.BinariseButton.grid(column=0, row=5, padx=2, pady=5)
        self.SeparateButton = Button(self.browseImagesWindow, text="Separate Grains", command=self.Separate)
        self.SeparateButton.grid(column=0, row=6, padx=2, pady=5)
        self.breakLine = Button(self.browseImagesWindow, text="Draw Break Line", command=self.DrawBreakLine)
        self.breakLine.grid(column=0, row=7, padx=2, pady=5)
        self.saveChanges = Button(self.browseImagesWindow, text="Save Changes", command=self.SaveBreakChanges)
        self.saveChanges.grid(column=0, row=8, padx=2, pady=5)
        self.measureShapes = Button(self.browseImagesWindow, text="Measure Shapes",command=self.MeasureShapes)
        self.measureShapes.grid(column=0, row=9, padx=2, pady=5)
        self.pushDB = Button(self.browseImagesWindow, text="Push to DB",command=self.DBPush)
        self.pushDB.grid(column=0, row=10, padx=2, pady=5)
        self.moveSpot = Button(self.browseImagesWindow, text="Reposition spot", command=self.PointMove)
        self.moveSpot.grid(column=0, row=11, padx=2, pady=5)
        self.grain_boundary_capture = Button(self.browseImagesWindow, text ="Grain Boundary Capture [p]", command=self.BoundaryDraw)
        self.grain_boundary_capture.grid(column=0, row=12, padx=2, pady=5)

        #self.insertPolygonPoint = Button(self.browseImagesWindow, text="insert Point", command=self.EditPolygon)
        #self.insertPolygonPoint.grid(column=0, row=8, padx=2, pady=5)
        #self.deletePolygonPoint = Button(self.browseImagesWindow, text="delete Point", command=self.EditPolygon)
        #self.deletePolygonPoint.grid(column=0, row=9, padx=2, pady=5)

        self.undo_delete = Button(self.browseImagesWindow, text="Undo Delete Contour", command=self.undo_delete_contour)
        self.undo_delete.grid(column=0, row=13, padx=2, pady=5)

    def ProcessFolder(self):
        self.ProcessFolderFlag = True
        for path,folder,files in os.walk(self.Folder_Location.get()):
            for name in files:
                self.currentMask = self.Folder_Location.get()+'/'+name #the file path of the current mask we're processing
                print('current mask: ', self.currentMask)
                self.DisplayMask()
                self.MeasureShapes()
                self.DBPush()
                self.currentMask = None
            self.ProcessFolderFlag = False
        print('Processing complete')

    def DisplayMask(self):
        path = self.File_Location.get()
        rl_path = ''
        tl_path = ''
        if path != '':
            self.threshold = cv2.imread(self.File_Location.get())[:, :, 0]
            self.threshold[self.threshold > 0] = 255
           # self.threshold = label(self.threshold,background=0, connectivity=None).astype('uint8')
            #labelim = label(image_open, background=0, connectivity=None)
            #self.threshold = labelim.astype('uint8')
            jsonName = '_'.join(path.split('/')[-1].split('_')[:3])+'.json'
            sampleid = jsonName.split('_')[0]
            t_regionID = path.split('/')[-1].split('_')
            regionID = '_'.join(t_regionID[4:]).replace('.png', '')

            if self.json_folder_location is None:
                self.error_message_text = "JSON file location has not been defined"
                self.open_error_message_popup_window()
                return
            else:
                with open(os.path.join(self.json_folder_location,jsonName), errors='ignore') as jsonFile:
                    data = json.load(jsonFile)
                for region in data["regions"]:
                    if region["id"] == regionID:
                        rl_path = region["RL_Path"] if "RL_Path" in region else self.RLPath.get()
                        tl_path = region["TL_Path"] if "TL_Path" in region else self.TLPath.get()
                        mask_path = region["Mask_Path"].split('\\')[0] if "Mask_Path" in region else self.MaskFolderLocation.get()
                self.RLTextBox.delete(0, END)
                self.RLTextBox.insert(0, rl_path)
                self.TLTextBox.delete(0, END)
                self.TLTextBox.insert(0, tl_path)
                self.MaskTextBox.delete(0, END)
                self.MaskTextBox.insert(0, mask_path)

        elif self.ProcessFolderFlag == True:
            self.threshold = cv2.imread(self.currentMask)[:, :, 0]

        image_pill = Image.fromarray(self.threshold)
        self.img = ImageTk.PhotoImage(image=image_pill)
        self.myCanvas.delete('all')
        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        self.contourList = {}
        count_contour = 0
        for i in range(len(contoursFinal)):
            groupID = 'extcont_' + str(count_contour)
            uniqueID = 'extcont_' + str(count_contour)
            squeeze = np.squeeze(contoursFinal[i])
            self.contourList[uniqueID] = squeeze
            poly_coords = []
            if len(contoursFinal[i]) <=1:
                pass
            else:
                for coords in squeeze:
                    poly_coords.append(coords[0])
                    poly_coords.append(coords[1])
                self.myCanvas.create_polygon(poly_coords, fill='', outline='red', activeoutline='yellow', width=3,
                                         tags=(groupID, uniqueID))
            count_contour += 1

    def DBPush(self):
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
        # print(queryStatement)
        cursor.execute(queryStatement)

        results = cursor.fetchall()

        if len(results) == 0:
            for row in self.dfShapeRounded.itertuples(False):
                valuesString = ''
                # print(row)
                for i in range(len(row)):
                    if i < len(row) - 1:
                        if i == 18 or i == 4 or i == 19 or i == 3 or i == 1:
                            valuesString = valuesString + "'" + str(row[i]) + "',"
                        else:
                            valuesString = valuesString + str(row[i]) + ','

                    if i == len(row) - 1:
                        valuesString = valuesString + "'" + str(row[i]) + "'"

                insertStatement = '''INSERT INTO shape_descriptors(''' + colArray + ''') VALUES(''' + valuesString + ''')'''
                # print(insertStatement)
                cursor.execute(insertStatement)
                cursor.commit()
            cursor.close()
            connection.close()
            print('Insert complete: ', regionID)
        else:
            cursor.close()
            connection.close()
            print('Sample already in DB: ', regionID)

    def SaveMask(self):
        fileRL = self.RLPath.get()
        fileTL = self.TLPath.get()
        maskPath = self.MaskFolderLocation.get()
        self.threshold[self.threshold>0]=255
        fig = plt.figure(figsize=(15, 15), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1])
        jsonName=''
        sampleid=''
        regionID=''

        if fileRL != '':
            fileName = fileRL.split('/')[-1]
            jsonName = '_'.join(fileName.split('_')[:3])+'.json'
            sampleid = jsonName.split('_')[0]
            t_regionID = fileName.split('_')
            regionID = '_'.join(t_regionID[4:]).replace('.png', '')

        elif self.File_Location.get() != '':
            fileName = self.File_Location.get().split('/')[-1]
            jsonName = '_'.join(fileName.split('_')[:2])


        maskPath = os.path.join(maskPath,fileName)
        if self.json_folder_location is None or self.json_folder_location == '':
            self.error_message_text = 'JSON file location has not been set'
            self.open_error_message_popup_window()
            return
        else:
            with open(os.path.join(self.json_folder_location,jsonName), errors='ignore') as jsonFile:
                data = json.load(jsonFile)
            for region in data['regions']:
                if region['id'] == regionID:
                    region["RL_Path"] = fileRL
                    region["TL_Path"] = fileTL
                    region["Mask_Path"] = maskPath

            with open(os.path.join(self.json_folder_location,jsonName), 'w', errors='ignore') as updatedFile:
                json.dump(data, updatedFile, indent=4)

        cv2.imwrite(maskPath, self.threshold)

    def DrawBreakLine(self):
        # print('DrawScale')
        self.myCanvas.unbind("<Button-1>")
        self.myCanvas.unbind("<ButtonPress-1>")
        self.myCanvas.unbind("<B1-Motion>")
        self.myCanvas.unbind("<ButtonRelease-1>")
        self.myCanvas.bind("<ButtonPress-1>", self.BreakLineStart)
        self.myCanvas.bind("<B1-Motion>", self.BreakLineUpdate)
        self.myCanvas.bind("<ButtonRelease-1>", lambda e: self.SaveNewBreakLine())

    def BreakLineStart(self, event):
        t_ID = 'line_' + str(datetime.datetime.now())
        ID = t_ID.replace(' ', '')
        colour = 'red'
        self.lineStart_x = self.myCanvas.canvasx(event.x)
        self.lineStart_y = self.myCanvas.canvasy(event.y)
        self.Line = self.myCanvas.create_line(self.lineStart_x, self.lineStart_y, self.lineStart_x + 1,
                                              self.lineStart_y + 1, width=3, fill=colour, activefill='yellow',tags=(ID))

    def BreakLineUpdate(self, moveEvent):
        self.myCanvas.unbind("<ButtonPress-1>")
        self.updatedX = self.myCanvas.canvasx(moveEvent.x)
        self.updatedY = self.myCanvas.canvasy(moveEvent.y)
        self.myCanvas.coords(self.Line, self.lineStart_x, self.lineStart_y, self.updatedX, self.updatedY)

    def SaveNewBreakLine(self):
        self.pairsList.append([(self.lineStart_x, self.lineStart_y), (self.updatedX, self.updatedY)])

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
        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        #image_open = cv2.morphologyEx(self.threshold, cv2.MORPH_OPEN, kernel)
        #image_open[image_open > 0] = 255
        #labelim = label(image_open, background=0, connectivity=None)
        labelim = label(self.threshold, background=0, connectivity=None)
        self.threshold = labelim.astype('uint8')
        #mask_image = copy.deepcopy(self.threshold)
        #mask_image_colour = cv2.cvtColor(mask_image, cv2.COLOR_GRAY2RGB)
        #mask_image_colour[:,:,1] = 0
        #mask_image_colour[:, :, 2] = 0
        #mask_image_colour[mask_image_colour[:, :, 0]>0] = 255
        if self.TLPath.get() != '' and self.Current_Image=='TL':
            original_Image = cv2.imread(self.TLPath.get())
            #output_Image = cv2.addWeighted(original_Image,0.7, mask_image_colour, 0.3, 0)
        elif self.RLPath.get() != '' and self.Current_Image=='RL':
            original_Image = cv2.imread(self.RLPath.get())
            #output_Image = cv2.addWeighted(original_Image, 0.7, mask_image_colour, 0.3, 0)
        #else:
            #output_Image = mask_image_colour
        #view the image
        #image_pill = Image.fromarray(output_Image)
        image_pill = Image.fromarray(original_Image)
        self.img = ImageTk.PhotoImage(image=image_pill)
        self.myCanvas.delete('all')
        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        #paint the contours on
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        count_contour = 0
        self.contourList.clear()
        for i in range(len(contoursFinal)):
            groupID = 'extcont_' + str(count_contour)
            uniqueID = 'extcont_' + str(count_contour)
            squeeze = np.squeeze(contoursFinal[i])
            self.contourList[uniqueID] = squeeze
            poly_coords = []
            for coords in squeeze:
                poly_coords.append(coords[0])
                poly_coords.append(coords[1])
            self.myCanvas.create_polygon(poly_coords, fill='', outline='red', activeoutline='yellow', width=3,
                                         tags=(groupID, uniqueID))
            count_contour += 1

    def MeasureShapes(self):
        self.jsonName=''
        if self.File_Location.get() != '' and self.threshold is None: #not sure if I can do this
            self.threshold = cv2.imread(self.File_Location.get())[:,:,0]
            self.width = self.threshold.shape[1]
            self.height = self.threshold.shape[0]
        image_remove = removeSmallObjects(self.threshold,15)  # remove small objects below a threshold size (max object size/15)
        image_clear = clear_border(labels=image_remove, bgval=0,buffer_size=1)  # remove objects that touch the image boundary
        image_clear_uint8 = image_clear.astype('uint8')
        self.threshold = image_clear_uint8

        self.contourList={}
        fileLocation = 'C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/t2_inv1_files'
        if self.File_Location.get() != '': #if we're processing a single mask image
            fPath = self.File_Location.get()
        elif self.ProcessFolderFlag == True: #if w are processing an entire folder of masks
            fPath = self.currentMask

        else: # if we are processing an image we have just binarised
            fPath= self.RLPath.get()
        self.jsonName = '_'.join(fPath.split('/')[-1].split('_')[:3]) + '.json'
        sampleid = self.jsonName.split('_')[0]
        t_regionID = fPath.split('/')[-1].split('_')
        regionID = '_'.join(t_regionID[4:]).replace('.png', '')

        imageDimensions = ''  # this will record the XY dimensions of the cropped image, so that the contours can be redrawn on a blank image in the event that the cropped image  file is ever lost
        spot = False
        for path, folder, files in os.walk(fileLocation):
            for name in files:
                if name == self.jsonName:  # find the json file that relates to the pdf page (image) under consideration
                    scaleFlag=False
                    spotList = []
                    dupList = []
                    with open(os.path.join(fileLocation, self.jsonName), errors='ignore') as jsonFile:
                        data = json.load(jsonFile)

                    for region in data['regions']:
                        if region['id'] == regionID:
                            imageTop = region['boundingBox']['top']  # find out the starting point (top left) of the photo under consideration
                            imageLeft = region['boundingBox']['left']
                            imageWidth = region['boundingBox']['width']
                            imageHeight = region['boundingBox']['height']
                            imageDimensions = str(imageTop) + ',' + str(imageLeft) + ',' + str(
                                imageTop + region['boundingBox']['width']) + ',' + str(
                                imageLeft + region['boundingBox']['height'])  # record those photo dimensions for use later
                        if region['tags'][0] == 'SPOT' and region['type'] == 'POINT':  # this will look for all spots in the pdf page, regardless of whether or not they are actually on the cropped image under consideration
                            spot = True
                            x = region['points'][0]['x']
                            y = region['points'][0]['y']
                            spotID = region['id']
                            newX = x - imageLeft
                            newY = y - imageTop
                            #print('spotID: ', spotID, ' | x: ', x, ' | y: ', y, ' | newX: ', newX, ' | newY: ', newY)
                            if x >= imageLeft:
                                if x <= imageLeft+imageWidth:
                                    if y >= imageTop:
                                        if y <= imageTop+imageHeight:
                                            spotList.append([newX, newY, spotID])
                        if region['type'] == 'SCALE':  # this will look for all scales (there should only be 1) on the pdf page, regardless of whether or not they are actually on the cropped image under consideration
                            delta_x = abs(region['points'][0]['x'] - region['points'][1]['x'])  # diff in x between THIS node and other nodes
                            delta_y = abs(region['points'][0]['y'] - region['points'][1]['y'])  # diff in y between THIS node and other nodes
                            distance = math.sqrt((delta_x ** 2) + (delta_y ** 2))  # pixel distance, equivalent to 100 microns
                            scaleFlag = True
                            micPix = 100 / distance
                        if region['type'] == 'RECTANGLE' and region['tags'][0] == 'SPOT':  # this will look for all rectanglular scales on the pdf page, regardless of whether or not they are actually on the cropped image under consideration
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
                            #('rectangle scale detected')
                            scaleFlag = True
                            micPix = 30 / getScale(name, path, 'SPOT')
                            #print('micron per pixel: ', micPix)
                        if region['type'] == 'RECTANGLE' and region['tags'][0] == 'DUPLICATE':
                            x = region['boundingBox']['left'] + (region['boundingBox']['width'] / 2)
                            y = region['boundingBox']['top'] + (region['boundingBox']['height'] / 2)
                            newX = x - imageLeft
                            newY = y - imageTop
                            if x > imageLeft and x < imageLeft + imageWidth:
                                if y > imageTop and y < imageTop + imageHeight:
                                    dupList.append([newX, newY])
                    if spot == False:
                        print('No spot in image')

                    if scaleFlag == False  or micPix<0:
                        scale = getScale(name, path, 'SPOT')
                        if scale == -1:
                            self.error_message_text = 'No scale available in sample'
                            self.open_error_message_popup_window()
                            return
                        else:
                            micPix = 30 / scale

        #here we remove all those grains that were tagged as duplicates in the json file
        for duplicate in dupList:
            label = self.threshold[int(duplicate[1]), int(duplicate[0])]
            if label != 0:
                self.threshold[self.threshold == label] = 0

        self.contourList = {}
        contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE, cv2.RETR_EXTERNAL
        props = regionprops(self.threshold)

        # These are my lists:
        sampleid_List = []
        regionid_List = []  # unique code coming from VOTT, per image
        centroid_List = []  # centroid of grain
        label_List = []  # this  records the   number assigned to a region by scimage (i.e. the region label)
        spots_per_grain_List = []  # this will record the analytical spots per region
        area_List = [] #areas of grains
        equivalent_diameter_List = []
        perimeter_List = []
        minor_axis_length_List = []
        major_axis_length_List = []
        solidity_List = []
        convex_area_List = []
        solidityImageJ_List = []
        formFactor_List = []
        roundness_List = []
        compactness_List = []
        aspectRatio_List = []
        solidity_List = []
        effectiveDiameter_List = []
        maxFeret_List = []
        minFeret_List = []
        contour_List = []
        maskImage_List = []
        imDimensions_List = []

        # Get the values and write to my lists:
        for x in range(0, len(props)):
            centroid = props[x].centroid
            label = props[x].label
            area = props[x].area * (micPix ** 2)
            equivalent_diameter = props[x].equivalent_diameter * micPix
            perimeter = props[x].perimeter * micPix
            minor_axis_length = props[x].minor_axis_length * micPix
            major_axis_length = props[x].major_axis_length * micPix
            solidity = props[x].solidity
            convex_area = props[x].convex_area * (micPix ** 2)
            formFactor = (4 * math.pi * area) / (perimeter ** 2)
            # solidity = area/convex_area
            roundness = (4 * area) / (math.pi * (major_axis_length ** 2))
            compactness = (math.sqrt((4 / math.pi) * area) / major_axis_length)
            aspectRatio = major_axis_length / minor_axis_length
            maxFeret, minFeret = feret_diameter(props[x].convex_image)  # Convex image is good enough because it'll give us the max points and min edges for maxFeret and minFeret

            # now find which contour belongs to which region. Also find out which spots lie in the contour:
            for contour in contoursFinal:
                polygon = Polygon(np.squeeze(contour))  # create a shapely polygon
                representative_point = polygon.representative_point()  # using the shapely polygon, get a point inside the polygon
                region_label = self.threshold[int(representative_point.y), int(representative_point.x)]  # get the region label at the representative point
                if region_label == label:  # is this boundary around the region in question?
                    contour_List.append(np.squeeze(contour).tolist())
                    spots = []
                    boundary = matplotlib.path.Path(np.squeeze(contour), closed=True)
                    for spot in spotList:
                        spotInside = boundary.contains_point([spot[0], spot[1]])
                        if spotInside == True:
                            spots.append(spot[2])  # a grain may have more than 1 spot associated with it. Find all spots associated with the grain
                    if spots != []:
                        spots_per_grain_List.append(','.join(spots))  # write all associated spots to the list.
                    else:
                        spots_per_grain_List.append('')  # if there are not spots in the grain, record empty.

            sampleid_List.append(sampleid)
            regionid_List.append(regionID)
            label_List.append(label)
            area_List.append(area)
            centroid_List.append(centroid)
            equivalent_diameter_List.append(equivalent_diameter)
            perimeter_List.append(perimeter)
            minor_axis_length_List.append(minor_axis_length)
            major_axis_length_List.append(major_axis_length)
            convex_area_List.append(convex_area)
            formFactor_List.append(formFactor)
            roundness_List.append(roundness)
            solidity_List.append(solidity)
            compactness_List.append(compactness)
            aspectRatio_List.append(aspectRatio)
            maxFeret_List.append(maxFeret)
            minFeret_List.append(minFeret)
            imDimensions_List.append(imageDimensions)
            if self.maskPath != '':
                maskImage_List.append(self.maskPath)  # path is defined in the previous code block. This  is where image2 is saved. It's a file path.
            elif self.File_Location.get() != '':
                maskImage_List.append(self.File_Location.get())
            elif self.ProcessFolderFlag == True:
                maskImage_List.append(self.currentMask)

        if self.Current_Image == 'TL' and self.TLPath.get() !='':
            img_to_display = cv2.imread(self.TLPath.get())
        elif self.Current_Image == 'RL' and self.RLPath.get() !='':
            img_to_display = cv2.imread(self.RLPath.get())
        else:
            self.threshold[self.threshold>0]=255
            img_to_display = np.stack((self.threshold,)*3, axis=-1)

        for i in range(len(label_List)):
            img_to_display = cv2.circle(img_to_display, (int(centroid_List[i][1]), int(centroid_List[i][0])), 3, (0, 0, 255), 2)
            cv2.putText(img_to_display, str(label_List[i]), (int(centroid_List[i][1]), int(centroid_List[i][0])), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255))

        for duplicate in dupList:
            img_to_display = cv2.circle(img_to_display, (int(duplicate[0]), int(duplicate[1])), 3, (255, 255, 255), 2)
            cv2.putText(img_to_display, 'Duplicate', (int(duplicate[0]) + 5, int(duplicate[1]) + 5), cv2.FONT_HERSHEY_DUPLEX,0.5, (255, 255, 255))

        image_pill = Image.fromarray(img_to_display)
        self.img = ImageTk.PhotoImage(image = image_pill)

        self.myCanvas.delete('all')
        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        #now draw the grain boundaries on
        count_contour = 0
        for i in range(len(label_List)):
            groupID ='extcont_'+str(count_contour)
            uniqueID='extcont_'+str(count_contour)
            squeeze = np.squeeze(contoursFinal[i])
            self.contourList[uniqueID]=squeeze
            poly_coords = []
            for coords in squeeze:
                poly_coords.append(coords[0])
                poly_coords.append(coords[1])
            self.myCanvas.create_polygon(poly_coords, fill='', outline='red', activeoutline='yellow', width=3,tags=(groupID, uniqueID))
            count_contour += 1
        for spot in spotList:
            spotX = spot[0]
            spotY = spot[1]
            spotID = spot[2]
            self.myCanvas.create_oval(spotX-6,spotY-6, spotX+6, spotY+6, fill='lightgreen',outline='green', width=2, activefill='yellow', activeoutline='yellow', tags=('s_'+str(spotID), 'spot_'+str(spotID)))
            self.myCanvas.create_text(spotX-10,spotY-10,fill='green', text=spotID, tags=('s_'+str(spotID), 'spotno_'+str(spotID)))

        # Create a pandas table for all these elements:
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
        micPix=None

    def binariseImages(self):
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
        contours, hierarchy = cv2.findContours(self.threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE, cv2.RETR_EXTERNAL
        self.myCanvas.delete('all')
        image_pill = Image.fromarray(imCopy)
        self.img = ImageTk.PhotoImage(image=image_pill)
        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        areaList=[]
        count_contour = 0
        for cnt in contours:
            uniqueID = 'contour_'+str(count_contour)
            groupID = 'contour_'+str(count_contour)
            if len(cnt) < 3:
                pass
            else:
                contArea = cv2.contourArea(cnt, False)

                if contArea == 0:  # if it's not a closed contour
                    pass
                elif contArea < 50:  # in some cases we may want to exclude very small shapes, too...this value might be  case dependent
                    pass
                else:
                    areaList.append(contArea)
                    squeeze = np.squeeze(cnt)
                    poly_coords=[]
                    for coords in squeeze:
                        poly_coords.append(coords[0])
                        poly_coords.append(coords[1])
                    self.myCanvas.create_polygon(poly_coords, fill='', outline='red', activeoutline='yellow', width=2,tags=(groupID, uniqueID))
                    self.contourList[uniqueID]=squeeze
            count_contour += 1

    def convert_contours_to_mask_image(self):
        mask = np.zeros((self.height, self.width), dtype=np.uint8)
        for contour in self.contourList:
            x, y = zip(*self.contourList[contour])
            newXY = list(zip(y, x))
            contMask = skimage.draw.polygon2mask((mask.shape[0], mask.shape[1]), newXY)
            skimage.segmentation.expand_labels(contMask,1)
            mask = mask + contMask
            mask[mask == 2] = 0
        return mask

    def erode_small_artifacts(self,mask):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9, 9))  # this large structuring element is designed to  remove bubble rims
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        opening[opening == 1] = 255
        opening_uint8 = opening.astype('uint8')
        self.threshold = opening_uint8


    def Separate(self):
        reconstructed_points = [] #for testing
        self.threshold = self.convert_contours_to_mask_image()
        #self.erode_small_artifacts(mask)

        contours, hierarchy = cv2.findContours(self.threshold, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)  # get the new contours of the eroded masks
        hierarchy = np.squeeze(hierarchy)

        composite_contour_list = []
        for i in range(len(contours)):
            cnt = np.squeeze(contours[i]).tolist()
            composite_contour = CompositeContour(np.squeeze(contours[i]),i)
            if hierarchy.ndim == 1:
                if hierarchy[3] == -1:
                    composite_contour.has_parent = False
                else:
                    composite_contour.has_parent = True
            else:
                if hierarchy[i][3] == -1:
                    composite_contour.has_parent = False
                else:
                    composite_contour.has_parent = True

            if len(cnt) < 3: #if it is a straight line or a point, it is not a closed contour and thus not of interest
                composite_contour.keep_contour = False
            else:
                composite_contour.coefficients,composite_contour.locus, composite_contour.reconstructed_points,composite_contour.keep_contour = GetCoefficients(composite_contour.original_points,composite_contour.has_parent)

                if composite_contour.keep_contour == False:
                    continue
                composite_contour.curvature_values, composite_contour.cumulative_distance = calculateK(composite_contour.reconstructed_points, composite_contour.coefficients) #composite_contour.reconstructed_points
                curvature_maxima_length_positions, curvature_maxima_values, curvature_maxima_x, curvature_maxima_y, non_maxima_curvature = FindCurvatureMaxima(composite_contour.curvature_values,composite_contour.cumulative_distance,composite_contour.reconstructed_points)
                node_curvature_values, node_distance_values, node_x, node_y = IdentifyContactPoints(curvature_maxima_length_positions, curvature_maxima_values, curvature_maxima_x, curvature_maxima_y, non_maxima_curvature)
                if node_curvature_values != []:
                    composite_contour.max_curvature_values = node_curvature_values
                else:
                    composite_contour.keep_contour = False

                if node_x !=[] and node_y !=[]:
                    composite_contour.max_curvature_coordinates = list(zip(node_x,node_y))
                else:
                    composite_contour.keep_contour = False

            composite_contour_list.append(composite_contour)
        groups = FindNestedContours(hierarchy)

        dpi = 100
        fig = plt.figure(figsize=(self.width / dpi, self.height / dpi))
        ax = fig.add_axes([0, 0, 1, 1])
        canvas = FigureCanvasAgg(fig)
        plt.margins(0, 0)
        plt.axis('off')
        if self.TLPath.get() != '':
            imgTL = cv2.imread(self.TLPath.get())
            plt.imshow(imgTL, cmap='Greys_r')
        plt.imshow(self.threshold, cmap='jet', alpha=0.5)
        for contour in composite_contour_list:
            if contour.keep_contour == False:
                continue
            x, y = zip(*contour.reconstructed_points)
            plt.scatter(x, y, c=contour.curvature_values, vmin=-1, vmax=1, s=5)
            xmax,ymax = zip(*contour.max_curvature_coordinates)
            #for i in range (len(xmax)):
            #    text= str(xmax[i])+" | "+str(ymax[i])
             #   plt.text(xmax[i]+1,ymax[i]+3,c = 'red', s=text, size="medium")

            plt.scatter(xmax,ymax,facecolors='none',edgecolors='red',s=10,linewidth=1)
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        canvas_data, (canvas_width,canvas_height) = canvas.print_to_buffer()  # taken from here: https://matplotlib.org/3.1.1/gallery/user_interfaces/canvasagg.html
        image_matrix = np.frombuffer(canvas_data, np.uint8).reshape((canvas_height, canvas_width, 4))
        image_pill = Image.frombytes("RGBA", (canvas_width, canvas_height), image_matrix)
        self.img = ImageTk.PhotoImage(image=image_pill)
        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        # now link all nodes within the groups:
        for group in groups:
            # get the contours that are relevant to the group in question:
            contour_group = []
            for index in group:
                for contour in composite_contour_list:
                    if contour.index == index and contour.keep_contour == True:  # watch out, what if the parent contour is removed?
                        contour_group.append(contour)
                        composite_contour_list.remove(contour)  # if it's added to a group to be processed, remove it from the main group so that we don't have to include it in future loops
            if contour_group == []:
                continue
            pairs = linkNodes(contour_group)
            matplotlib.use('Agg')
            for p in pairs:
                x1 = p[0][0]
                y1 = p[0][1]
                x2 = p[1][0]
                y2 = p[1][1]
                self.pairsList.append([(x1, y1), (x2, y2)])
                ID = 'line_' + str(self.count)
                self.count += 1
                self.myCanvas.create_line(x1, y1, x2, y2, width=3, fill='red', activefill='yellow', tags=(ID))

    def onClick(self, event):
        thisSpot = event.widget.find_withtag('current')[0]
        all_IDs = self.myCanvas.find_withtag(self.thisSpotID)
        self.thisSpotID = self.myCanvas.gettags(thisSpot)[0]
        for ID in all_IDs:
            if not ID == thisSpot:
                self.labelID = ID
                self.myCanvas.itemconfig(self.labelID, state=tk.HIDDEN)

        self.spotCaptureWindow = Toplevel(root)
        self.spotCaptureWindow.title("Capture Spot Number")
        self.spotCaptureWindow.minsize(300, 100)

        self.spotCaptureLabel = Label(self.spotCaptureWindow, text="Spot Number")
        self.spotCaptureLabel.grid(column=0, row=0)

        self.currentSpotNumber = tk.StringVar()
        self.currentSpotTextBox = Entry(self.spotCaptureWindow, width=20, textvariable=self.currentSpotNumber)
        self.currentSpotTextBox.grid(column=1, row=0)
        self.currentSpotTextBox.focus()

        self.saveSpotNo = Button(self.spotCaptureWindow, text='Save', command=self.Save)
        self.spotCaptureWindow.bind('<Return>', lambda e: self.Save())
        self.saveSpotNo.grid(column=0, row=1, pady=5)

    def DisplayImages(self):
        #This is for cycling through images associated with json files when capturing spots
        result = True
        self.myCanvas.delete('all')
        im = ''
        jf = ''

        if self.imgCount < len(self.jsonList) and self.imgCount > -1:
            self.image_iterator_current = self.jsonList[self.imgCount]
            im = self.image_iterator_current[1]
            jf = self.image_iterator_current[0]
            pattern = r"_p[0-9]{1,2}.png"

            self.currentSample = im.split("_")[0]
            #re.sub(pattern, "",im)  # don't remove this. This tracks the sample number and is used for tracking unique sample id's per sample
            iterator = self.sampleList.index(self.currentSample) + 1
            fileName = os.path.join(self.folderPath, im)
            self.img = ImageTk.PhotoImage(Image.open(fileName))
            self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
            self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")
            self.label['text'] = im + '  | Sample ' + str(iterator) + ' of ' + str(len(self.sampleList))
        else:
            result = False
            return result

        with open(os.path.join(self.folderPath, jf), errors='ignore') as jsonFile:
            data = json.load(jsonFile)
            for region in data['regions']:
                if region['tags'][0] == 'SPOT AREA' and region['type'] == 'RECTANGLE':
                    self.spotCount += 1
                    spotID = region['id']
                    x1 = region['points'][0]['x']
                    y1 = region['points'][0]['y']
                    x2 = region['points'][1]['x']
                    y2 = region['points'][2]['y']
                    self.myCanvas.create_rectangle(x1, y1, x2, y2, width=3, outline='blue', activefill='yellow',
                                                   activeoutline='yellow', tags=(spotID, 'spot' + str(self.spotCount)))
                    self.myCanvas.create_text(x1, y1 - 15, text="Spot area", fill='blue', font=("Helvetica", 12, "bold"),tags=spotID)
                    self.myCanvas.tag_bind('spot' + str(self.spotCount), '<ButtonPress-1>', self.onClick)

                if region['tags'][0] == 'DUPLICATE' and region['type'] == 'RECTANGLE':
                    self.spotCount += 1
                    spotID = region['id']
                    x1 = region['points'][0]['x']
                    y1 = region['points'][0]['y']
                    x2 = region['points'][1]['x']
                    y2 = region['points'][2]['y']
                    self.myCanvas.create_rectangle(x1, y1, x2, y2, width=3, outline='red', activefill='yellow',
                                                   activeoutline='yellow',
                                                   tags=(spotID, 'DUPLICATE' + str(self.spotCount)))
                    self.myCanvas.create_text(x1, y1 - 15, text="Duplicate", fill='red', font=("Helvetica", 12, "bold"),
                                              tags=spotID)
                    self.myCanvas.tag_bind('DUPLICATE' + str(self.spotCount), '<ButtonPress-1>', self.onClick)

                if region['tags'][0] == 'SPOT' and region['type'] == 'POINT':
                    self.spotCount += 1
                    spotID = region['id']
                    x1 = region['points'][0]['x']
                    y1 = region['points'][0]['y']
                    self.myCanvas.create_oval(x1 - 6, y1 - 6, x1 + 6, y1 + 6, width=4, outline='blue', fill='blue',
                                              activefill='yellow', activeoutline='yellow',
                                              tags=(spotID, 'SpotPoint' + str(self.spotCount)))
                    self.myCanvas.create_text(x1, y1 - 15, text=spotID, fill='blue', font=("Helvetica", 12, "bold"),tags=spotID)
                    self.myCanvas.tag_bind('spot' + str(self.spotCount), '<ButtonPress-1>', self.onClick)

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
                    self.myCanvas.create_polygon(polyCoords, fill='', outline='red', activeoutline='yellow', width=1,
                                                 tags=(groupID, uniqueID))
                    self.allPolys[uniqueID] = idCoordList

                if region['tags'][0] == 'SCALE':
                    self.spotCount += 1
                    ID = region['id']
                    x1 = region['points'][0]['x']
                    y1 = region['points'][0]['y']
                    x2 = region['points'][1]['x']
                    y2 = region['points'][1]['y']
                    self.myCanvas.create_line(x1, y1, x2, y2, width=3, fill='red', activefill='yellow',
                                              tags=(ID, 'newScale' + str(self.spotCount)))
                    # self.myCanvas.tag_bind(ID,'<ButtonPress-1>', self.onClick)

    def Load_Image(self,image_to_display):
        #This is for optionally loading either the TL or RL image
        self.myCanvas.delete('all')
        image_pill=None
        if image_to_display == 0:
            self.Current_Image = 'RL'
            fileRL = self.RLPath.get()
            if fileRL == '':
                self.error_message_text = "No reflected light image has been selected"
                self.open_error_message_popup_window()
                return
            img = cv2.imread(fileRL)
            self.width = img.shape[1]
            self.height = img.shape[0]
            image_pill = Image.fromarray(img)
        if image_to_display == 1:
            self.Current_Image = 'TL'
            fileTL = self.TLPath.get()
            if fileTL == '':
                self.error_message_text = "No transmitted light image has been selected"
                self.open_error_message_popup_window()
                return
            img = cv2.imread(fileTL)
            self.width = img.shape[1]
            self.height = img.shape[0]
            image_pill = Image.fromarray(img)

        self.img = ImageTk.PhotoImage(image=image_pill)
        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        self.Draw_Contours()

    def Draw_Contours(self):
        # paint the contours on
        #contoursFinal, hierarchyFinal = cv2.findContours(self.threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #count_contour = 0

        for key,value in self.contourList.items():
            poly_coords = []
            uniqueID = key
            groupID = key
            if len(value) == 1:
                pass
            else:
                for coords in value:
                    poly_coords.append(coords[0])
                    poly_coords.append(coords[1])
                self.myCanvas.create_polygon(poly_coords, fill='', outline='red', activeoutline='yellow', width=3,tags=(groupID, uniqueID))
        #for i in range(len(contoursFinal)):
            #groupID = 'extcont_' + str(count_contour)
            #uniqueID = 'extcont_' + str(count_contour)
            #squeeze = np.squeeze(contoursFinal[i])
            #self.contourList[uniqueID] = squeeze
            #poly_coords = []
           # for coords in squeeze:
           #     poly_coords.append(coords[0])
           #     poly_coords.append(coords[1])
            #self.myCanvas.create_polygon(poly_coords, fill='', outline='red', activeoutline='yellow', width=3,
           #                              tags=(groupID, uniqueID))
            #count_contour += 1

root = Tk()
my_gui = Application(root)
root.mainloop()
