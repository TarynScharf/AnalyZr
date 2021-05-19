import tkinter as tk
import traceback
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

import os

from src.model.drawing_objects.breakline import Breakline
from src.model.image_data import ImageData
from src.view.application_drawing import Drawing

os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2,40).__str__()
import matplotlib
from PIL import Image
from src.model.composite_contour import CompositeContour
matplotlib.use('Agg')
from src.model.ZirconSeparationUtils import *


class Application:

    def __init__(self, master, model):
        self.master = master
        self.model = model
        master.title("Zircon Shape Analysis")
        master.geometry('1600x3000')

        # Reroute exceptions to display a message box to the user
        #sys.excepthook = self.exception_hook

        self.myFrame = tk.Frame(master, width=1600, height=3000)
        self.myFrame.pack(expand=True, fill='both')
        self.drawing=Drawing(self.myFrame, self.model, self)

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
        self.binariseMenu.add_command(label="Load json Files", command=lambda: self.Browse('json'))
        self.binariseMenu.add_command(label="Image Segmentation Toolbox", command=self.create_image_segmentation_toolbox_dialog)
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
        image, image_data = self.model.get_current_image_for_data_capture()
        self.label['text'] = image_data.get_image_name() + '  | Sample ' + str(
            self.model.get_current_sample_index() + 1) + ' of ' + str(self.model.get_sample_count())
        self.drawing.display_image(image)
        self.drawing.draw_image_data(image_data)

    def display_image(self, image):
        self.drawing.display_image(image)

    def Browse(self, case):
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

    def close_popup_window_and_create_jsons(self,window, json_files_to_create):
        self.close_window(window)
        for file_name in json_files_to_create:
            self.model.write_json_file(file_name)

    def GetImageInfo(self):
        #Does 2 things:
        # Check for images in the folder, returns error message if there are none.
        #checks if each image has a corresponding json file. Offers to create the ones that are missing.

        self.jsonList = []
        image_folder_path = self.image_folder_path.get()
        json_folder_path = self.json_folder_path.get()
        if json_folder_path == '':
            json_folder_path = image_folder_path

        has_images,missing_json_files = self.model.check_for_images_and_jsons(image_folder_path,json_folder_path)

        if has_images == False:
            error_message_text = "The folder contains no images for data capture."
            self.open_error_message_popup_window(error_message_text)
            return

        self.model.set_source_folder_paths(image_folder_path,json_folder_path)

        if missing_json_files:
            if self.create_json_var.get() == 1:
                for file in missing_json_files:
                    self.model.write_json_file(file)
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
        self.browse_for_files_window = Toplevel(self.master)
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
        self.close_window(self.browse_for_files_window)
        self.update_data_capture_display()

    def activate_browse_for_json_folder(self):
        if self.load_json_folder.get()==1:
            state = NORMAL
            path = ""
        elif self.load_json_folder.get()==0:
            state = DISABLED
            path = self.image_folder_path.get()

        self.json_folder_Label.config(state=state)
        self.json_folder_text_box.config(state=state)
        self.browse_for_json_folder.config(state=state)
        self.model.set_json_folder_path(path)

    def create_image_segmentation_toolbox_dialog(self):
        self.browseImagesWindow = Toplevel(self.master)
        self.browseImagesWindow.title("Image Segmentation Toolbox")
        self.browseImagesWindow.minsize(400, 100)
        self.browseImagesWindow.attributes('-topmost', True)

        self.RL_Label = Label(self.browseImagesWindow, text="RL Image")
        self.RL_Label.grid(column=0, row=0)
        self.RLPath = tk.StringVar()
        self.RLPath.set('')
        #self.RLPath.set('/home/matthew/Code/ZirconSeparation/test/images/88411_spots_p1_RL__WqO4ozqE.png')
        self.RLPath.set('C:/Users/20023951/PycharmProjects/ZirconSeparation/test/images/88411_spots_p1_RL__WqO4ozqE.png')
        self.RLTextBox = Entry(self.browseImagesWindow, width=150, textvariable=self.RLPath)
        self.RLTextBox.grid(column=1, row=0)
        self.browseRL = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('RL'))
        self.browseRL.grid(column=3, row=0, padx=2, pady=5)
        self.rlVar = IntVar()
        self.rlCheckButton = Checkbutton(self.browseImagesWindow, text= 'Binarise  RL',variable=self.rlVar)
        self.rlCheckButton.grid(column=4, row=0, padx=2, pady=5)
        self.Display_RL_Image_Button = Button(self.browseImagesWindow, text="Display", width=8, command=lambda: self.display_parent_image(0))
        self.Display_RL_Image_Button.grid(column=5, row=0, padx=2, pady=5)

        self.TL_Label = Label(self.browseImagesWindow, text="TL Image")
        self.TL_Label.grid(column=0, row=1)
        self.TLPath = tk.StringVar()
        self.TLPath.set('')
        self.TLPath.set('C:/Users/20023951/PycharmProjects/ZirconSeparation/test/images/88411_spots_p1_TL_PnCztOBkT.png')
        self.TLTextBox = Entry(self.browseImagesWindow, width=150, textvariable=self.TLPath)
        self.TLTextBox.grid(column=1, row=1)
        self.browseTL = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('TL'))
        self.browseTL.grid(column=3, row=1, padx=2, pady=5)
        self.tlVar = IntVar()
        self.tlCheckButton = Checkbutton(self.browseImagesWindow, text='Binarise  TL', variable=self.tlVar)
        self.tlCheckButton.grid(column=4, row=1, padx=2, pady=5)
        self.Display_TL_Image_Button = Button(self.browseImagesWindow, text="Display", width=8,
                                              command=lambda: self.display_parent_image(1))
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
        self.Display_Mask = Button(self.browseImagesWindow, text="Display Mask", width=15, command=lambda: self.drawing.DisplayMask())
        self.Display_Mask.grid(column=4, row=3, padx=3, pady=5)


        self.Process_Folder = Label(self.browseImagesWindow, text="Process Mask Folder")
        self.Process_Folder.grid(column=0, row=4)
        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')
        self.Folder_TextBox = Entry(self.browseImagesWindow, width=100, textvariable=self.Folder_Location)
        self.Folder_TextBox.grid(column=1, row=4)
        self.Browse_Folder = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('Folder'))
        self.Browse_Folder.grid(column=3, row=4, padx=3, pady=5)
        self.Process_Folder = Button(self.browseImagesWindow, text="Process Folder", width=15,command=lambda: self.model.ProcessFolder())
        self.Process_Folder.grid(column=4, row=4, padx=3, pady=5)

        self.BinariseButton = Button(self.browseImagesWindow, text="Binarise", command=self.binariseImages)
        self.BinariseButton.grid(column=0, row=5, padx=2, pady=5)
        self.SeparateButton = Button(self.browseImagesWindow, text="Separate Grains", command=self.separate)
        self.SeparateButton.grid(column=0, row=6, padx=2, pady=5)
        self.breakLine = Button(self.browseImagesWindow, text="Draw Break Line", command=self.drawing.DrawBreakLine)
        self.breakLine.grid(column=0, row=7, padx=2, pady=5)
        self.saveChanges = Button(self.browseImagesWindow, text="Save Changes", command=self.SaveBreakChanges)
        self.saveChanges.grid(column=0, row=8, padx=2, pady=5)
        self.measureShapes = Button(self.browseImagesWindow, text="Measure Shapes",command=self.start_measure_shapes)
        self.measureShapes.grid(column=0, row=9, padx=2, pady=5)
        self.pushDB = Button(self.browseImagesWindow, text="Push to DB",command=self.model.push_shape_measurements_to_database)
        self.pushDB.grid(column=0, row=10, padx=2, pady=5)
        self.moveSpot = Button(self.browseImagesWindow, text="Reposition spot", command=self.drawing.PointMove)
        self.moveSpot.grid(column=0, row=11, padx=2, pady=5)
        self.grain_boundary_capture = Button(self.browseImagesWindow, text ="Grain Boundary Capture [p]", command=self.drawing.BoundaryDraw)
        self.grain_boundary_capture.grid(column=0, row=12, padx=2, pady=5)

        self.undo_delete = Button(self.browseImagesWindow, text="Undo Delete Contour", command=self.undo_delete_contour)
        self.undo_delete.grid(column=0, row=13, padx=2, pady=5)

        self.write_to_csv_button = Button(self.browseImagesWindow, text="Save to CSV", command=self.model.write_to_csv)
        self.write_to_csv_button.grid(column=0, row=14, padx=2, pady=5)

    def SaveBreakChanges(self,new_contour=None):
        RLPath = self.RLPath.get()
        TLPath = self.TLPath.get()
        image, contours =self.model.SaveBreakChanges(RLPath, TLPath,new_contour)

        self.display_image(image)
        for contour in contours:
            self.drawing.draw_contour(contour)

    def undo_delete_contour(self):
        contour_to_restore = self.model.undo_delete_contour()
        if contour_to_restore is not None:
            self.drawing.draw_contour(contour_to_restore)

    def binariseImages(self):
        image,contours,self.width,self.height = self.model.binariseImages(self.RLPath.get(), self.TLPath.get(),self.rlVar.get(), self.tlVar.get())

        self.drawing.display_image(image)
        for contour in contours:
            self.drawing.draw_contour(contour)

    def start_measure_shapes(self):
        mask_path = self.MaskFolderLocation.get()
        self.model.MeasureShapes(mask_path)

    def ProcessFolder(self):
        self.ProcessFolderFlag = True
        for path,folder,files in os.walk(self.Folder_Location.get()):
            for name in files:
                self.currentMask = self.Folder_Location.get()+'/'+name #the file path of the current mask we're processing
                self.DisplayMask()
                self.model.MeasureShapes(self.currentMask,self.TLPath.get(),self.RLPath.get(),True)
                self.model.push_shape_measurements_to_database()
                self.currentMask = None
            self.ProcessFolderFlag = False
        print('Processing complete')

    def display_spots_during_measurement(self, spotList):
        self.drawing.display_spots_during_measurement(spotList)

    def DisplayMask(self):
        path = self.File_Location.get()
        rl_path = ''
        tl_path = ''
        if path != '':
            region = self.model.load_mask_from_file(path)
            if region == None:
                error_message_text = "JSON file location has not been defined"
                self.open_error_message_popup_window(error_message_text)
                return

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
            self.model.load_current_mask()

        image_pill = Image.fromarray(self.threshold)
        self.drawing.display_image(image_pill)
        self.model.extract_contours_from_image()

    def write_to_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension = '.csv', filetypes = [("CSV Files","*.csv")], title="Save As")
        self.model.write_to_csv(filepath)

    def SaveMask(self):
        fileRL = self.RLPath.get()
        fileTL = self.TLPath.get()
        maskPath = self.MaskFolderLocation.get()
        self.model.write_mask_to_png(fileRL,fileTL,maskPath)

    def separate(self):
        composite_contour_list, image_to_show, is_image_binary, pairs_list = self.model.separate(self.TLPath.get(), self.RLPath.get())
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

    def display_parent_image(self, image_to_display):
        #This is for optionally loading either the TL or RL image
        image_pill=None
        if image_to_display == 0:
            self.Current_Image = 'RL'
            fileRL = self.RLPath.get()
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
            fileTL = self.TLPath.get()
            if fileTL == '':
                error_message_text = "No transmitted light image has been selected"
                self.open_error_message_popup_window(error_message_text)
                return
            img = cv2.imread(fileTL)
            self.width = img.shape[1]
            self.height = img.shape[0]
            image_pill = Image.fromarray(img)

        self.drawing.display_image(image_pill)

        for polygon in self.model.get_current_image_contours():
            self.drawing.draw_contour(polygon)


