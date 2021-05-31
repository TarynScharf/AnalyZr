import os
import tkinter as tk
from tkinter import *
from tkinter.ttk import *

from src.model import FileUtils
from src.model.image_type import ImageType
from src.model.json_data import JsonData


class SegmentationDialog():
    def __init__(self, view):
        self.view = view
        self.Segmentation_Window = Toplevel(self.view.master)
        self.Segmentation_Window.title("Image Segmentation Toolbox")
        self.Segmentation_Window.minsize(400, 110)
        self.Segmentation_Window.lift()

        #VARIABLES

        self.mask_file_path = tk.StringVar()
        self.mask_file_path.set('')

        self.mask_file_path = tk.StringVar()
        self.mask_file_path.set('')

        self.Mask_Folder_Location = tk.StringVar()
        self.Mask_Folder_Location.set('')

        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')

        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')

        self.RLPath = tk.StringVar()
        self.RLPath.set('')
        self.rlVar = IntVar()
        #self.RLPath.set('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Inv1_Images/granite/189937_spots/Cropped/189937_spots_p2_RL_SO9e8wLIz.png')

        self.TLPath = tk.StringVar()
        self.TLPath.set('')
        #self.TLPath.set('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Inv1_Images/granite/189937_spots/Cropped/189937_spots_p2_TL_HQ1Cl19PT.png')
        self.tlVar = IntVar()


        # VISUAL REFERENCES FRAME

        self.binarisation_frame = LabelFrame(self.Segmentation_Window, text='Visual References')
        self.binarisation_frame.grid(row=0, columnspan=3, padx=2, pady=5, sticky="ew")

        self.RL_Label = Label(self.binarisation_frame, text="RL Image")
        self.RL_Label.grid(column=0, row=0)
        # self.RLPath.set('/home/matthew/Code/ZirconSeparation/test/images/88411_spots_p1_RL__WqO4ozqE.png')

        self.RLTextBox = Entry(self.binarisation_frame, width=150, textvariable=self.RLPath)
        self.RLTextBox.grid(column=1, row=0)
        self.browseRL = Button(self.binarisation_frame, text="...", width=5, command=lambda: self.Browse('RL'))
        self.browseRL.grid(column=3, row=0, padx=2, pady=5)

        self.rlCheckButton = Checkbutton(self.binarisation_frame, text='Binarise  RL', variable=self.rlVar, command = self.update_binarisation_button_availability)
        self.rlCheckButton.grid(column=4, row=0, padx=2, pady=5)
        self.Display_RL_Image_Button = Button(self.binarisation_frame, text="Display", width=8, command=lambda: self.display_image(ImageType.RL))
        self.Display_RL_Image_Button.grid(column=5, row=0, padx=2, pady=5)

        self.TL_Label = Label(self.binarisation_frame, text="TL Image")
        self.TL_Label.grid(column=0, row=1)

        self.TLTextBox = Entry(self.binarisation_frame, width=150, textvariable=self.TLPath)
        self.TLTextBox.grid(column=1, row=1)
        self.browseTL = Button(self.binarisation_frame, text="...", width=5, command=lambda: self.Browse('TL'))
        self.browseTL.grid(column=3, row=1, padx=2, pady=5)

        self.tlCheckButton = Checkbutton(self.binarisation_frame, text='Binarise TL', variable=self.tlVar,command = self.update_binarisation_button_availability)
        self.tlCheckButton.grid(column=4, row=1, padx=2, pady=5)
        self.Display_TL_Image_Button = Button(self.binarisation_frame, text="Display", width=8,
                                              command=lambda: self.display_image(ImageType.TL))
        self.Display_TL_Image_Button.grid(column=5, row=1, padx=2, pady=5)

        self.BinariseButton = Button(self.binarisation_frame, text="Binarise", command=self.binarise_images)
        self.BinariseButton.config(state=DISABLED)
        self.BinariseButton.grid(column=0, row=2, padx=2, pady=5)

        self.saveMask = Button(self.binarisation_frame, text="Save Mask", width = 10, command=lambda: self.save_mask())
        self.saveMask.config(state=DISABLED)
        self.saveMask.grid(column=1, row=2, padx=2, pady=5,sticky='w')

        #EDIT BOUNDARIES FRAME
        self.segmentation_label_frame = LabelFrame(self.Segmentation_Window, text='Image Segmentation')
        self.segmentation_label_frame.grid(columnspan=3,row=1, padx=2, pady=5,sticky="ew")

        self.Separate_Button = Button(self.segmentation_label_frame, text="Separate Grains", command=self.view.separate)
        self.Separate_Button.config(state=DISABLED)
        self.Separate_Button.grid(column=0, row=0, padx=2, pady=5)

        self.breakLine = Button(self.segmentation_label_frame, text="Draw Break Line", command=self.view.drawing.DrawBreakLine)
        self.breakLine.config(state=DISABLED)
        self.breakLine.grid(column=1, row=0, padx=2, pady=5)

        self.saveChanges = Button(self.segmentation_label_frame, text="Save Changes", command=self.view.SaveBreakChanges)
        self.saveChanges.config(state=DISABLED)
        self.saveChanges.grid(column=2, row=0, padx=2, pady=5)

        self.grain_boundary_capture = Button(self.segmentation_label_frame, text="Grain Boundary Capture [p]", command=self.view.drawing.BoundaryDraw)
        self.grain_boundary_capture.config(state = DISABLED)
        self.grain_boundary_capture.grid(column=3, row=0, padx=2, pady=5)

        self.undo_delete = Button(self.segmentation_label_frame, text="Undo Delete Contour", command=self.view.undo_delete_contour)
        self.undo_delete.config(state=DISABLED)
        self.undo_delete.grid(column=4, row=0, padx=2, pady=5)

        #MEASURE SHAPES FRAME
        self.Measure_Shapes_Frame = LabelFrame(self.Segmentation_Window, text='Measure Shapes')
        self.Measure_Shapes_Frame.grid(columnspan=3, row=3, padx=2, pady=5,sticky="ew")

        self.Process_Image = Label(self.Measure_Shapes_Frame, text="Browse for Mask Image")
        self.Process_Image.grid(column=0, row=1,sticky='w')

        self.mask_filepath_textbox = Entry(self.Measure_Shapes_Frame, width=100, textvariable=self.mask_file_path)
        self.mask_filepath_textbox.grid(column=1, row=1, sticky='w')

        self.Browse_File = Button(self.Measure_Shapes_Frame, text="...", width=5, command=lambda: self.Browse('File'))
        self.Browse_File.grid(column=2, row=1, padx=3, pady=5,sticky='w')

        self.Display_Mask = Button(self.Measure_Shapes_Frame, text="Display Mask Image", width=20, command=lambda: self.display_mask())
        self.Display_Mask.grid(column=3, row=1, padx=3, pady=5,sticky='w')

        self.Process_Folder = Label(self.Measure_Shapes_Frame, text="Process Mask Folder")
        self.Process_Folder.grid(column=0, row=2,sticky='w')

        self.Folder_TextBox = Entry(self.Measure_Shapes_Frame, width=100, textvariable=self.Mask_Folder_Location)
        self.Folder_TextBox.grid(column=1, row=2,sticky='w')

        self.Browse_Folder = Button(self.Measure_Shapes_Frame, text="...", width=5, command=lambda: self.Browse('Folder'))
        self.Browse_Folder.grid(column=2, row=2, padx=3, pady=5,sticky='w')

        self.Process_Folder = Button(self.Measure_Shapes_Frame, text="Process Folder", width=20, command=lambda: self.process_mask_folder)
        self.Process_Folder.grid(column=3, row=2, padx=3, pady=5,sticky='w')

        self.measureShapes = Button(self.Measure_Shapes_Frame, text="Measure Shapes", command=self.measure_shapes)
        self.measureShapes.config(state=DISABLED)
        self.measureShapes.grid(column=0, row=3, padx=2, pady=5,sticky='w')

        self.moveSpot = Button(self.Measure_Shapes_Frame, text="Reposition spot", command=self.view.drawing.PointMove)
        self.moveSpot.config(state=DISABLED)
        self.moveSpot.grid(column=1, row=3, padx=2, pady=5, sticky='w')

    def update_binarisation_button_availability(self):
        if self.rlVar.get() == 1 or self.tlVar.get() == 1:
            self.BinariseButton.config(state = NORMAL)
        else:
            self.BinariseButton.config(state=DISABLED)

    def process_mask_folder(self):
        mask_file_folder = self.Mask_Folder_Location.get()
        self.view.process_all_masks_in_folder(mask_file_folder)

    def binarise_images(self):
        RLPath = self.RLPath.get()
        TLPath = self.TLPath.get()
        rlVar = self.rlVar.get()
        tlVar = self.tlVar.get()
        self.view.binariseImages(RLPath, TLPath, rlVar, tlVar)
        self.saveMask.config(state=NORMAL)
        self.Separate_Button.config(state=NORMAL)
        self.breakLine.config(state=NORMAL)
        self.saveChanges.config(state=NORMAL)
        self.grain_boundary_capture.config(state=NORMAL)
        self.undo_delete.config(state=NORMAL)
        self.measureShapes.config(state=NORMAL)

    def display_image(self, image_type):
        image = self.view.model.set_current_image(image_type)
        self.view.drawing.display_image(image)

    def Browse(self,case_type):

        path = self.view.Browse(case_type, self.Segmentation_Window)

        if case_type == 'RL':
            self.RLPath.set(path)
            self.update_textbox(self.RLTextBox,path)
            self.view.model.set_image_details(path, ImageType.RL)

        if case_type == 'TL':
            self.TLPath.set(path)
            self.update_textbox(self.TLTextBox, path)
            self.view.model.set_image_details(path, ImageType.TL)

        if case_type == 'Mask':
            self.mask_file_path.set(path)
            self.update_textbox(self.mask_filepath_textbox,path)
            self.view.model.set_image_details(path, ImageType.MASK)
            self.measureShapes.config(state=NORMAL)
            self.saveMask.config(state=NORMAL)
            self.Separate_Button.config(state=NORMAL)
            self.breakLine.config(state=NORMAL)
            self.saveChanges.config(state=NORMAL)
            self.grain_boundary_capture.config(state=NORMAL)
            self.undo_delete.config(state=NORMAL)
            self.measureShapes.config(state=NORMAL)

        elif case_type == 'Folder':
            self.Folder_Location.set(path)
            self.update_textbox(self.Folder_TextBox, path)
            self.measureShapes.config(state=NORMAL)

        elif case_type == 'File':
            self.mask_file_path.set(path)
            self.update_textbox(self.mask_filepath_textbox, path)
            self.measureShapes.config(state=NORMAL)
            self.saveMask.config(state=NORMAL)
            self.Separate_Button.config(state=NORMAL)
            self.breakLine.config(state=NORMAL)
            self.saveChanges.config(state=NORMAL)
            self.grain_boundary_capture.config(state=NORMAL)
            self.undo_delete.config(state=NORMAL)
            self.measureShapes.config(state=NORMAL)

        return path

    def display_mask(self):
        self.view.DisplayMask(self.mask_file_path.get())
        self.update_textbox(self.mask_filepath_textbox, self.mask_file_path.get())
        self.update_textbox(self.TLTextBox, self.view.model.tl_path)
        self.update_textbox(self.RLTextBox, self.view.model.rl_path)
        self.measureShapes.config(state=NORMAL)

    def measure_shapes(self):
        mask_path = self.mask_file_path.get()
        self.view.start_measure_shapes(mask_path)
        self.moveSpot.config(state=NORMAL)

    def update_textbox(self, textbox, text_string):
        textbox.delete(0,END)
        textbox.insert(0,text_string)

    def save_mask(self):
        mask_folder_path = self.Browse('Mask')

        if self.view.model.rl_path:
            path = self.view.model.rl_path
            image_type = ImageType.RL
        elif self.view.model.tl_path:
            path = self.view.model.tl_path
            image_type = ImageType.TL

        region_id = JsonData.get_region_id_from_file_path(image_type, path)
        json_unique_name = JsonData.get_json_file_name_from_path(image_type,path)
        mask_file_name = FileUtils.get_name_without_extension(json_unique_name) + "_mask"
        if region_id is not None:
           mask_file_name +=f'_{region_id}'

        mask_path = os.path.join(mask_folder_path,mask_file_name+'.png')
        json_folder_path = self.view.model.json_folder_path
        if json_folder_path is None:
            self.view.open_error_message_popup_window('No json folder has been loaded')
            return

        json_file_path = os.path.join(json_folder_path,json_unique_name)
        json_data = JsonData.load_all(json_file_path)
        image_region_object = json_data.get_image_region(region_id)
        image_region_object.mask_path = mask_path
        json_data.save_changes_to_region(region_id,image_region_object,json_file_path) #if region id is '' then get the first region id

        self.view.model.set_mask_path(mask_path)
        self.view.model.write_mask_to_png(mask_path)


