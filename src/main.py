from src.view.application_view import View
from src.model.application_model import Model
from tkinter import Tk

root = Tk()
model = Model()
view = View(root, model)

root.mainloop()