import tkinter as tk
import traceback
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

import os

from src.model.drawing_objects.breakline import Breakline
from src.model.image_data import ImageData
from src.view.application_drawing import Drawing
from src.view.data_capture_dialog import DataCaptureDialog
from src.view.measurement_table_dialog import MeasurementDialog
from src.view.segmentation_dialog import SegmentationDialog

os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2,40).__str__()
import matplotlib
from PIL import Image
from src.model.composite_contour import CompositeContour
matplotlib.use('Agg')
from src.model.ZirconSeparationUtils import *


class DataCaptureWindow(object):
    pass


class View:

    def __init__(self, master, model):
        self.master = master
        self.model = model
        master.title("Zircon Shape Analysis")
        master.geometry('1600x3000')

        # Reroute exceptions to display a message box to the user
        #sys.excepthook = self.exception_hook

        self.myFrame = tk.Frame(master, width=1600, height=3000)
        self.myFrame.pack(expand=True, fill='both')
        self.drawing:Drawing=Drawing(self.myFrame, self.model, self)

        self.mainMenu = Menu(self.master)
        self.fileMenu = Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label="File", menu=self.fileMenu)

        self.imagesMenu = Menu(self.mainMenu, tearoff=0)
        self.imagesMenu.add_command(label="Load Images", command=lambda: self.create_data_capture_dialog())
        self.imagesMenu.add_command(label="Move to Next Image [->]", command=self.NextImage)
        self.imagesMenu.add_command(label="Move to Previous Image [<-]", command=self.PrevImage)

        self.imagesMenu.add_command(label="Capture Analytical Spot [s]", command=self.drawing.start_spot_capture)
        self.imagesMenu.add_command(label="Capture Analytical Spot Size [a]", command=self.drawing.RectSpotDraw)
        self.imagesMenu.add_command(label="Mark Object for Deletion [d]", command=self.drawing.DupDraw)
        self.imagesMenu.add_command(label="Capture Scale [l]", command=self.drawing.DrawScale)

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
        self.width = None #width of displayed image
        self.height = None #height of displaed image
        self.ProcessFolderFlag = False

        self.json_folder_path = tk.StringVar()

        # Global bindings (aka shortcuts)
        master.bind("s", lambda e: self.drawing.start_spot_capture())
        master.bind("a", lambda e: self.drawing.RectSpotDraw())
        master.bind("d", lambda e: self.drawing.DupDraw())
        master.bind("<Left>", lambda e: self.PrevImage())
        master.bind("<Right>", lambda e: self.NextImage())
        master.bind("<Escape>", lambda e: self.UnbindMouse())
        master.bind("p", lambda e: self.drawing.BoundaryDraw())
        master.bind("i", lambda e: self.EditPolygon())
        master.bind("m", lambda e: self.drawing.PointMove())
        master.bind("l", lambda e: self.drawing.DrawScale())


    def open_segmentation_toolbox_dialog(self):
        SegmentationDialog(self)

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

    def ok_cancel_create_json_files(self, list_of_json_files_to_create):
        self.ok_cancel_json_window = Toplevel(self.master)
        self.ok_cancel_json_window.title("Create missing json Files")
        self.ok_cancel_json_window.minsize(400,100)

        self.ok_cancel_json_text = Label(self.ok_cancel_json_window, text = "Json files are missing. Do you want to create them?")
        self.ok_cancel_json_text.grid(column = 0, row = 0)

        self.ok_create_jsons = Button(self.ok_cancel_json_window, text="OK", width=5,command=lambda: self.close_popup_window_and_create_jsons(self.ok_cancel_json_window,list_of_json_files_to_create))
        self.ok_create_jsons.grid(column=1, row=1, padx=2, pady=5)

        self.cancel_create_jsons = Button(self.ok_cancel_json_window, text="Cancel", width=8,command=lambda: self.close_window(self.ok_cancel_json_window))
        self.ok_create_jsons.grid(column=2, row=1, padx=2, pady=5)

    def close_popup_window_and_create_jsons(self, window, json_file_paths):
        self.close_window(window)
        for file_name in json_file_paths:
            self.model.create_new_json_file(file_name)

    def get_image_info_for_data_capture(self, image_folder_path, json_folder_path, data_capture_image_type):
        #Does 2 things:
        # Check for images in the folder, returns error message if there are none.
        #checks if each image has a corresponding json file. Offers to create the ones that are missing.

        self.jsonList = []
        if json_folder_path == '':
            json_folder_path = image_folder_path

        has_images, missing_json_files = self.model.check_for_images_and_jsons(image_folder_path, json_folder_path, data_capture_image_type)

        if has_images == False:
            error_message_text = "The folder contains no images for data capture."
            self.open_error_message_popup_window(error_message_text)
            return

        self.model.set_source_folder_paths(image_folder_path,json_folder_path)

        if missing_json_files:
            if self.create_json_var.get() == 1:
                for file in missing_json_files:

                    self.model.create_new_json_file(file)
            else:
                self.ok_cancel_create_json_files(missing_json_files)


        self.model.read_sampleID_and_spots_from_json()

    def open_error_message_popup_window(self, error_message_text):
        self.errorMessageWindow = Toplevel(self.master)
        self.errorMessageWindow.title("Error")
        self.errorMessageWindow.minsize(300, 100)
        self.errorLabel = Label(self.errorMessageWindow, text=error_message_text)
        self.errorLabel.grid(column=0, row=0)

    def create_data_capture_dialog(self):
        DataCaptureDialog(self)


    def close_window(self,window):
            window.destroy()

    def load_files(self,image_folder_path,json_folder_path,image_type):
        self.get_image_info_for_data_capture(image_folder_path, json_folder_path,image_type)
        self.update_data_capture_display()


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
            image_to_display, contours, spotList, region_measurements = self.model.measure_shapes(mask_path, False)
        except ValueError as e:
            self.open_error_message_popup_window(str(e))
            return
        self.drawing.clear_canvas_and_display_image(image_to_display)
        for spot in spotList:
            self.drawing.draw_interactive_spot(spot, 'green')
        MeasurementDialog(self,region_measurements)
        #self.display_measurement_table(region_measurements)


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


    def ProcessFolder(self):
        self.ProcessFolderFlag = True
        for path,folder,files in os.walk(self.Folder_Location.get()):
            for name in files:
                self.currentMask = self.Folder_Location.get()+'/'+name #the file path of the current mask we're processing
                self.DisplayMask()
                try:
                    self.model.measure_shapes(self.currentMask, True)
                except ValueError as e:
                    self.open_error_message_popup_window(str(e))

                self.model.push_shape_measurements_to_database()
                self.currentMask = None
            self.ProcessFolderFlag = False
        print('Processing complete')

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

    def write_to_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension = '.csv', filetypes = [("CSV Files","*.csv")], title="Save As")
        self.model.write_to_csv(filepath)

    def separate(self):
        composite_contour_list, image_to_show, is_image_binary, pairs_list = self.model.separate()
        self.drawing.plot_kvalues_on_grain_image(composite_contour_list, image_to_show, is_image_binary,self.width, self.height)
        for line in pairs_list:
            self.drawing.draw_interactive_breakline(line)

    def create_spot_capture_dialog(self, event):
        thisSpot = event.widget.find_withtag('current')[0]
        all_IDs = self.myCanvas.find_withtag(self.thisSpotID)
        self.thisSpotID = self.myCanvas.gettags(thisSpot)[0]
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
        self.saveSpotNo.grid(column=0, row=1, pady=5)

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


