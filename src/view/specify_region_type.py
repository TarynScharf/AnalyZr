import tkinter as tk
from tkinter.ttk import *
from tkinter import *

from src.model.image_type import ImageType

class RegionTypeDialog():
    def __init__(self, view, model, rectangle):
        self.rectangle = rectangle
        self.view = view
        self.model = model
        self.regionCaptureWindow = Toplevel(self.view.master)
        self.regionCaptureWindow.grab_set()
        self.regionCaptureWindow.title("Specify Image Region Type")
        self.regionCaptureWindow.minsize(300, 100)
        self.regionCaptureLabel = Label(self.regionCaptureWindow, text='Region Type')
        self.regionCaptureLabel.grid(column=0, row=0)
        self.regionCaptureWindow.lift()
        image_types = [ImageType.TL.value, ImageType.RL.value]
        self.region_type_combobox = Combobox(self.regionCaptureWindow, values=image_types)
        self.region_type_combobox.grid(column=1, row=0, padx=2, pady=5, sticky='w')
        self.ok_button = Button(self.regionCaptureWindow, text='OK', command=self.close_dialog)
        self.ok_button.grid(column=0, row=1, padx=2, pady=5, sticky='w')

    def close_dialog(self):
        self.rectangle.type = self.region_type_combobox.get()
        self.view.drawing.draw_interactive_rectange(self.rectangle)
        self.view.model.save_drawing_object_to_json(self.rectangle)
        self.regionCaptureWindow.destroy()

