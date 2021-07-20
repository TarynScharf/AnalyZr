import tkinter as tk
from tkinter import *
from tkinter import filedialog
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

    def save_drawing_object_to_json(self):
        if self.real_world_distance.get().isdigit:
            self.scale_line.real_world_distance = self.real_world_distance.get()
            self.model.save_drawing_object_to_json(self.scale_line)
            self.capture_scale_window.destroy()
        else:
            raise ValueError(f'No real world distance provided')

    def on_closing(self):
        self.capture_scale_window.destroy()
        self.model.DeleteObject(self.scale_line.group_tag)
        self.view.drawing.myCanvas.delete(self.scale_line.group_tag)




