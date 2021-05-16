import tkinter as tk
import uuid
from tkinter import *
from tkinter.ttk import *

import PIL
from PIL import ImageTk

from src.model.drawing_objects.spot import Spot


class Drawing():
    def __init__(self,frame,model,view):
        self.model = model
        self.view = view
        self.myFrame=frame
        self.myCanvas = Canvas(self.myFrame, bg="white")
        self.vScroll = Scrollbar(self.myFrame, orient='vertical', command=self.myCanvas.yview)
        self.hScroll = Scrollbar(self.myFrame, orient='horizontal', command=self.myCanvas.xview)
        self.vScroll.pack(side=RIGHT, fill=Y)
        self.hScroll.pack(side=BOTTOM, fill=X)
        self.myCanvas.configure(yscrollcommand=self.vScroll.set)
        self.myCanvas.configure(xscrollcommand=self.hScroll.set)
        self.myCanvas.bind("<Button-3>", self.DeleteObject)
        self.myCanvas.pack(side=LEFT, expand=True, fill=BOTH)
        self.myCanvas.bind_all("<MouseWheel>", self.ScrollWithMouseWheel)

        self.currentImage = None

        # variables for drawing
        self.uniqueTag = None
        self.groupTag = None
        self.lineStart_y = None  # used for drawing a scale line
        self.lineStart_x = None  # used for drawing a scale line
        self.Type = None
        self.updatedX = None #as the user draws, the x coordinate will constantly update
        self.updatedY = None #as the user draws, the y coordinate will constantly update
        self.scaleLine = None
        self.imgCount = 0
        self.rectangleType = None

    def DeleteObject(self, event):
        thisObj = event.widget.find_withtag('current')[0]  # get the object clicked on
        thisObjID = self.myCanvas.gettags(thisObj)[0]  # find the groupID for the object clicked on
        coords = self.myCanvas.coords(thisObjID)
        self.myCanvas.delete(thisObjID)  # delete everything with the same groupID
        self.model.DeleteObject(thisObjID,coords) #pass the groupID and coordinates to the model, where everything else is handled

    def ScrollWithMouseWheel(self, event):
        self.myCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def open_save_spot_dialog(self, spot, is_new_spot):
        self.spotCaptureWindow = Toplevel(self.view.master)
        self.spotCaptureWindow.title("Capture Spot Number")
        self.spotCaptureWindow.minsize(300, 100)
        self.spotCaptureLabel = Label(self.spotCaptureWindow, text='Spot ID')
        self.spotCaptureLabel.grid(column=0, row=0)
        self.currentSpotNumber = tk.StringVar()
        self.currentSpotNumber.set('')
        self.currentSpotTextBox = Entry(self.spotCaptureWindow, width=20, textvariable=self.currentSpotNumber)
        self.currentSpotTextBox.grid(column=1, row=0)
        self.currentSpotTextBox.focus()

        def save_spot():
            spotNo = self.currentSpotNumber.get()
            userText = spotNo.strip()
            '''try:
                testNum = float(userText)
            except:
                self.error_message_text = "Non-numeric spot number"
                self.open_error_message_popup_window()
                return None'''
            try:
                if is_new_spot:
                    spot.group_tag = userText
                    self.model.add_new_spot(spot)
                else:
                    self.model.update_spot_id(spot, userText)
            except Exception as e:
                self.view.open_error_message_popup_window(str(e))
                return None

            self.myCanvas.itemconfig(spot.unique_text_tag, text=userText, state=tk.NORMAL, tags=spot.get_text_tags())
            self.myCanvas.itemconfig(spot.unique_tag, tags=spot.get_tags())
            self.currentSpotTextBox.delete(first=0, last=100)
            self.spotCaptureWindow.destroy()

        self.saveSpotNo = Button(self.spotCaptureWindow, text='Save', command=save_spot)
        self.spotCaptureWindow.bind('<Return>', lambda e: save_spot())
        self.saveSpotNo.grid(column=0, row=1, pady=5)

    def DrawScale(self):
        #this allows the user to draw a two-point line to capture a length scale which exists in some of the images
        self.myCanvas.unbind("<Button-1>")  # unbind the spot digitisation
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<ButtonPress-1>", self.LineStart)
        self.myCanvas.bind("<B1-Motion>", self.LineDraw)
        self.myCanvas.bind("<ButtonRelease-1>", self.finish_scale)

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

    def finish_scale(self,mouse_event):
        self.model.save_scale_to_json(self.uniqueTag,self.lineStart_x,self.lineStart_y,self.updatedX, self.updatedY)
        self.scaleLine = None

    def DupDraw(self):
        self.rectangleType = 'DUPLICATE'
        self.RectDraw()

    def BoundaryDraw(self):
        self.myCanvas.unbind("<Button-1>")  # unbind the spot digitisation
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<ButtonPress-1>", self.add_polygon_vertex)
        self.myCanvas.bind("<ButtonPress-2>", self.PolyComplete)

        uniqueCode = str(datetime.datetime.now())
        self.groupTag = 'boundary' + uniqueCode  # polygon and points(ovals)will have the same group tag
        self.uniqueTag = 'poly' + uniqueCode  # only the polygon gets the unique id
        self.Type = "POLYGON"

    def add_polygon_vertex(self, polyDrawEvent):
        self.x0 = self.myCanvas.canvasx(polyDrawEvent.x)
        self.y0 = self.myCanvas.canvasy(polyDrawEvent.y)
        self.model.add_polygon_vertex(self.x0,self.y0,self.uniqueTag, self.groupTag)

    def draw_polygon(self,polygon):
        coords = []  # used locally to collate all xy's
        coords=polygon.flatten_coordinates()
        size = polygon.size()
        tags = polygon.groupTag, polygon.uniqueTag
        if size<2:
            return # if there is only one point, don't draw any lines.

        self.myCanvas.delete(self.uniqueTag)  # delete all pre-existing lines and redraw
        if size > 2:
            self.myCanvas.create_polygon(coords, fill='', outline='red', activeoutline='yellow', width=1,tags=tags)  # redraw,now includes the added point
        else:
            self.myCanvas.create_line(coords, fill='red', activefill='yellow', width=1, tags=tags)  # if there are only two points, its a line not a polygon

    def PolyComplete(self, event):
        self.myCanvas.unbind("<ButtonPress-2>")  # unbind from polygon digitisation
        self.model.complete_polygon(self.uniqueTag)

    def display_image(self, image):
        self.myCanvas.delete('all')
        tk_img = ImageTk.PhotoImage(image=image)
        self.myCanvas.configure(scrollregion=[0, 0, tk_img.width(), tk_img.height()])
        self.myCanvas.create_image(0, 0, image=tk_img, anchor=NW, tags="Image")
        self.currentImage = tk_img

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

        self.model.update_spot_in_json_file(self.spotID,self.x0,self.y0)

        self.uniqueTag = None
        self.groupTag = None
        self.spotID = ''

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

        self.save_rectangle_to_json(self.rectStart_x, self.rectStart_y, self.updatedX, self.updatedY,self.rectangleType,self.uniqueTag)

    def capture_spot(self, drawSpotEvent):
        x0 = self.myCanvas.canvasx(drawSpotEvent.x)
        y0 = self.myCanvas.canvasy(drawSpotEvent.y)
        groupTag = 'NewSpot_'+str(uuid.uuid4())
        this_spot = Spot(x0,y0, groupTag)
        self.draw_interactive_spot(this_spot,'blue')
        self.open_save_spot_dialog(this_spot, True)

    def UnbindMouse(self):
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<Button-1>")  # unbind point digitisation

    def start_spot_capture(self):
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<Button-1>", self.capture_spot)

    def DrawBreakLine(self):
        # print('DrawScale')
        self.myCanvas.unbind("<Button-1>")
        self.myCanvas.unbind("<ButtonPress-1>")
        self.myCanvas.unbind("<B1-Motion>")
        self.myCanvas.unbind("<ButtonRelease-1>")
        self.myCanvas.bind("<ButtonPress-1>", self.BreakLineStart)
        self.myCanvas.bind("<B1-Motion>", self.BreakLineUpdate)
        self.myCanvas.bind("<ButtonRelease-1>", self.finish_breakline())

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

    def finish_breakline(self,mouse_event):
        self.model.insert_new_breakline_to_pairslist(self.lineStart_x, self.lineStart_y, self.updatedX, self.updatedY)

    def Draw_Contours(self):
        for key, contour_polygon in self.contourList.items():
            if contour_polygon.size() == 1:
                pass
            self.myCanvas.create_polygon(contour_polygon.flattened_coordinates(), fill='', outline='red', activeoutline='yellow', width=1,
                                         tags=(contour_polygon.groupTag, contour_polygon.uniqueTag))

    def display_spots_during_measurement(self,spotList):

        for spot in spotList:
            spotX = spot[0]
            spotY = spot[1]
            spotID = spot[2]
            self.myCanvas.create_oval(spotX-5,spotY-5, spotX+5, spotY+5, fill='lightgreen',outline='green', width=1, activefill='yellow', activeoutline='yellow', tags=('s_'+str(spotID), 'spot_'+str(spotID)))
            self.myCanvas.create_text(spotX-7,spotY-7,fill='green', text=spotID, tags=('s_'+str(spotID), 'spotno_'+str(spotID)))


    def plot_kvalues_on_grain_image(self, underlying_image, is_binary_image, composite_contour_list):
        dpi = 100
        fig = plt.figure(figsize=(self.width / dpi, self.height / dpi))
        ax = fig.add_axes([0, 0, 1, 1])
        matplotlib.use('Agg')
        canvas = FigureCanvasAgg(fig)
        plt.margins(0, 0)
        plt.axis('off')

        if not is_binary_image:
            plt.imshow(underlying_image, cmap='jet', alpha=0.5)
        else:
            plt.imshow(underlying_image, cmap='Greys_r')

        for contour in composite_contour_list:
            if contour.keep_contour == False:
                continue
            x, y = zip(*contour.reconstructed_points)
            plt.scatter(x, y, c=contour.curvature_values, vmin=-1, vmax=1, s=5)
            xmax,ymax = zip(*contour.max_curvature_coordinates)
            #for i in range (len(xmax)):
            #    text= str(xmax[i])+" | "+str(ymax[i])
             #   plt.text(xmax[i]+1,ymax[i]+3,c = 'red', s=text, size="medium")

            sc=plt.scatter(xmax,ymax,facecolors='none',edgecolors='red',s=7,linewidth=1)
            #cbaxis = fig.add_axes([0.9,0.1,0.03,0.8])
            #cbar = plt.colorbar(sc, cax=cbaxis)
            #cbar.set_label('Curvature (K)', rotation=270, labelpad=20)
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

        canvas_data, (canvas_width,canvas_height) = canvas.print_to_buffer()  # taken from here: https://matplotlib.org/3.1.1/gallery/user_interfaces/canvasagg.html
        image_matrix = np.frombuffer(canvas_data, np.uint8).reshape((canvas_height, canvas_width, 4))
        image_pill = Image.frombytes("RGBA", (canvas_width, canvas_height), image_matrix)
        self.drawing.display_image(image_pill)

    def draw_image_data(self, image_data):
        for spot in image_data.spots:
            self.draw_interactive_spot(spot,'blue')

        for spot_area in image_data.spot_areas:
            self.draw_interactive_rectange(spot_area)

        for rectangle in image_data.unwanted_objects:
            self.draw_interactive_rectange(rectangle)

        if image_data.scale is not None:
            self.draw_interactive_scale(image_data.scale)

    def draw_breaklines(self, breaklines):
        for line in breaklines:
            self.myCanvas.create_line(line.x0, line.y0, line.x1, line.y1, width=2, fill='red', activefill='yellow', tags=line.tag)

    def draw_interactive_rectange(self, rectangle):
        self.myCanvas.create_rectangle(rectangle.x0, rectangle.y0, rectangle.x1, rectangle.y1, width=3, outline=rectangle.get_colour(), activefill='yellow',
                                       activeoutline='yellow',
                                       tags=rectangle.get_tags())
        self.myCanvas.create_text(rectangle.x0, rectangle.y0 - 15, text=rectangle.type(), fill='red', font=("Helvetica", 12, "bold"),
                                  tags=rectangle.get_text_tags())

    def draw_interactive_spot(self, spot,colour):
        self.myCanvas.create_oval(spot.x0 - 6, spot.y0 - 6, spot.x0 + 6, spot.y0 + 6, width=2, outline=colour, fill=colour,
                                  activefill='yellow', activeoutline='yellow',
                                  tags=spot.get_tags())

        self.myCanvas.create_text(spot.x0, spot.y0 - 5, text=spot.group_tag, fill=colour, font=("Helvetica", 8, "bold"), tags=spot.get_text_tags())
        self.myCanvas.tag_bind(spot.unique_tag, '<ButtonPress-1>', self.view.create_spot_capture_dialog)

    def draw_interactive_scale(self, scale):
        self.myCanvas.create_line(scale.x0, scale.y0, scale.x1, scale.y1, width=3, fill='red', activefill='yellow',
                                  tags=scale.get_tags())
        # self.myCanvas.tag_bind(ID,'<ButtonPress-1>', self.onClick)