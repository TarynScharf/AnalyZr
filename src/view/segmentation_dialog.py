import json
import os
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *

from src.model import FileUtils
from src.model.image_type import ImageType
from src.model.json_data import JsonData
from src.model.mask_scroll_instance import MaskScrollInstance


class SegmentationDialog():
    def __init__(self, view):
        self.view = view
        self.Segmentation_Window = Toplevel(self.view.master)
        self.Segmentation_Window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.Segmentation_Window.title("Image Segmentation Toolbox")
        self.Segmentation_Window.minsize(400, 110)
        self.Segmentation_Window.attributes("-topmost", 1)
        self.Segmentation_Window.grab_set()

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

        self.TLPath = tk.StringVar()
        self.TLPath.set('')
        self.tlVar = IntVar()

        self.list_of_grain_numbers= ['all']


        # VISUAL REFERENCES FRAME

        self.binarisation_frame = LabelFrame(self.Segmentation_Window, text='Visual References')
        self.binarisation_frame.grid(row=0, columnspan=3, padx=2, pady=5, sticky="ew")

        self.RL_Label = Label(self.binarisation_frame, text="RL Image")
        self.RL_Label.grid(column=0, row=0)

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

        self.loadJson = Button(self.binarisation_frame, text="Load Json Files", width=16, command=lambda: self.view.set_json_folder_path('json',self.view.myFrame))
        self.loadJson.config()
        self.loadJson.grid(column=1, row=2, padx=80, pady=5, sticky='w')

        self.showSpots = Button(self.binarisation_frame, text="Load Spots", width=10,command=lambda: self.load_spots())
        self.showSpots.config(state=HIDDEN)
        self.showSpots.grid(column=1, row=2, padx=200, pady=5, sticky='w')

        self.removeBoundariesWithoutSpotsButton = Button(self.binarisation_frame, text="Remove Boundaries without Spots", width=30,command=lambda: self.remove_boundaries_without_spots())
        self.removeBoundariesWithoutSpotsButton.config(state=HIDDEN)
        self.removeBoundariesWithoutSpotsButton.grid(column=1, row=2, padx=300, pady=5, sticky='w')

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

        self.Display_Mask = Button(self.Measure_Shapes_Frame, text="Load Mask Image", width=20, command=lambda: self.display_mask())
        self.Display_Mask.grid(column=3, row=1, padx=3, pady=5,sticky='w')

        self.Process_Folder = Label(self.Measure_Shapes_Frame, text="Process Mask Folder")
        self.Process_Folder.grid(column=0, row=2,sticky='w')

        self.Folder_TextBox = Entry(self.Measure_Shapes_Frame, width=100, textvariable=self.Mask_Folder_Location)
        self.Folder_TextBox.grid(column=1, row=2,sticky='w')

        self.Browse_Folder = Button(self.Measure_Shapes_Frame, text="...", width=5, command=self.browse_for_mask_folder)
        self.Browse_Folder.grid(column=2, row=2, padx=3, pady=5,sticky='w')

        self.Process_Folder = Button(self.Measure_Shapes_Frame, text="Process Folder", width=20, command=self.process_mask_folder)
        self.Process_Folder.grid(column=3, row=2, padx=3, pady=5,sticky='w')

        self.measureShapes = Button(self.Measure_Shapes_Frame, text="Measure Shapes", command=self.measure_shapes)
        self.measureShapes.config(state=DISABLED)
        self.measureShapes.grid(column=0, row=3, padx=2, pady=5,sticky='w')

        self.moveSpot = Button(self.Measure_Shapes_Frame, text="Reposition spot [q]", command=self.view.drawing.RepositionObject)
        self.moveSpot.config(state=DISABLED)
        self.moveSpot.grid(column=1, row=3, padx=2, pady=5, sticky='w')

        self.ShowGrainText = Label(self.Measure_Shapes_Frame, text="Isolate selected grain")
        self.ShowGrainText.grid(column=1, row=3, padx=130, pady=5, sticky='w')
        self.ShowGrainText.config(state=DISABLED)
        self.ShowGrainCombobox = Combobox(self.Measure_Shapes_Frame, values = self.list_of_grain_numbers)
        self.ShowGrainCombobox.config(state= DISABLED)
        self.ShowGrainCombobox.grid(column=1, row=3, padx=250, pady=5, sticky='w')
        self.ShowGrainCombobox.bind('<<ComboboxSelected>>', self.DisplaySelectedGrain)


        self.view.master.unbind("s")
        self.view.master.unbind("a")
        self.view.master.unbind("d")
        self.view.master.unbind("<Left>")
        self.view.master.unbind("<Right>")
        self.view.master.unbind("l")
        self.view.master.bind("p", lambda e: self.view.drawing.BoundaryDraw())
        self.view.master.unbind("q")
        self.view.master.bind("b", lambda e: self.view.drawing.DrawBreakLine())
        self.view.master.bind("s", lambda e: self.view.save_image())

    def remove_boundaries_without_spots(self):
        self.view.remove_boundaries_without_spots()


    def DisplaySelectedGrain(self, event):
        combobox_value = self.ShowGrainCombobox.get()
        self.view.DisplaySelectedGrain(combobox_value)

    def browse_for_mask_folder(self):
        self.Segmentation_Window.grab_release()
        json_folder_path = self.view.get_json_path()
        if json_folder_path == None:
            return
        self.Browse('Folder')
        mask_folder_path = self.Folder_Location.get()
        scroll = MaskScrollInstance(self.view)
        scroll.create_mask_list(mask_folder_path)
        source_files = scroll.create_source_file_dictionary(json_folder_path)
        if not source_files:
            self.update_textbox(self.Folder_TextBox,'')
            return
        self.view.model.threshold = None
        self.set_shortcuts_for_mask_scrolling(scroll)
        self.view.NextMaskImage(scroll, self)

        self.moveSpot.config(state=NORMAL)
        self.breakLine.config(state=NORMAL)
        self.saveMask.config(state = NORMAL)
        self.Separate_Button.config(state = NORMAL)
        self.saveChanges.config(state = NORMAL)
        self.undo_delete.config(state = NORMAL)
        self.grain_boundary_capture.config(state = NORMAL)
        self.BinariseButton.config(state=NORMAL)

    def load_spots(self):
        mask_path = self.mask_file_path.get()
        rl_path = self.RLPath.get()
        tl_path = self.TLPath.get()
        json_base_name = None

        if mask_path != '':
            pattern = '_mask_'
            match = re.search(pattern,mask_path)
            json_base_name = mask_path[0:match.start()]

        elif rl_path !='' and tl_path !='':
            rl_path_split = rl_path.split('_')
            tl_path_split  = tl_path.split('_')
            rl_base_name = '_'.join(rl_path_split[0:-1])
            tl_base_name = '_'.join(tl_path_split[0:-1])
            if rl_base_name != tl_base_name:
                messagebox("RL and TL images do not have the same base name.")
                return
            json_base_name = rl_base_name

        elif self.RLPath.get() == '' and self.TLPath.get() =='':
            messagebox("No mask, RL or TL image selected.")
            return

        elif self.RLPath.get != '':
            rl_path = self.RLPath.get().split('_')
            json_base_name = '_'.join(rl_path[0:- 1])
        elif self.TLPath.get !='':
            tl_path = self.TLPath.get().split('_')
            json_base_name = '_'.join(tl_path[0:- 1])

        self.view.load_spots(json_base_name)
        self.moveSpot.config(state=NORMAL)
        self.removeBoundariesWithoutSpotsButton.config(state=NORMAL)


    def set_shortcuts_for_mask_scrolling(self, scroll_instance):
        self.view.master.bind("<Left>", lambda e: self.view.PrevMaskImage(scroll_instance,self))
        self.view.master.bind("<Right>", lambda e: self.view.NextMaskImage(scroll_instance,self))
        self.view.master.bind("<Escape>", lambda e: self.drawing.UnbindMouse())
        self.view.master.bind("p", lambda e: self.view.drawing.BoundaryDraw())
        self.view.master.bind("q", lambda e: self.view.drawing.RepositionObject())
        self.view.master.bind("b", lambda e: self.view.drawing.DrawBreakLine())
        self.view.master.bind("s", lambda e: self.view.save_image())
        self.view.drawing.myCanvas.bind("<Button-3>", self.view.drawing.DeleteObject)

    def update_binarisation_button_availability(self):
        if self.rlVar.get() == 1 or self.tlVar.get() == 1:
            self.BinariseButton.config(state = NORMAL)
        else:
            self.BinariseButton.config(state=DISABLED)

    def process_mask_folder(self):
        mask_file_folder = self.Mask_Folder_Location.get()
        self.view.process_all_masks_in_folder(mask_file_folder)

    def binarise_images(self):
        self.Segmentation_Window.grab_release()
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
        self.moveSpot.config(state = DISABLED)
        self.mask_file_path.set('')
        self.update_textbox(self.mask_filepath_textbox, '')

    def display_image(self, image_type):
        RLPath = self.RLPath.get()
        TLPath = self.TLPath.get()
        rlVar = self.rlVar.get()
        tlVar = self.tlVar.get()

        if image_type==ImageType.RL:
            image_path = self.RLPath.get()
        elif image_type == ImageType.TL:
            image_path = self.TLPath.get()
        elif image_type == ImageType.MASK:
            image_path = self.mask_file_path.get()
        self.view.model.set_image_details(image_path, image_type)

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
            #self.mask_file_path.set(path)
            #self.update_textbox(self.mask_filepath_textbox,path)
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
            self.view.model.set_image_details(path, ImageType.MASK)
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
        self.Segmentation_Window.grab_release()
        if self.view.model.json_folder_path == None or self.view.model.json_folder_path == '':
            messagebox.showinfo('Error', 'No json folder has been selected.')
            return
        mask_path = self.mask_file_path.get()
        self.view.DisplayMask(mask_path)
        self.update_textbox(self.mask_filepath_textbox,mask_path)
        region_id = JsonData.get_region_id_from_file_path(ImageType.MASK,mask_path)
        json_file = JsonData.get_json_file_name_from_collage_path(ImageType.MASK, mask_path)
        data = JsonData.load_all(os.path.join(self.view.model.json_folder_path,json_file))
        image_region = data.get_image_region(region_id)
        if image_region == None:
            messagebox.showinfo('Error', f'Image Region {region_id} cannot be found in file {os.path.join(self.view.model.json_folder_path,json_file)}.\n'
                                'The mask cannot be displayed.')
            return
        tl_path = image_region.tl_path if image_region.tl_path is not None else ""
        rl_path = image_region.rl_path if image_region.rl_path is not None else ""
        self.update_textbox(self.TLTextBox, tl_path)
        self.update_textbox(self.RLTextBox, rl_path)
        self.measureShapes.config(state=NORMAL)

        self.deactivate_grain_selection_combobox()

    def measure_shapes(self):
        self.view.master.bind("q", lambda e: self.view.drawing.RepositionObject())
        self.moveSpot.config(state=NORMAL)

        mask_path = self.mask_file_path.get().strip()
        if mask_path != None and mask_path != '':
            self.display_mask()

        self.view.start_measure_shapes(mask_path)
        self.moveSpot.config(state=NORMAL)

        self.activate_grain_selection_combobox()

    def activate_grain_selection_combobox(self):
        grain_numbers = self.view.get_grain_labels()
        self.list_of_grain_numbers.extend(grain_numbers[1:])
        self.ShowGrainCombobox['values'] = self.list_of_grain_numbers
        self.ShowGrainCombobox.config(state='readonly')
        self.ShowGrainText.config(state=NORMAL)

    def deactivate_grain_selection_combobox(self):
        self.ShowGrainCombobox.config(state=DISABLED)
        self.ShowGrainText.config(state=DISABLED)



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

        json_folder_path = self.view.model.json_folder_path
        if json_folder_path is None or json_folder_path == '':
            messagebox.showinfo('No json folder has been loaded')
            return

        json_unique_name, region_id = self.view.model.identify_json_file(image_type,path)
        if json_unique_name == None or region_id == None:
            return

        mask_file_name = FileUtils.get_name_without_extension(json_unique_name) + "_mask_" + region_id
        mask_path = os.path.join(mask_folder_path, mask_file_name + '.png')

        json_file_path = os.path.join(json_folder_path,json_unique_name)
        json_data = JsonData.load_all(json_file_path)
        image_region_object = json_data.get_image_region(region_id)
        image_region_object.mask_path = mask_path
        image_region_object.rl_path = self.view.model.rl_path
        image_region_object.tl_path = self.view.model.tl_path
        json_data.save_changes_to_region(region_id,image_region_object,json_file_path) #if region id is '' then get the first region id

        self.view.model.set_mask_path(mask_path)
        self.view.model.write_mask_to_png(mask_path)

    def on_closing(self):
        self.Segmentation_Window.destroy()
        self.view.mainMenu.entryconfig('Data Capture', state=NORMAL)
        self.view.mainMenu.entryconfig('Segment Images', state=NORMAL)


