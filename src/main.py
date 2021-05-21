from src.view.application_view import View
from src.model.application_model import Model
from tkinter import Tk

root = Tk()
model = Model()
view = View(root, model)

#model.set_source_folder_paths('/home/matthew/Code/ZirconSeparation/test/files','/home/matthew/Code/ZirconSeparation/test/files')
model.set_source_folder_paths('C:/Users/20023951/PycharmProjects/ZirconSeparation/test/files','C:/Users/20023951/PycharmProjects/ZirconSeparation/test/files')
model.read_sampleID_and_spots_from_json()
view.update_data_capture_display()
root.mainloop()