import tkinter as tk
from tkinter import *
from tkinter.ttk import *

class SegmentationDialog():
    def __init__(self, view,rl_path, tl_path, rlVar, tlVar):
        self.view = view
        self.Segmentation_Window = Toplevel(self.view.master)
        self.Segmentation_Window.title("Image Segmentation Toolbox")
        self.Segmentation_Window.minsize(400, 110)
        self.Segmentation_Window.lift()

        #VARIABLES
        self.MaskFolderLocation = tk.StringVar()
        self.MaskFolderLocation.set('')

        self.mask_file_path = tk.StringVar()
        self.mask_file_path.set('')

        self.Process_Image_File_Location = tk.StringVar()
        self.Process_Image_File_Location.set('')

        self.Mask_Folder_Location = tk.StringVar()
        self.Mask_Folder_Location.set('')

        self.rl_path = rl_path
        self.tl_path = tl_path

        self.rlVar = rlVar
        self.tlVar = tlVar

        self.MaskFolderLocation = tk.StringVar()
        self.MaskFolderLocation.set('')

        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')

        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')

        # VISUAL REFERENCES FRAME
        self.visual_reference_label_frame = LabelFrame(self.Segmentation_Window, text='Visual References')
        self.visual_reference_label_frame.grid(row=0,columnspan=3, padx=2, pady=5,sticky="ew")

        self.Display_TL_Image_Button = Button(self.visual_reference_label_frame, text="Display TL Image", width=20,command=lambda: self.view.display_parent_image(1,rl_path, tl_path))
        self.Display_TL_Image_Button.grid(row=0, column=0, padx=2, pady=5)

        self.Display_RL_Image_Button = Button(self.visual_reference_label_frame, text="Display RL Image", width=20, command=lambda: self.view.display_parent_image(0,rl_path, tl_path))
        self.Display_RL_Image_Button.grid(row=0, column=1, padx=2, pady=5)

        self.rebinarise = Button(self.visual_reference_label_frame, text="Rebinarise", width=20, command=lambda: self.view.binariseImages(rl_path, tl_path, rlVar, tlVar))
        self.rebinarise.grid(row=0, column=2, padx=2, pady=5)

        # SEGMENTATION FRAME
        self.segmentation_label_frame = LabelFrame(self.Segmentation_Window, text='Image Segmentation')
        self.segmentation_label_frame.grid(columnspan=3,row=1, padx=2, pady=5,sticky="ew")

        self.Separate_Button = Button(self.segmentation_label_frame, text="Separate Grains", command=self.view.separate)
        self.Separate_Button.grid(column=0, row=0, padx=2, pady=5)

        self.breakLine = Button(self.segmentation_label_frame, text="Draw Break Line", command=self.view.drawing.DrawBreakLine)
        self.breakLine.grid(column=1, row=0, padx=2, pady=5)

        self.saveChanges = Button(self.segmentation_label_frame, text="Save Changes", command=self.view.SaveBreakChanges)
        self.saveChanges.grid(column=2, row=0, padx=2, pady=5)

        #EDIT BOUNDARIES FRAME
        self.edit_boundaries_label_frame = LabelFrame(self.Segmentation_Window, text='Edit Grain Boundaries')
        self.edit_boundaries_label_frame.grid(columnspan=3,row=2, padx=2, pady=5,sticky="ew")

        self.grain_boundary_capture = Button(self.edit_boundaries_label_frame, text="Grain Boundary Capture [p]", command=self.view.drawing.BoundaryDraw)
        self.grain_boundary_capture.grid(column=0, row=0, padx=2, pady=5)

        self.undo_delete = Button(self.edit_boundaries_label_frame, text="Undo Delete Contour", command=self.view.undo_delete_contour)
        self.undo_delete.grid(column=1, row=0, padx=2, pady=5)

        #MEASURE SHAPES FRAME
        self.Measure_Shapes_Frame = LabelFrame(self.Segmentation_Window, text='Measure Shapes')
        self.Measure_Shapes_Frame.grid(columnspan=3, row=3, padx=2, pady=5,sticky="ew")

        self.Mask_Label = Label(self.Measure_Shapes_Frame, text="Mask Save Location")
        self.Mask_Label.grid(column=0, row=0,sticky='w')

        self.MaskTextBox = Entry(self.Measure_Shapes_Frame, width=100, textvariable=self.MaskFolderLocation)
        self.MaskTextBox.grid(column=1, row=0,sticky='w')

        self.browseMask = Button(self.Measure_Shapes_Frame, text="...", width=5, command=lambda: self.Browse('Mask',self.Segmentation_Window))
        self.browseMask.grid(column=2, row=0, padx=2, pady=5,sticky='w')

        self.saveMask = Button(self.Measure_Shapes_Frame, text="Save Mask", width = 10,command=lambda: self.view.save_mask(self.MaskFolderLocation.get()))
        self.saveMask.grid(column=3, row=0, padx=2, pady=5,sticky='w')

        self.Process_Image = Label(self.Measure_Shapes_Frame, text="Browse for Mask Image")
        self.Process_Image.grid(column=0, row=1,sticky='w')

        self.File_TextBox = Entry(self.Measure_Shapes_Frame, width=100, textvariable=self.Process_Image_File_Location)
        self.File_TextBox.grid(column=1, row=1,sticky='w')

        self.Browse_File = Button(self.Measure_Shapes_Frame, text="...", width=5, command=lambda: self.Browse('File', self.Segmentation_Window))
        self.Browse_File.grid(column=2, row=1, padx=3, pady=5,sticky='w')

        self.Display_Mask = Button(self.Measure_Shapes_Frame, text="Display Mask Image", width=20, command=lambda: self.display_mask())
        self.Display_Mask.grid(column=3, row=1, padx=3, pady=5,sticky='w')

        self.Process_Folder = Label(self.Measure_Shapes_Frame, text="Process Mask Folder")
        self.Process_Folder.grid(column=0, row=2,sticky='w')

        self.Folder_TextBox = Entry(self.Measure_Shapes_Frame, width=100, textvariable=self.Mask_Folder_Location)
        self.Folder_TextBox.grid(column=1, row=2,sticky='w')

        self.Browse_Folder = Button(self.Measure_Shapes_Frame, text="...", width=5, command=lambda: self.Browse('Folder'))
        self.Browse_Folder.grid(column=2, row=2, padx=3, pady=5,sticky='w')

        self.Process_Folder = Button(self.Measure_Shapes_Frame, text="Process Folder", width=20, command=lambda: self.model.ProcessFolder())
        self.Process_Folder.grid(column=3, row=2, padx=3, pady=5,sticky='w')

        self.measureShapes = Button(self.Measure_Shapes_Frame, text="Measure Shapes", command=self.view.start_measure_shapes(self.mask_file_path.get()))
        self.measureShapes.grid(column=0, row=3, padx=2, pady=5,sticky='w')

        self.moveSpot = Button(self.Measure_Shapes_Frame, text="Reposition spot", command=self.view.drawing.PointMove)
        self.moveSpot.grid(column=1, row=3, padx=2, pady=5, sticky='w')

        # SAVE RESULTS FRAME
        self.Save_Results_Frame = LabelFrame(self.Segmentation_Window, text='Measure Shapes')
        self.Save_Results_Frame.grid(columnspan=3, row=4, padx=2, pady=5,sticky="ew")

        self.pushDB = Button(self.Save_Results_Frame, text="Push to DB", command=self.view.model.push_shape_measurements_to_database)
        self.pushDB.grid(column=0, row=0, padx=2, pady=5)

        self.write_to_csv_button = Button(self.Save_Results_Frame, text="Save to CSV", command=self.view.model.write_to_csv)
        self.write_to_csv_button.grid(column=1, row=0, padx=2, pady=5)


    def binarise_images(self):
        RLPath = self.RLPath.get()
        TLPath = self.TLPath.get()
        rlVar = self.rlVar.get()
        tlVar = self.tlVar.get()
        self.view.binariseImages(RLPath, TLPath, rlVar, tlVar)

    def Browse(self,case_type, window):
        if case_type == 'Mask':
            folderName = self.view.Browse(case_type, window)
            self.MaskFolderLocation.set(folderName)
            self.MaskTextBox.delete(0, END)
            self.MaskTextBox.insert(0, folderName)

        elif case_type == 'Folder':
            folderName = self.view.Browse(case_type, self.Segmentation_Window)
            self.Folder_Location.set(folderName)
            self.Folder_TextBox.delete(0, END)
            self.Folder_TextBox.insert(0, folderName)

        elif case_type == 'File':
            filename = self.view.Browse(case_type, self.Segmentation_Window)
            self.mask_file_path.set(filename)
            self.File_TextBox.delete(0, END)
            self.File_TextBox.insert(0, filename)

    def display_mask(self):
        rl_path, tl_path, mask_path = self.view.DisplayMask(self.mask_file_path.get())
        #self.RLTextBox.delete(0, END)
        #self.RLTextBox.insert(0, rl_path)
        #self.TLTextBox.delete(0, END)
        #self.TLTextBox.insert(0, tl_path)
        self.MaskTextBox.delete(0, END)
        self.MaskTextBox.insert(0, mask_path)