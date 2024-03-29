import tkinter as tk
import uuid
from datetime import datetime
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

import PIL
import shapely
from PIL import ImageTk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

from src.model.drawing_objects.breakline import Breakline
from src.model.drawing_objects.contour import Contour
from src.model.drawing_objects.rectangle import Rectangle, RectangleType
from src.model.drawing_objects.spot import Spot
import src.model.drawing_objects.scale as scale
from src.view.save_spot_dialog import SaveSpotDialog
from src.view.specify_region_type import RegionTypeDialog


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
        self.breakline = None
        self.displayed_image = None
        self.object_to_reposition= None #used for spot and unwanted object repositioning

    def DeleteObject(self, event):
        if len(event.widget.find_withtag('current'))==0:
            return
        thisObj = event.widget.find_withtag('current')[0]  # get the object clicked on
        tags = self.myCanvas.gettags(thisObj)  # find the groupID for the object clicked on
        group_tag = tags[0]
        if group_tag == 'Image':
            return
        self.myCanvas.delete(group_tag)  # delete everything with the same groupID
        self.model.DeleteObject(group_tag.replace('spot_','')) #pass the groupID and coordinates to the model, where everything else is handled

    def start_spot_review(self):
        self.myCanvas.unbind("<Button-1>")
        self.myCanvas.bind("<Button-1>", self.get_spot_review_info)

    def get_spot_review_info(self,event):
        thisObj = event.widget.find_withtag('current')[0]
        group_tag = self.myCanvas.gettags(thisObj)[0]
        unique_tag = self.myCanvas.gettags(thisObj)[1]
        if 'spot_' in group_tag:
            spot = self.model.get_spot_data(group_tag,unique_tag)
            is_new_spot = False
            spot_capture_dialog=SaveSpotDialog(self.view, self,spot, is_new_spot)
            self.myCanvas.wait_window(spot_capture_dialog.spotCaptureWindow)
            spot_tags = spot.get_tags()
            text_tags = spot.get_text_tags()
            self.myCanvas.itemconfig(spot.unique_text_tag, text=spot.group_tag.replace('spot_', ''), state=tk.NORMAL, tags=(text_tags[0], text_tags[1]))
            self.myCanvas.itemconfig(spot.unique_tag, tags=(spot_tags[0], spot_tags[1]))

            self.myCanvas.unbind("<Button-1>")
        else:
            tk.messagebox.showwarning(message = "Please select an analytical spot to review." )


    def ScrollWithMouseWheel(self, event):
        self.myCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def open_save_spot_dialog(self, spot, is_new_spot):
        self.spotCaptureWindow = Toplevel(self.view.master)
        self.spotCaptureWindow.title("Capture Spot Number")
        self.spotCaptureWindow.minsize(300, 100)

        self.spotCaptureLabel = Label(self.spotCaptureWindow, text='Spot ID')
        self.spotCaptureLabel.grid(column=0, row=0,padx=2, pady=2, sticky = 'EW')

        self.currentSpotNumber = tk.StringVar()
        self.currentSpotNumber.set('')
        self.note = tk.StringVar()
        self.note.set('')

        self.currentSpotTextBox = Entry(self.spotCaptureWindow, width=20, textvariable=self.currentSpotNumber)
        self.currentSpotTextBox.grid(column=1, row=0,padx=2, pady=2, sticky = 'W')
        self.currentSpotTextBox.focus()

        #Added to address reviewer comments: CL texture
        self.CL_texture_label = Label(self.spotCaptureWindow, text='CL texture')
        self.CL_texture_label.grid(column=0, row=1,padx=2, pady=2, sticky = 'W')
        self.CL_texture_combobox = Combobox(self.spotCaptureWindow,width=20,values=['homogenous',
                                                                                    'oscillitory',
                                                                                    'patchy',
                                                                                    'sector',
                                                                                    'other'])
        self.CL_texture_combobox.grid(column=1,row=1,padx=2, pady=2, sticky = 'W')

        # Added to address reviewer comments: Freeform notes:
        self.notes_label = Label(self.spotCaptureWindow, text='Comments:', width = 50)
        self.notes_label.grid(column=0, row=2,padx=2, pady=2,sticky ='W')
        self.notes_textbox = Entry(self.spotCaptureWindow,textvariable=self.note)
        self.notes_textbox.grid(column=1, row=2,padx=2, pady=2,sticky ='W')

        def save_spot():
            spotNo = self.currentSpotNumber.get()
            cl_texture = self.CL_texture_combobox.get()
            notes = self.notes_textbox.get().strip()
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
                    spot.cl_texture =  cl_texture
                    spot.notes = notes
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

        self.saveSpotNo = Button(self.spotCaptureWindow, text='Save', command=save_spot, width =10)
        self.spotCaptureWindow.bind('<Return>', lambda e: save_spot())
        self.saveSpotNo.grid(column=1, row=3, padx=2, pady=2, sticky ='W')

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
        groupTag = 'scale' +str(uuid.uuid4())
        lineStart_x = self.myCanvas.canvasx(event.x)
        lineStart_y = self.myCanvas.canvasy(event.y)
        self.scaleLine= scale.Scale(lineStart_x,lineStart_y,lineStart_x+1,lineStart_y+1,groupTag)
        self.draw_interactive_scale(self.scaleLine)

    def LineDraw(self, moveEvent):
        self.scaleLine.x1 = self.myCanvas.canvasx(moveEvent.x)
        self.scaleLine.y1 =  self.myCanvas.canvasy(moveEvent.y)
        self.myCanvas.coords(self.scaleLine.unique_tag, self.scaleLine.x0, self.scaleLine.y0, self.scaleLine.x1, self.scaleLine.y1)

    def finish_scale(self,mouse_event):
        self.view.get_real_world_distance_for_scale(self.scaleLine)
        self.scaleLine = None

    def DupDraw(self):
        self.rectangleType = RectangleType.DUPLICATE
        self.RectDraw()

    def BoundaryDraw(self):
        self.myCanvas.unbind("<Button-1>")  # unbind the spot digitisation
        self.myCanvas.unbind("<ButtonPress-1>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonPress-2>")
        self.myCanvas.unbind("<B1-Motion>")  # unbind rectangle digitisation
        self.myCanvas.unbind("<ButtonRelease-1>")  # unbind rectangle digitisation
        self.myCanvas.bind("<ButtonPress-1>", self.add_polygon_vertex)
        self.myCanvas.bind("<ButtonPress-2>", self.PolyComplete)

        groupTag = 'boundary' + str(uuid.uuid4())  # polygon and points(ovals)will have the same group tag
        self.contour = Contour(groupTag)

    def add_polygon_vertex(self, polyDrawEvent):
        x0 = self.myCanvas.canvasx(polyDrawEvent.x)
        y0 = self.myCanvas.canvasy(polyDrawEvent.y)
        self.contour.add_vertex(x0,y0)
        self.myCanvas.delete(self.contour.unique_tag)
        self.draw_contour(self.contour)

    def PolyComplete(self, event):
        self.myCanvas.unbind("<ButtonPress-2>")  # unbind from polygon digitisation
        new_polygon = self.model.add_new_contour(self.contour)
        self.view.SaveBreakChanges(new_polygon)
        self.myCanvas.bind("<ButtonPress-3>", self.DeleteObject)
        self.myCanvas.unbind("<ButtonPress-1>")
        self.contour = None

    def clear_canvas_and_display_image(self, image):
        self.myCanvas.delete('all')
        self.display_image(image)

    def display_image(self, image):
        tk_img = ImageTk.PhotoImage(image=image)
        self.myCanvas.configure(scrollregion=[0, 0, tk_img.width(), tk_img.height()])
        self.myCanvas.create_image(0, 0, image=tk_img, anchor=NW, tags="Image")
        self.myCanvas.tag_lower('Image')
        #This variable looks unused but must be kept so that the image is not garbage collected
        self.displayed_image  = tk_img

    def RepositionObject(self):
        self.myCanvas.bind("<Button-1>", self.StartRepositionObject)
        self.myCanvas.bind("<ButtonRelease-1>", self.FinishObjectMove)

    def StartRepositionObject(self, moveEvent):
        thisObj = moveEvent.widget.find_withtag('current')[0]
        unique_tag = self.myCanvas.gettags(thisObj)[1]


        self.myCanvas.bind("<ButtonRelease-1>", self.FinishObjectMove)

        if 'spot' in unique_tag:
            self.object_to_reposition = self.view.model.find_spot_in_measured_image_by_unique_tag(unique_tag)
            self.myCanvas.delete(self.object_to_reposition.unique_text_tag)
            self.myCanvas.bind("<B1-Motion>", self.UpdateObjectMove)
        if 'duplicate' in unique_tag:
            self.object_to_reposition = self.view.model.find_unwanted_object_in_measured_image_by_unique_tag(unique_tag)
            self.myCanvas.delete(self.object_to_reposition.unique_text_tag)
            self.myCanvas.bind("<B1-Motion>", self.UpdateObjectMove)

    def UpdateObjectMove(self, moveEvent):
        if 'spot_' in self.object_to_reposition.unique_tag:
            self.object_to_reposition.x0 = self.myCanvas.canvasx(moveEvent.x)
            self.object_to_reposition.y0 = self.myCanvas.canvasy(moveEvent.y)
            self.myCanvas.coords(self.object_to_reposition.unique_tag, self.object_to_reposition.x0 - 6, self.object_to_reposition.y0 - 6, self.object_to_reposition.x0 + 6, self.object_to_reposition.y0 + 6)
            self.myCanvas.coords(self.object_to_reposition.unique_text_tag, self.object_to_reposition.x0 - 7, self.object_to_reposition.y0 - 7)
        if 'duplicate_' in self.object_to_reposition.unique_tag:
            self.object_to_reposition.set_centroid(self.myCanvas.canvasx(moveEvent.x), self.myCanvas.canvasy(moveEvent.y))
            self.myCanvas.coords(self.object_to_reposition.unique_tag, self.object_to_reposition.x0, self.object_to_reposition.y0, self.object_to_reposition.x1, self.object_to_reposition.y1)
            self.myCanvas.coords(self.object_to_reposition.unique_text_tag, self.object_to_reposition.x0 - 7, self.object_to_reposition.y0 - 7)


    def FinishObjectMove(self, moveEvent):
        self.myCanvas.unbind("<B1-Motion>")
        self.myCanvas.unbind("<ButtonRelease-1>")
        self.myCanvas.unbind("<Button-1>")
        self.model.update_object_location_in_json_file(self.object_to_reposition)

        if 'spot_' in self.object_to_reposition.unique_tag:
            self.draw_text(self.object_to_reposition.get_text_tags(), self.object_to_reposition.x0 - 7, self.object_to_reposition.y0 - 7, self.object_to_reposition.group_tag.replace('spot_', ''), 'green')
        if 'duplicate' in self.object_to_reposition.unique_tag:
            self.draw_text(self.object_to_reposition.get_text_tags(), self.object_to_reposition.x0, self.object_to_reposition.y0 - 15, self.object_to_reposition.rectangle_type.value, self.object_to_reposition.get_colour())

        self.object_to_reposition = None

    def RectSpotDraw(self):
        self.rectangleType = RectangleType.SPOT_AREA
        self.RectDraw()

    def RectDraw(self):
        self.myCanvas.unbind("<Button-1>")
        self.myCanvas.bind("<ButtonPress-1>", self.RectStartCoords)
        self.myCanvas.bind("<B1-Motion>", self.RectUpdateCoords)
        self.myCanvas.bind("<ButtonRelease-1>", self.RectFinalCoords)

    def RectStartCoords(self, event):
        if self.rectangleType == RectangleType.DUPLICATE:
            groupSuffix = 'NewDup'
            self.text_label = "Duplicate"
        if self.rectangleType == RectangleType.SPOT_AREA:
            groupSuffix = 'NewSpot'
            self.text_label="spot area"

        groupTag = groupSuffix +str(uuid.uuid4())
        rectStart_x = self.myCanvas.canvasx(event.x)
        rectStart_y = self.myCanvas.canvasy(event.y)
        self.rectangle = Rectangle(rectStart_x,rectStart_y, rectStart_x + 1,rectStart_y + 1,self.rectangleType,groupTag)
        self.draw_interactive_rectange(self.rectangle)

    def RectUpdateCoords(self, event):
        self.rectangle.x1 = self.myCanvas.canvasx(event.x)
        self.rectangle.y1 = self.myCanvas.canvasy(event.y)
        self.myCanvas.coords(self.rectangle.unique_tag, self.rectangle.x0, self.rectangle.y0, self.rectangle.x1, self.rectangle.y1)

    def RectFinalCoords(self, event):

        self.draw_interactive_rectange(self.rectangle)
        self.model.save_drawing_object_to_json(self.rectangle)

    def capture_spot(self, drawSpotEvent):
        x0 = self.myCanvas.canvasx(drawSpotEvent.x)
        y0 = self.myCanvas.canvasy(drawSpotEvent.y)
        groupTag = 'NewSpot_'+str(uuid.uuid4())
        this_spot = Spot(x0,y0, groupTag)
        self.draw_interactive_spot(this_spot,'cyan','blue')
        spot_capture_dialog = SaveSpotDialog(self.view, self, this_spot, True)
        self.myCanvas.wait_window(spot_capture_dialog.spotCaptureWindow)
        spot_tags = this_spot.get_tags()
        text_tags = this_spot.get_text_tags()
        self.myCanvas.itemconfig(this_spot.unique_text_tag, text=this_spot.group_tag.replace('spot_',''), state=tk.NORMAL, tags=('spot_'+text_tags[0],text_tags[1]))
        self.myCanvas.itemconfig(this_spot.unique_tag, tags=('spot_'+spot_tags[0],spot_tags[1]))
        #self.currentSpotTextBox.delete(first=0, last=100)
        #self.spotCaptureWindow.destroy()

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
        self.myCanvas.unbind("<Button-1>")
        self.myCanvas.unbind("<ButtonPress-1>")
        self.myCanvas.unbind("<B1-Motion>")
        self.myCanvas.unbind("<ButtonRelease-1>")
        self.myCanvas.bind("<ButtonPress-1>", self.BreakLineStart)
        self.myCanvas.bind("<B1-Motion>", self.BreakLineUpdate)
        self.myCanvas.bind("<ButtonRelease-1>", self.finish_breakline)

    def BreakLineStart(self, event):
        group_tag = 'line_' + str(uuid.uuid4())
        colour = 'red'
        x0 = self.myCanvas.canvasx(event.x)
        y0 = self.myCanvas.canvasy(event.y)
        self.breakline = Breakline(x0,y0,x0+1, y0+1,group_tag)
        self.draw_interactive_breakline(self.breakline)

    def BreakLineUpdate(self, moveEvent):
        self.myCanvas.unbind("<ButtonPress-1>")
        self.breakline.x1 = self.myCanvas.canvasx(moveEvent.x)
        self.breakline.y1 = self.myCanvas.canvasy(moveEvent.y)
        self.myCanvas.coords(self.breakline.unique_tag, self.breakline.x0, self.breakline.y0, self.breakline.x1, self.breakline.y1)

    def finish_breakline(self,mouse_event):
        self.model.insert_new_breakline_to_pairslist(self.breakline)

    def display_spots_during_measurement(self,spotList):

        for spot in spotList:
            spotX = spot[0]
            spotY = spot[1]
            spotID = spot[2]
            self.myCanvas.create_oval(spotX-5,spotY-5, spotX+5, spotY+5, fill='lightgreen',outline='green', width=1, activefill='yellow', activeoutline='yellow', tags=('s_'+str(spotID), 'spot_'+str(spotID)))
            self.myCanvas.create_text(spotX-7,spotY-7,fill='green', text=spotID, tags=('s_'+str(spotID), 'spotno_'+str(spotID)))

    def plot_kvalues_on_grain_image(self, composite_contour_list, underlying_image, is_binary_image, image_width, image_height):
        dpi = 100
        fig = plt.figure(figsize=(image_width / dpi, image_height / dpi))
        ax = fig.add_axes([0, 0, 1, 1])
        matplotlib.use('Agg')
        canvas = FigureCanvasAgg(fig)
        plt.margins(0, 0)
        plt.axis('off')

        if not is_binary_image:
            plt.imshow(underlying_image, cmap='jet')
        else:
            plt.imshow(underlying_image, cmap='Greys_r')
        max_angles = [max(contour.curvature_values) for contour in composite_contour_list if contour.keep_contour]
        max_angle = max(max_angles)
        for contour in composite_contour_list:
            if contour.keep_contour == False:
                continue
            x, y = zip(*contour.reconstructed_points)

            xmax, ymax = zip(*contour.max_curvature_coordinates)
            plt.scatter(x, y, c=contour.curvature_values, cmap='rainbow', vmin=0, vmax=max_angle, s=10)
            plt.scatter(xmax, ymax, edgecolor='red',s=20)

        canvas_data, (canvas_width,canvas_height) = canvas.print_to_buffer()  # taken from here: https://matplotlib.org/3.1.1/gallery/user_interfaces/canvasagg.html
        image_matrix = np.frombuffer(canvas_data, np.uint8).reshape((canvas_height, canvas_width, 4))
        image_pill = PIL.Image.frombytes("RGBA", (canvas_width, canvas_height), image_matrix)
        self.clear_canvas_and_display_image(image_pill)

    def plot_angle_displacement_graph(self, contour,max_angle):

        if contour.keep_contour == False:
            return
        #calculate the cumulative displacement along the contour
        dxy = np.diff(contour.reconstructed_points, axis=0)
        dt = np.sqrt((dxy ** 2).sum(axis=1))
        cumulative_distance = np.concatenate([([0.]), np.cumsum(dt)])


        #get the displacement value for each max curvature:
        displacements = []
        for maximum in contour.max_curvature_values:
            for i in range(len(contour.curvature_values)):
                if maximum == contour.curvature_values[i]:
                    displacements.append(cumulative_distance[i])

        fig = plt.figure(figsize=(7,7))
        ax = fig.add_axes([0.1, 0.1, 0.9, 0.9])

        plt.margins(0, 0)
        ax.plot(cumulative_distance, contour.curvature_values, c='black', zorder=1)
        ax.set_ylabel('Angle (degrees)', fontsize='11')
        ax.set_xlabel('Contour Perimeter Distance (pixels)',fontsize='11')
        plt.xlim((0, 1600))
        plt.ylim(-60,110)
        plt.tight_layout()

    def draw_image_data(self, image_data):
        for spot in image_data.spots:
            self.draw_interactive_spot(spot,'cyan','blue')

        for spot_area in image_data.spot_areas:
            self.draw_interactive_rectange(spot_area)

        for rectangle in image_data.unwanted_objects:
            self.draw_interactive_rectange(rectangle)

        for polygon in image_data.polygons:
            self.draw_interactive_polygon(polygon)

        if image_data.scale is not None:
            self.draw_interactive_scale(image_data.scale)

    def draw_interactive_breakline(self, line):
        self.myCanvas.create_line(line.x0, line.y0, line.x1, line.y1, width=2, fill='red', activefill='yellow', tags=line.get_tags())

    def draw_interactive_rectange(self, rectangle):
        self.myCanvas.create_rectangle(rectangle.x0, rectangle.y0, rectangle.x1, rectangle.y1, width=3, outline=rectangle.get_colour(), activefill='yellow',
                                       activeoutline='yellow',
                                       tags=rectangle.get_tags())
        self.draw_text(rectangle.get_text_tags(), rectangle.x0, rectangle.y0 - 15, rectangle.rectangle_type.value, rectangle.get_colour())

    def draw_interactive_spot(self, spot,colour,outline_colour):
        self.myCanvas.create_oval(spot.x0 - 6, spot.y0 - 6, spot.x0 + 6, spot.y0 + 6, width=2, outline=outline_colour, fill=colour,
                                  activefill='yellow', activeoutline='yellow',
                                  tags=spot.get_tags())
        self.draw_text(spot.get_text_tags(),spot.x0, spot.y0-15, spot.group_tag.replace('spot_',''), outline_colour)

    def draw_interactive_scale(self, scale):
        self.myCanvas.create_line(scale.x0, scale.y0, scale.x1, scale.y1, width=3, fill='red', activefill='yellow',
                                  tags=scale.get_tags())

    def draw_interactive_polygon(self,polygon):
        self.myCanvas.create_polygon(polygon.coordinates,fill='', outline='red', activeoutline='yellow', width=2, tags=polygon.get_tags())

    def draw_contour(self, contour):
        coords=contour.flatten_coordinates()
        size = contour.size()
        if size<2:
            return # if there is only one point, don't draw any lines.

        self.myCanvas.delete(self.uniqueTag)  # delete all pre-existing lines and redraw
        if size > 2:
            self.myCanvas.create_polygon(coords, fill='', outline='red', activeoutline='yellow', width=2, tags=contour.get_tags())  # redraw,now includes the added point
        else:
            self.myCanvas.create_line(coords, fill='red', activefill='yellow', width=2, tags=contour.get_tags())  # if there are only two points, its a line not a polygon

    def ensure_contour_does_not_overlie_other_contours(self, undeleted_contour):
        new_contour = shapely.geometry.Polygon(undeleted_contour.paired_coordinates()).buffer(0)
        items_to_raise_above_new_contour = []
        for key,contour in self.model.contours_by_group_tag.items():
            if undeleted_contour.group_tag == contour.group_tag:
                pass
            if new_contour.contains(shapely.geometry.Polygon(contour.paired_coordinates()).buffer(0)):
                self.myCanvas.tag_lower(undeleted_contour.unique_tag,contour.unique_tag)
                break

    def draw_text(self,tags,x,y,text,colour):
        self.myCanvas.create_text(x, y, text=text, fill=colour, font=("Helvetica", 8, "bold"), tags=tags)