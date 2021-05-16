from src.view.application_gui import Application
from src.model.application_model import Model
from tkinter import Tk

root = Tk()
model = Model()
my_gui = Application(root,model)
root.mainloop()