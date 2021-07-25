import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.messagebox import askokcancel
from tkinter.ttk import *

from src.model.image_type import ImageType


class DataCaptureDialog():
    def __init__(self, view):
        self.view = view
        self.browse_for_files_window = Toplevel(self.view.master)
        self.browse_for_files_window.title("Select Images for Data Capture")
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

        image_types = [ImageType.TL.value, ImageType.RL.value, ImageType.COLLAGE.value]
        self.image_type_combobox = Combobox(self.browse_for_files_window, values=image_types)
        self.image_type_combobox.bind("<<ComboboxSelected>>", self.activate_buttons)
        self.image_type_combobox.grid(column=1, row=1, padx=2, pady=5, sticky='w')


        # browse for json files
        self.load_json_folder_check_button = Checkbutton(self.browse_for_files_window,state=DISABLED, text='Load jsons separately', variable=self.load_json_folder, command=lambda: self.activate_browse_for_json_folder())
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

        self.create_json_files_check_button = Checkbutton(self.browse_for_files_window,state=DISABLED, text='Generate json files if missing', variable=self.create_json_var)
        self.create_json_files_check_button.grid(column = 0,columnspan=2, row=4, padx=2, pady=5,sticky = 'w')

        self.ok_load_files_for_capture = Button(self.browse_for_files_window,state=DISABLED, text="OK", width=5, command=lambda: self.load_files())
        self.ok_load_files_for_capture.grid(column=0, row=5, padx=2, pady=5,sticky = 'w')

        self.cancel_load_files_for_capture = Button(self.browse_for_files_window, text="Cancel", width=8, command=lambda: self.view.close_window(self.browse_for_files_window))
        self.cancel_load_files_for_capture.grid(column=1, row=5, padx=2, pady=5,sticky = 'w')

    def activate_buttons(self,val):
        self.create_json_files_check_button.config(state=NORMAL)
        self.load_json_folder_check_button.config(state=NORMAL)
        self.json_folder_text_box.config(state=NORMAL)
        self.json_folder_Label.config(state=NORMAL)
        self.ok_load_files_for_capture.config(state=NORMAL)
        self.browse_for_json_folder.config(state=NORMAL)

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
        if image_folder == '':
            messagebox.showinfo("Error", "Select an image folder")
            self.browse_for_files_window.lift()
            return
        json_folder = self.json_folder_path.get()
        if json_folder == '':
            messagebox.showinfo("Error", "Select a json file folder")
            self.browse_for_files_window.lift()
            return

        try:
            data_capture_image_type = ImageType(self.image_type_combobox.get())
        except Exception as e:
            messagebox.showinfo("Error", "Select a data capture image type")
            self.browse_for_files_window.lift()
            return

        create_json_files = self.create_json_var.get()
        files_exist, missing_json_files = self.check_existence_of_images_and_jsons(image_folder, json_folder, data_capture_image_type, create_json_files)
        if files_exist:
            self.read_and_display_image_data(image_folder,json_folder)
        else:
            if missing_json_files is not None:
                answer = askokcancel(title='Create missing json files',message='Do you wish to create missing json files?')

                if answer == True:
                    self.browse_for_files_window.destroy()
                    for file_name in missing_json_files:
                        self.view.model.create_new_json_file(file_name, data_capture_image_type)
                    self.read_and_display_image_data(image_folder, json_folder)

    def check_existence_of_images_and_jsons(self, image_folder_path, json_folder_path, data_capture_image_type, create_json_files):
        # Does 2 things:
        # Check for images in the folder, returns error message if there are none.
        # checks if each image has a corresponding json file. Offers to create the ones that are missing.

        if json_folder_path == '':
            json_folder_path = image_folder_path

        has_images, missing_json_files = self.view.model.check_for_images_and_jsons(image_folder_path, json_folder_path, data_capture_image_type)

        if has_images == False:
            error_message_text = f"The folder contains no png images of the type selected for data capture: {data_capture_image_type.value}."
            self.open_error_message_popup_window(error_message_text)
            return False, None

        if not missing_json_files:
            return True, None

        if create_json_files == 1:
            for file in missing_json_files:
                self.view.model.create_new_json_file(file, data_capture_image_type)
            return True, None

        return False, missing_json_files

    def read_and_display_image_data(self,image_folder_path,json_folder_path):
        self.view.model.set_source_folder_paths(image_folder_path, json_folder_path)
        self.view.model.read_sampleID_and_spots_from_json()
        self.view.update_data_capture_display()
        self.view.activate_data_capture_options()
        self.browse_for_files_window.destroy()

