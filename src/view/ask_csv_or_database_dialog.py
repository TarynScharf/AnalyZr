
from tkinter import *
from tkinter.ttk import *


class AskCsvOrDatabase():

    def __init__(self, view,all_folder_measurements):
        self.view = view
        self.ask_csv_or_db_window = Toplevel(self.view.master)
        self.ask_csv_or_db_window.title("Save Measurements")
        self.ask_csv_or_db_window.minsize(400, 100)
        self.ask_csv_or_db_window.lift()
        self.measurements = all_folder_measurements

        self.ask_csv_or_db_window_Label = Label(self.ask_csv_or_db_window, text="Would you like to save measurements to csv or database?")
        self.ask_csv_or_db_window_Label.grid(column=0, row=0,columnspan =5, sticky='w')
        self.csv_button = Button(self.ask_csv_or_db_window, text="csv", width=5, command= self.save_to_csv)
        self.csv_button.grid(column=0, row=1, padx=2, pady=5,sticky = 'w')
        self.db_button = Button(self.ask_csv_or_db_window, text="DB", width=5, command= self.save_to_db)
        self.db_button.grid(column=1, row=1, padx=2, pady=5,sticky = 'w')

    def save_to_csv(self):
        self.view.save_folder_measurements_to_csv(self.measurements)
        self.ask_csv_or_db_window.destroy()
    def save_to_db(self):
        self.view.save_folder_measurements_to_db(self.measurements)
        self.ask_csv_or_db_window.destroy()


