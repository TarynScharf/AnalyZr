import tkinter as tk
from tkinter import *
from tkinter.ttk import *

from src.model.image_type import ImageType


class DataCaptureDialog():
    def __init__(self, view):
        self.view = view
        self.browse_for_files_window = Toplevel(self.view.master)
        self.browse_for_files_window.title("Select Images for Spot Capture")
        self.browse_for_files_window.minsize(400, 100)
        self.browse_for_files_window.lift()

        #VARIABLES
        self.json_folder_path = tk.StringVar()
        self.json_folder_path.set('')

        self.load_json_folder = IntVar()

        self.create_json_var = IntVar()

        self.Folder_Location = tk.StringVar()
        self.Folder_Location.set('')

        self.image_folder_path = tk.StringVar()
        self.image_folder_path.set('')

        # browse for images
        self.image_folder_Label = Label(self.browse_for_files_window, text="Data capture image folder")
        self.image_folder_Label.grid(column=0, row=0,sticky = 'w')

        self.image_folder_text_box = Entry(self.browse_for_files_window, width=150, textvariable=self.image_folder_path)
        self.image_folder_text_box.grid(column=1,columnspan =5, row=0,sticky = 'w')

        self.browse_for_image_folder = Button(self.browse_for_files_window, text="...", width=5, command=lambda: self.Browse('capture', self.browse_for_files_window))
        self.browse_for_image_folder.grid(column=6, row=0, padx=2, pady=5,sticky = 'w')

        self.select_image_type_label = Label(self.browse_for_files_window, text="Data capture from")
        self.select_image_type_label.grid(column=0, row=1, sticky='w')

        image_types = [type.value for type in ImageType]
        self.image_type_combobox = Combobox(self.browse_for_files_window, values=image_types)
        self.image_type_combobox.grid(column=1, row=1, padx=2, pady=5, sticky='w')

        # browse for json files
        self.load_json_folder_check_button = Checkbutton(self.browse_for_files_window, text='Load jsons separately', variable=self.load_json_folder, command=lambda: self.activate_browse_for_json_folder())
        self.load_json_folder_check_button.grid(column=0, columnspan=2, row=2, padx=2, pady=5, sticky='w')

        self.json_folder_Label = Label(self.browse_for_files_window, text="Json Folder")
        self.json_folder_Label.config(state=DISABLED)
        self.json_folder_Label.grid(column=0, row=3,sticky = 'w')

        self.json_folder_text_box = Entry(self.browse_for_files_window, width=150, textvariable=self.json_folder_path)
        self.json_folder_text_box.config(state=DISABLED)
        self.json_folder_text_box.grid(column=1,columnspan =5, row=3,sticky = 'w')

        self.browse_for_json_folder = Button(self.browse_for_files_window, text="...", width=5, command=lambda: self.Browse('json',self.browse_for_files_window))
        self.browse_for_json_folder.config(state=DISABLED)
        self.browse_for_json_folder.grid(column=6, row=3, padx=2, pady=5,sticky = 'w')

        self.create_json_files_check_button = Checkbutton(self.browse_for_files_window, text='Generate json files if missing', variable=self.create_json_var)
        self.create_json_files_check_button.grid(column = 0,columnspan=2, row=4, padx=2, pady=5,sticky = 'w')

        self.ok_load_files_for_capture = Button(self.browse_for_files_window, text="OK", width=5, command=lambda: self.load_files())
        self.ok_load_files_for_capture.grid(column=0, row=5, padx=2, pady=5,sticky = 'w')

        self.cancel_load_files_for_capture = Button(self.browse_for_files_window, text="Cancel", width=8, command=lambda: self.view.close_window(self.browse_for_files_window))
        self.cancel_load_files_for_capture.grid(column=1, row=5, padx=2, pady=5,sticky = 'w')

    def Browse(self,case_type,window):
        if case_type == 'json':
            json_folder_name = self.view.Browse(case_type,window)
            self.json_folder_location = json_folder_name
            self.json_folder_path.set(json_folder_name)
            window.lift()

        elif case_type == 'capture':
            filename = self.view.Browse(case_type,window)
            self.image_folder_path.set(filename)
            if self.load_json_folder.get() == 0:
                self.json_folder_path.set(self.image_folder_path.get())
            window.lift()

    def activate_browse_for_json_folder(self):
        if self.load_json_folder.get() == 1:
            state = NORMAL
            path = ""
        elif self.load_json_folder.get() == 0:
            state = DISABLED
            path = self.image_folder_path.get()

        self.json_folder_Label.config(state=state)
        self.json_folder_text_box.config(state=state)
        self.browse_for_json_folder.config(state=state)
        self.view.model.set_json_folder_path(path)

    def load_files(self):
        image_folder = self.image_folder_path.get()
        json_folder = self.json_folder_path.get()
        data_capture_image_type = ImageType(self.image_type_combobox.get())
        self.view.load_files(image_folder,json_folder,data_capture_image_type, self.create_json_var.get())
        self.browse_for_files_window.destroy()