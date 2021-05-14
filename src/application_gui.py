import csv
import datetime
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

import os
from src.application_model import Model
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2,40).__str__()
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

    def __init__(self, master, model):
        self.master = master
        self.model = model
        master.title("Zircon Shape Analysis")
        master.geometry('1600x3000')

        self.mainMenu = Menu(self.master)
        self.fileMenu = Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label="File", menu=self.fileMenu)

        self.imagesMenu = Menu(self.mainMenu, tearoff=0)
        self.imagesMenu.add_command(label="Load Images", command=lambda: self.create_spot_capture_dialog())
        self.imagesMenu.add_command(label="Capture Analytical Spot [s]", command=self.start_spot_capture)
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

        self.drawing=Drawing(self.myFrame)

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

    def update_polygon(self,polygon):
        self.drawing.draw_polygon(polygon)

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
            self.model.write_json_file(file_name)

    def GetImageInfo(self):
        #Does 3 things:
        # Check for images in the folder, returns error message if there are none.
        #checks if each image has a corresponding json file. Offers to create the ones that are missing.
        #loads the images for spot capture
        self.jsonList = []

        has_images,missing_json_files = self.model.check_for_images_and_jsons(self.folderPath)

        if has_images == False:
            self.error_message_text = "The folder contains no images for data capture."
            self.open_error_message_popup_window()
            return

        if missing_json_files:
            if self.create_json_var.get() == 1:
                for file in missing_json_files:
                    self.model.write_json_file(file)
            else:
                self.ok_cancel_create_json_files(missing_json_files)

        self.model.read_sampleID_and_spots_from_json(self.folderPath)

    def open_error_message_popup_window(self):
        self.errorMessageWindow = Toplevel(root)
        self.errorMessageWindow.title("Error")
        self.errorMessageWindow.minsize(300, 100)
        self.errorLabel = Label(self.errorMessageWindow, text=self.error_message_text)
        self.errorLabel.grid(column=0, row=0)

    def create_spot_capture_dialog(self):
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
        self.browseImagesWindow = Toplevel(root)
        self.browseImagesWindow.title("Image Segmentation Toolbox")
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
        self.saveMask = Button(self.browseImagesWindow, text="Save Mask", command=lambda: self.model.SaveMask())
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

        self.BinariseButton = Button(self.browseImagesWindow, text="Binarise", command=self.model.binariseImages)
        self.BinariseButton.grid(column=0, row=5, padx=2, pady=5)
        self.SeparateButton = Button(self.browseImagesWindow, text="Separate Grains", command=self.model.Separate)
        self.SeparateButton.grid(column=0, row=6, padx=2, pady=5)
        self.breakLine = Button(self.browseImagesWindow, text="Draw Break Line", command=self.drawing.DrawBreakLine)
        self.breakLine.grid(column=0, row=7, padx=2, pady=5)
        self.saveChanges = Button(self.browseImagesWindow, text="Save Changes", command=self.model.SaveBreakChanges)
        self.saveChanges.grid(column=0, row=8, padx=2, pady=5)
        self.measureShapes = Button(self.browseImagesWindow, text="Measure Shapes",command=self.start_measure_shapes)
        self.measureShapes.grid(column=0, row=9, padx=2, pady=5)
        self.pushDB = Button(self.browseImagesWindow, text="Push to DB",command=self.DBPush)
        self.pushDB.grid(column=0, row=10, padx=2, pady=5)
        self.moveSpot = Button(self.browseImagesWindow, text="Reposition spot", command=self.drawing.PointMove)
        self.moveSpot.grid(column=0, row=11, padx=2, pady=5)
        self.grain_boundary_capture = Button(self.browseImagesWindow, text ="Grain Boundary Capture [p]", command=self.drawing.BoundaryDraw)
        self.grain_boundary_capture.grid(column=0, row=12, padx=2, pady=5)

        self.undo_delete = Button(self.browseImagesWindow, text="Undo Delete Contour", command=self.model.undo_delete_contour)
        self.undo_delete.grid(column=0, row=13, padx=2, pady=5)

        self.write_to_csv_button = Button(self.browseImagesWindow, text="Save to CSV", command=self.write_to_csv)
        self.write_to_csv_button.grid(column=0, row=14, padx=2, pady=5)

    def start_measure_shapes(self):
        mask_path = self.MaskFolderLocation.get()
        self.model.MeasureShapes(mask_path)


    def ProcessFolder(self):
        self.ProcessFolderFlag = True
        for path,folder,files in os.walk(self.Folder_Location.get()):
            for name in files:
                self.currentMask = self.Folder_Location.get()+'/'+name #the file path of the current mask we're processing
                self.DisplayMask()
                self.model.MeasureShapes(self.currentMask,True)
                self.model.push_shape_measurements_to_database()
                self.currentMask = None
            self.ProcessFolderFlag = False
        print('Processing complete')

    def DisplayMask(self):
        path = self.File_Location.get()
        rl_path = ''
        tl_path = ''
        if path != '':
            region = self.model.load_mask_from_file(path)
            if region == None:
                self.error_message_text = "JSON file location has not been defined"
                self.open_error_message_popup_window()
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
        self.erode_small_artifacts(self.threshold)
        image_pill = Image.fromarray(imCopy)
        self.drawing.display_image(image_pill)

        def filter_polygon_by_area(contour):
            area = cv2.contourArea(contour, False)
            return area>=50

        self.model.extract_contours_from_image('contour',filter_polygon_by_area)


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
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2, 2))  # this large structuring element is designed to  remove bubble rims
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        opening[opening == 1] = 255
        opening_uint8 = opening.astype('uint8')
        self.threshold = opening_uint8


    def Separate(self):
        reconstructed_points = [] #for testing
        self.threshold = self.convert_contours_to_mask_image()
        #

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
                    composite_contour.max_curvature_distance = node_distance_values
                    #create_curvature_distance_plot(composite_contour)
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
        elif self.RLPath.get()!='':
            imgRL = cv2.imread(self.RLPath.get())
            plt.imshow(imgRL, cmap='Greys_r')
        else:
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

            sc=plt.scatter(xmax,ymax,facecolors='none',edgecolors='red',s=7,linewidth=1)
            #cbaxis = fig.add_axes([0.9,0.1,0.03,0.8])
            #cbar = plt.colorbar(sc, cax=cbaxis)
            #cbar.set_label('Curvature (K)', rotation=270, labelpad=20)
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

        canvas_data, (canvas_width,canvas_height) = canvas.print_to_buffer()  # taken from here: https://matplotlib.org/3.1.1/gallery/user_interfaces/canvasagg.html
        image_matrix = np.frombuffer(canvas_data, np.uint8).reshape((canvas_height, canvas_width, 4))
        image_pill = Image.frombytes("RGBA", (canvas_width, canvas_height), image_matrix)
        self.drawing.display_image(image_pill)


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
                self.myCanvas.create_line(x1, y1, x2, y2, width=2, fill='red', activefill='yellow', tags=(ID))

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

        if self.imgCount < len(self.jsonList) and self.imgCount > -1:
            self.image_iterator_current = self.jsonList[self.imgCount]
            im = self.image_iterator_current[1]
            jf = self.image_iterator_current[0]
            pattern = r"_p[0-9]{1,2}.png"

            self.currentSample = im.split("_")[0]
            #re.sub(pattern, "",im)  # don't remove this. This tracks the sample number and is used for tracking unique sample id's per sample
            iterator = self.sampleList.index(self.currentSample) + 1
            fileName = os.path.join(self.folderPath, im)
            self.drawing.display_image(Image.open(fileName))
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
                    self.myCanvas.create_oval(x1 - 6, y1 - 6, x1 + 6, y1 + 6, width=2, outline='blue', fill='blue',
                                              activefill='yellow', activeoutline='yellow',
                                              tags=(spotID, 'SpotPoint' + str(self.spotCount)))
                    self.myCanvas.create_text(x1, y1 - 5, text=spotID, fill='white', font=("Helvetica", 8, "bold"),tags=spotID)
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

        self.drawing.display_image(image_pill)

        self.Draw_Contours()

root = Tk()
model = Model()
my_gui = Application(root,model)
root.mainloop()
