import tkinter as tk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import *

class MeasureScaleDialog():
    def __init__(self, view, model, scale_line):
        self.view = view
        self.model = model
        self.scale_line = scale_line
        self.capture_scale_window = Toplevel(self.view.master)
        self.capture_scale_window.title("Real World Distance")
        self.capture_scale_window.minsize(200, 70)
        self.capture_scale_window.lift()
        self.capture_scale_window.grab_set()
        self.capture_scale_window.focus_set()

        #VARIABLES
        self.real_world_distance = tk.StringVar()

        #WINDOW WIDGETS
        self.scale_label = Label(self.capture_scale_window,text = "Real world distance")
        self.scale_label.grid(column=0, row=0, sticky='w')
        self.distance_entry = Entry(self.capture_scale_window, width = 10, textvariable = self.real_world_distance)
        self.distance_entry.grid(column = 1, row = 0, sticky = 'w',padx=2, pady=5)
        self.ok_button = Button(self.capture_scale_window, text = 'OK', width=5, command=lambda:self.save_drawing_object_to_json())
        self.ok_button.grid(column = 0, row = 1, sticky = 'w',padx=2, pady=5)

        self.capture_scale_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.capture_scale_window.bind('<Return>', lambda e: self.save_drawing_object_to_json())

        self.capture_scale_window.bind('<Return>', lambda e: self.save_drawing_object_to_json())

    def save_drawing_object_to_json(self):
        try:
            if not self.real_world_distance.get().isdigit():
                messagebox.showinfo('Error', 'No real world distance provided')
                return
            self.capture_scale_window.destroy()
            self.scale_line.real_world_distance = self.real_world_distance.get()
            saved = self.model.save_drawing_object_to_json(self.scale_line)
            if not saved:
                self.view.drawing.myCanvas.delete(self.scale_line.group_tag)
                raise ValueError('Linear scale already exists in image. Only one linear scale is allowed per image.')
        except Exception as e:
            self.view.open_error_message_popup_window(str(e))


    def on_closing(self):
        self.capture_scale_window.destroy()
        self.model.DeleteObject(self.scale_line.group_tag)
        self.view.drawing.myCanvas.delete(self.scale_line.group_tag)




