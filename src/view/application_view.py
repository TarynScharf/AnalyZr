import io
import tkinter as tk
import traceback
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import *

import os

from src.view.application_drawing import Drawing
from src.view.ask_csv_or_database_dialog import AskCsvOrDatabase
from src.view.data_capture_dialog import DataCaptureDialog
from src.view.measurement_table_dialog import MeasurementDialog
from src.view.segmentation_dialog import SegmentationDialog
from src.view.measure_scale_dialog import MeasureScaleDialog

os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2,40).__str__()
import matplotlib
from PIL import Image
matplotlib.use('Agg')
from src.model.ZirconSeparationUtils import *

class DataCaptureWindow(object):
    pass


class View:

    def __init__(self, master, model):
        self.master = master
        self.model = model
        master.title("Zircon Shape Analysis")
        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.state('zoomed')
        master.geometry(f'{width}x{height}')

        self.myFrame = tk.Frame(master)
        self.myFrame.pack(expand=True, fill='both')
        self.drawing:Drawing=Drawing(self.myFrame, self.model, self)

        self.mainMenu = Menu(self.master)

        self.imagesMenu = Menu(self.mainMenu, tearoff=0)
        self.imagesMenu.add_command(label="Load Images", command=lambda: self.create_data_capture_dialog())
        self.imagesMenu.add_command(label="Move to Next Image - shorcut right arrow",state=DISABLED, command=self.NextImage)
        self.imagesMenu.add_command(label="Move to Previous Image - left arrow",state=DISABLED, command=self.PrevImage)

        self.imagesMenu.add_command(label="Capture Analytical Spot - s",state=DISABLED, command=self.drawing.start_spot_capture)
        self.imagesMenu.add_command(label="Capture Analytical Spot Size - a",state=DISABLED, command=self.drawing.RectSpotDraw)
        self.imagesMenu.add_command(label="Mark Object for Deletion - d",state=DISABLED, command=self.drawing.DupDraw)
        self.imagesMenu.add_command(label="Capture Scale - l",state=DISABLED, command=self.drawing.DrawScale)
        self.imagesMenu.add_command(label="Cancel Current Command - esc", state = DISABLED, command = self.drawing.UnbindMouse)

        self.imagesMenu.insert_separator(1)
        self.imagesMenu.insert_separator(6)
        self.mainMenu.add_cascade(label="Data Capture", menu=self.imagesMenu)
        master.config(menu=self.mainMenu)

        self.binariseMenu = Menu(self.mainMenu, tearoff=0)
        self.binariseMenu.add_command(label="Load json Files", command=lambda: self.set_json_folder_path('json',self.myFrame))
        self.binariseMenu.add_command(label="Image Segmentation Toolbox", command=self.open_segmentation_toolbox_dialog)
        #self.binariseMenu.add_command(label="Grain Boundary Capture [p]", command=self.BoundaryDraw)
        #self.binariseMenu.add_command(label="Polygon Insert Point [i]", command=self.EditPolygon)
        #self.binariseMenu.add_command(label="Polygon Insert Point [m]", command=self.PointMove)
        self.binariseMenu.insert_separator(1)
        self.mainMenu.add_cascade(label="Segment Images", menu=self.binariseMenu)
        master.config(menu=self.mainMenu)

        # Two Frames. myFrame for the canvas, myMenuFrame for the buttons
        self.myMenuFrame = tk.Frame(master, width=1600, height=30)
        self.myMenuFrame.pack(fill='both')

        # Image name, so  we know which image we're working on
        self.label = Label(self.myMenuFrame, text='')
        self.label.grid(column=1, row=0, padx=5, pady=10)
        self.width = None #width of displayed image
        self.height = None #height of displaed image

        self.json_folder_path = tk.StringVar()


    def save_image(self):
        image_file_name = filedialog.asksaveasfilename(defaultextension='.jpg')
        postscript = self.drawing.myCanvas.postscript(colormode='color')
        image = Image.open(io.BytesIO(postscript.encode('utf-8')))

        if not image_file_name[len(image_file_name)-4:].lower() == '.jpg':
            image.save(image_file_name+'jpg')
        image.save(image_file_name)

    def open_segmentation_toolbox_dialog(self):
        self.drawing.myCanvas.delete('all')
        self.mainMenu.entryconfig('Data Capture', state=DISABLED)
        self.drawing.UnbindMouse()

        try:
            SegmentationDialog(self)
        except ValueError as e:
            self.open_error_message_popup_window(str(e))
            return

    def exception_hook(self, exception_type, value, tb) -> None:
        """
        Method to hook into Python's exception handling mechanism to display any errors that occur in the UI
        as well as in the console.
        """
        #if isinstance(value, ExpectedException):
        #    self.view.show_expected_error(str(value))
        #    return

        sys.__excepthook__(exception_type, value, tb)
        error = str(value) + "\n" + "".join(traceback.format_tb(tb))
        #self.view.show_unexpected_error(error)
        self.open_error_message_popup_window(error)


    def NextImage(self):
        self.model.next_image()
        self.update_data_capture_display()

    def PrevImage(self):
        self.model.previous_image()
        self.update_data_capture_display()

    def update_data_capture_display(self):
        image, json_data = self.model.get_current_image_for_data_capture()
        self.label['text'] = json_data.get_data_capture_image_name() + '  | Sample ' + str(
            self.model.get_current_sample_index() + 1) + ' of ' + str(self.model.get_sample_count())
        self.drawing.clear_canvas_and_display_image(image)
        self.drawing.draw_image_data(json_data)

    def display_image(self, image):
        self.drawing.clear_canvas_and_display_image(image)

    def set_json_folder_path(self,case,window):
        json_path = self.Browse(case,window)
        self.model.set_json_folder_path(json_path)

    def Browse(self, case, window):
        if case == 'RL': #if browing for an RL image in the binarise menu
            filename = filedialog.askopenfilename(parent = window, filetypes=[("all files", "*.*")])
            return filename

        elif case == 'TL': #if browsing for a TL image in the binarise menu
            filename = filedialog.askopenfilename(parent = window, filetypes=[("all files", "*.*")])
            return filename

        elif case == 'Mask': #if browsing for a mask image in the binarise menu
            folderName = filedialog.askdirectory()
            return folderName

        elif case == 'Folder': #if browsing for a folder
            folderName = filedialog.askdirectory(parent = window)
            return folderName

        elif case == 'json':
            json_folder_name = filedialog.askdirectory(parent = window)
            return json_folder_name

        elif case == 'capture': #if browsing for a folder of images for spot capture
            filename = filedialog.askdirectory()
            return filename

        elif case == 'File':
            filename = filedialog.askopenfilename(parent = window, filetypes=[("all files", "*.*")])
            return filename


    def open_error_message_popup_window(self, error_message_text):
        self.errorMessageWindow = Toplevel(self.master)
        self.errorMessageWindow.title("Error")
        self.errorMessageWindow.minsize(300, 100)
        self.errorLabel = Label(self.errorMessageWindow, text=error_message_text)
        self.errorLabel.grid(column=0, row=0)

    def create_data_capture_dialog(self):
        DataCaptureDialog(self,self.drawing)


    def close_window(self,window):
            window.destroy()

    def SaveBreakChanges(self,new_contour=None):
        image, contours =self.model.SaveBreakChanges(new_contour)
        self.display_image(image)
        for contour in contours:
            self.drawing.draw_contour(contour)

    def undo_delete_contour(self):
        contour_to_restore = self.model.undo_delete_contour()
        if contour_to_restore is not None:
            self.drawing.draw_contour(contour_to_restore)

    def binariseImages(self,RLPath, TLPath, rlVar, tlVar):
        self.model.set_rl_tl_paths_and_usage(RLPath, TLPath,rlVar, tlVar)
        try:
            image,contours,self.width,self.height = self.model.binariseImages()
        except ValueError as e:
            self.open_error_message_popup_window(str(e))
            return

        self.drawing.clear_canvas_and_display_image(image)
        for contour in contours:
            self.drawing.draw_contour(contour)

    def start_measure_shapes(self,mask_path):
        try:
            image_to_display, contours, spotList, region_measurements = self.model.measure_shapes(mask_path,False)
        except ValueError as e:
            self.open_error_message_popup_window(str(e))
            return
        self.drawing.clear_canvas_and_display_image(image_to_display)
        for contour in contours:
            self.drawing.draw_contour(contour)
        for spot in spotList:
            self.drawing.draw_interactive_spot(spot, 'green2','green')
        MeasurementDialog(self,region_measurements)

    def process_all_masks_in_folder(self, mask_file_folder):
        all_folder_measurements = []
        for path,folder,files in os.walk(mask_file_folder):
            for name in files:
                current_mask_file_path = os.path.join(mask_file_folder,name) #the file path of the current mask we're processing
                self.DisplayMask(current_mask_file_path)
                try:
                    _, _, _, measurements = self.model.measure_shapes(current_mask_file_path,True)
                    all_folder_measurements = all_folder_measurements+measurements
                except ValueError as e:
                    self.open_error_message_popup_window(str(e))
                    return
        AskCsvOrDatabase(self, all_folder_measurements)

    def save_folder_measurements_to_csv(self,all_folder_measurements):
            filepath = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[("CSV Files", "*.csv")], title="Save As")
            if filepath == '':
                messagebox.showinfo("Information", "Processing cancelled")
                return
            self.model.write_to_csv(filepath, all_folder_measurements)
            messagebox.showinfo("Information", "Processing Complete")

    def save_folder_measurements_to_db(self,all_folder_measurements):
            self.ensure_database_path_set()
            try:
                self.model.push_shape_measurements_to_database(all_folder_measurements)
            except Exception as e:
                self.open_error_message_popup_window(str(e))
                return
            messagebox.showinfo("Information", "Processing Complete")

    def ensure_database_path_set(self):
        #if self.model.database_file_path is not None:
        #    return
        database_file_path = self.Browse('File',self.master)
        if not database_file_path:
            return

        self.model.set_database_file_path(database_file_path)

    def DisplayMask(self, mask_file_path):
        try:
            region = self.model.load_mask_from_file(mask_file_path)
        except Exception as e:
            self.open_error_message_popup_window(str(e))
            return

       # if self.ProcessFolderFlag == True:
       #     self.model.load_current_mask()

        image_pill = self.model.get_threshold_image()
        self.drawing.clear_canvas_and_display_image(image_pill)
        self.model.extract_contours_from_image('contour')

    def separate(self):
        composite_contour_list, image_to_show, is_image_binary, pairs_list = self.model.separate()
        self.drawing.plot_kvalues_on_grain_image(composite_contour_list, image_to_show, is_image_binary,self.width, self.height)
        for line in pairs_list:
            self.drawing.draw_interactive_breakline(line)

    '''def create_spot_capture_dialog(self, event):
        thisSpot = event.widget.find_withtag('current')[0]
        all_IDs = self.drawing.myCanvas.find_withtag(self.thisSpotID)
        self.thisSpotID = self.drawing.myCanvas.gettags(thisSpot)[0]
        for ID in all_IDs:
            if not ID == thisSpot:
                self.labelID = ID
                self.myCanvas.itemconfig(self.labelID, state=tk.HIDDEN)

        self.spotCaptureWindow = Toplevel(self.master)
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
        self.saveSpotNo.grid(column=0, row=1, pady=5)'''

    def display_parent_image(self, image_to_display,fileRL,fileTL):
        #This is for optionally loading either the TL or RL image
        image_pill=None
        if image_to_display == 0:
            self.Current_Image = 'RL'
            if fileRL == '':
                error_message_text = "No reflected light image has been selected"
                self.open_error_message_popup_window(error_message_text)
                return
            img = cv2.imread(fileRL)
            self.width = img.shape[1]
            self.height = img.shape[0]
            image_pill = Image.fromarray(img)
        if image_to_display == 1:
            self.Current_Image = 'TL'
            if fileTL == '':
                error_message_text = "No transmitted light image has been selected"
                self.open_error_message_popup_window(error_message_text)
                return
            img = cv2.imread(fileTL)
            self.width = img.shape[1]
            self.height = img.shape[0]
            image_pill = Image.fromarray(img)

        self.drawing.clear_canvas_and_display_image(image_pill)

        for polygon in self.model.get_current_image_contours():
            self.drawing.draw_contour(polygon)

    def get_real_world_distance_for_scale(self, scale_line):
        MeasureScaleDialog(self, self.model, scale_line)


    def activate_data_capture_options(self):
        self.imagesMenu.entryconfig("Move to Next Image - shorcut right arrow", state=NORMAL)
        self.imagesMenu.entryconfig("Move to Previous Image - left arrow", state=NORMAL)
        self.imagesMenu.entryconfig("Capture Analytical Spot - s", state=NORMAL) #"Capture Analytical Spot [s]"
        self.imagesMenu.entryconfig("Capture Analytical Spot Size - a", state=NORMAL) #"Capture Analytical Spot Size [a]"
        self.imagesMenu.entryconfig("Mark Object for Deletion - d", state=NORMAL) #"Mark Object for Deletion [d]"
        self.imagesMenu.entryconfig("Capture Scale - l", state=NORMAL) #"Capture Scale [l]"
        self.imagesMenu.entryconfig("Cancel Current Command - esc", state=NORMAL) #"Capture Scale [l]"






