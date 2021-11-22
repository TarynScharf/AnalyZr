import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.messagebox import askokcancel
from tkinter.ttk import *

from src.model.image_type import ImageType


class DataCaptureDialog():
    def __init__(self, view,drawing):
        self.view = view
        self.drawing=drawing
        self.browse_for_files_window = Toplevel(self.view.master)
        self.browse_for_files_window.title("Select Images for Data Capture")
        self.browse_for_files_window.minsize(400, 100)
        self.browse_for_files_window.lift()
        self.browse_for_files_window.grab_set()

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
        json_folder = self.json_folder_path.get()
        image_type = ImageType(self.image_type_combobox.get())
        create_json_files = self.create_json_var.get()

        if image_folder == '':
            messagebox.showinfo("Error", "Select an image folder")
            self.browse_for_files_window.lift()
            return
        if json_folder == '':
            messagebox.showinfo("Error", "Select a json file folder")
            self.browse_for_files_window.lift()
            return

        try:
            data_capture_image_type = image_type
        except Exception as e:
            messagebox.showinfo("Error", "Select an image type")
            self.browse_for_files_window.lift()
            return
        try:
            files_exist, missing_json_files = self.view.check_existence_of_images_and_jsons(image_folder, json_folder, data_capture_image_type, create_json_files)
            if files_exist:
                self.read_and_display_image_data(image_folder, json_folder, data_capture_image_type)
            else:
                if missing_json_files is not None:
                    answer = askokcancel(title='Create missing json files', message='Do you wish to create missing json files?')
                    if answer == True:
                        for file_name in missing_json_files:
                            self.view.model.create_new_json_file(file_name, data_capture_image_type, json_folder)
                        self.read_and_display_image_data(image_folder, json_folder,data_capture_image_type)
                    else:
                        messagebox.showinfo("Error", "No json files in the selected folder.")
                        self.browse_for_files_window.lift()
                        return
        except Exception as e:
            messagebox.showinfo('Error', e)
            return


        self.view.master.bind("<Left>", lambda e: self.view.PrevImage())
        self.view.master.bind("<Right>", lambda e: self.view.NextImage())
        self.view.master.bind("<Escape>", lambda e: self.drawing.UnbindMouse())
        self.view.master.bind("p", lambda e: self.drawing.BoundaryDraw())
        self.view.master.bind("s", lambda e: self.drawing.start_spot_capture())
        self.view.master.bind("a", lambda e: self.drawing.RectSpotDraw())
        self.view.master.bind("d", lambda e: self.drawing.DupDraw())
        self.view.master.bind("l", lambda e: self.drawing.DrawScale())
        self.view.master.bind("r", lambda e: self.drawing.start_region_capture())
        self.browse_for_files_window.destroy()

    def read_and_display_image_data(self,image_folder_path,json_folder_path,data_capture_image_type):
        self.view.model.set_source_folder_paths(image_folder_path, json_folder_path)
        self.view.model.read_sampleID_and_spots_from_json(data_capture_image_type,image_folder_path)
        self.view.update_data_capture_display()
        self.view.activate_data_capture_options()
        self.browse_for_files_window.destroy()

