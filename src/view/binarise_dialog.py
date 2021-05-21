import tkinter as tk
from tkinter import *
from tkinter.ttk import *

from src.view.segmentation_dialog import SegmentationDialog


class BinariseDialog():
    def __init__(self,view):
        self.view = view
        self.browseImagesWindow = Toplevel(self.view.master)
        self.browseImagesWindow.title("Select Images to Binarise")
        self.browseImagesWindow.minsize(400, 100)
        self.browseImagesWindow.attributes('-topmost', True)

        #VARIABLES
        self.RLPath = tk.StringVar()
        self.RLPath.set('')
        self.rlVar = IntVar()
        self.RLPath.set('C:/Users/20023951/PycharmProjects/ZirconSeparation/test/images/88411_spots_p1_RL__WqO4ozqE.png')

        self.TLPath = tk.StringVar()
        self.TLPath.set('')
        self.TLPath.set('C:/Users/20023951/PycharmProjects/ZirconSeparation/test/images/88411_spots_p1_TL_PnCztOBkT.png')
        self.tlVar = IntVar()

        #WIDGETS
        self.RL_Label = Label(self.browseImagesWindow, text="RL Image")
        self.RL_Label.grid(column=0, row=0)
        # self.RLPath.set('/home/matthew/Code/ZirconSeparation/test/images/88411_spots_p1_RL__WqO4ozqE.png')

        self.RLTextBox = Entry(self.browseImagesWindow, width=150, textvariable=self.RLPath)
        self.RLTextBox.grid(column=1, row=0)
        self.browseRL = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('RL'))
        self.browseRL.grid(column=3, row=0, padx=2, pady=5)

        self.rlCheckButton = Checkbutton(self.browseImagesWindow, text='Binarise  RL', variable=self.rlVar)
        self.rlCheckButton.grid(column=4, row=0, padx=2, pady=5)
        self.Display_RL_Image_Button = Button(self.browseImagesWindow, text="Display", width=8, command=lambda: self.view.display_parent_image(0,self.RLPath.get(), self.TLPath.get()))
        self.Display_RL_Image_Button.grid(column=5, row=0, padx=2, pady=5)

        self.TL_Label = Label(self.browseImagesWindow, text="TL Image")
        self.TL_Label.grid(column=0, row=1)

        self.TLTextBox = Entry(self.browseImagesWindow, width=150, textvariable=self.TLPath)
        self.TLTextBox.grid(column=1, row=1)
        self.browseTL = Button(self.browseImagesWindow, text="...", width=5, command=lambda: self.Browse('TL'))
        self.browseTL.grid(column=3, row=1, padx=2, pady=5)

        self.tlCheckButton = Checkbutton(self.browseImagesWindow, text='Binarise TL', variable=self.tlVar)
        self.tlCheckButton.grid(column=4, row=1, padx=2, pady=5)
        self.Display_TL_Image_Button = Button(self.browseImagesWindow, text="Display", width=8,
                                              command=lambda: self.view.display_parent_image(1,self.RLPath.get(), self.TLPath.get()))
        self.Display_TL_Image_Button.grid(column=5, row=1, padx=2, pady=5)

        self.BinariseButton = Button(self.browseImagesWindow, text="Binarise", command=self.binarise_images)
        self.BinariseButton.grid(column=0, row=2, padx=2, pady=5)

    def binarise_images(self):
        RLPath = self.RLPath.get()
        TLPath = self.TLPath.get()
        rlVar = self.rlVar.get()
        tlVar = self.tlVar.get()
        self.view.binariseImages(RLPath, TLPath, rlVar, tlVar)
        self.browseImagesWindow.destroy()
        SegmentationDialog(self.view, RLPath, TLPath, rlVar, tlVar)

    def Browse(self,image_type):
        filename = self.view.Browse(image_type, self.browseImagesWindow)

        if image_type == 'RL':
            self.RLPath.set(filename)
            self.RLTextBox.delete(0, END)
            self.RLTextBox.insert(0, filename)
        if image_type == 'TL':
            self.TLPath.set(filename)
            self.TLTextBox.delete(0, END)
            self.TLTextBox.insert(0, filename)





