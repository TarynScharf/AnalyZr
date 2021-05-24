import os
import tkinter as tk
from tkinter import *
from tkinter.ttk import *

from src.model import FileUtils
from src.model.image_type import ImageType
from src.model.json_data import JsonData
from src.model.region_measurements import RegionMeasurement


class MeasurementDialog():
    def __init__(self, view,measurements):
        self.view = view
        self.measurement_window = Toplevel(self.view.master)
        self.measurement_window.title("Image Segmentation Toolbox")
        self.measurement_window.minsize(400, 110)
        self.measurement_window.lift()

        headers = RegionMeasurement.get_headers()
        number_of_columns = len(headers)
        for j,header in enumerate(headers):
            e = Label(self.measurement_window, text=header)
            e.grid(row=0, column=j)

        for i in range(len(measurements)):
            row_entry = measurements[i].as_list()
            for j in range(number_of_columns):
                e = Label(self.measurement_window,text = row_entry[j])
                e.grid(row=i+1, column=j)

        self.Save_Results_Frame = LabelFrame(self.measurement_window, text='Measure Shapes')
        self.Save_Results_Frame.grid(columnspan=number_of_columns, row=4, padx=2, pady=5, sticky="ew")

        self.pushDB = Button(self.measurement_window, text="Push to DB", command=self.view.model.push_shape_measurements_to_database)
        self.pushDB.grid(column=0, row=0, padx=2, pady=5)

        self.write_to_csv_button = Button(self.measurement_window, text="Save to CSV", command=self.view.model.write_to_csv)
        self.write_to_csv_button.grid(column=1, row=0, padx=2, pady=5)