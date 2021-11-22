import os
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

from src.model import FileUtils
from src.model.image_type import ImageType
from src.model.json_data import JsonData
from src.model.region_measurements import RegionMeasurement

class MeasurementDialog():
    def __init__(self, view,measurements):
        self.measurements = measurements
        self.view = view
        self.measurement_window = Toplevel(self.view.master)
        self.measurement_window.title("Image Segmentation Toolbox")
        self.measurement_window.minsize(400, 110)
        self.measurement_window.lift()
        self.measurement_window.grab_set()

        self.buttons_frame = tk.Frame(self.measurement_window, width=400, height=150)
        self.buttons_frame.grid(row=0, column=0,sticky='w')

        self.pushDB = Button(self.buttons_frame, text="Push to DB", command=self.write_to_database)
        self.pushDB.grid(column=0, row=0, padx=2, pady=5, sticky='w')

        self.write_to_csv_button = Button(self.buttons_frame, text="Save to CSV", command=self.write_to_csv)
        self.write_to_csv_button.grid(column=1, row=0, padx=2, pady=5, sticky='w')

        self.canvas_frame = tk.Frame(self.measurement_window, width=400, height=50)
        self.canvas_frame.grid(row=1, column=0, sticky='nsew')

        self.measurement_window.grid_columnconfigure(0, weight=1)
        self.measurement_window.grid_rowconfigure(1,weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = Canvas(self.canvas_frame, bg="white")
        self.canvas.grid(row=0, column=0, sticky='nsew')

        self.vScroll = Scrollbar(self.canvas_frame, orient='vertical', command=self.canvas.yview)
        self.hScroll = Scrollbar(self.canvas_frame, orient='horizontal', command=self.canvas.xview)
        self.vScroll.grid(row=0, column=1, sticky='ns')
        self.hScroll.grid(row=1, column=0, sticky='ew')

        self.table_frame = tk.Frame(self.canvas, width=400, height=150)
        self.canvas.create_window((0, 0), window=self.table_frame)
        self.table_frame.bind('<Configure>',self.on_frame_configure)
        self.canvas.configure(yscrollcommand=self.vScroll.set)
        self.canvas.configure(xscrollcommand=self.hScroll.set)

        headers = RegionMeasurement.get_headers()
        number_of_columns = len(headers)
        for j,header in enumerate(headers):
                e = Label(self.table_frame, text=header, anchor='w', justify=LEFT)
                e.grid(row=0, column=j, sticky = 'w', padx=5)

        for i in range(len(measurements)):
            row_entry = measurements[i].as_list()
            for j in range(number_of_columns):
                    e = Label(self.table_frame,text = str(row_entry[j]),anchor='w',justify=LEFT)
                    e.grid(row=i+1, column=j, sticky='w', padx=5)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def write_to_csv(self,):
        filepath = filedialog.asksaveasfilename(defaultextension = '.csv', filetypes = [("CSV Files","*.csv")], title="Save As")
        self.view.model.write_to_csv(filepath, self.measurements)

    def write_to_database(self):
        self.view.ensure_database_path_set()
        try:
            self.view.model.push_shape_measurements_to_database(self.measurements)
        except Exception as e:
            self.view.open_error_message_popup_window(str(e))


