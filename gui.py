# Let's add a tkinter interface that allows dynamic editing of lines:
import tkinter as tk
from tkinter import Tk, Label, Button, filedialog
from tkinter import *
from tkinter.ttk import *
import os
import json
import re
from PIL import ImageTk, Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime


class Application:

    def __init__(self, master, pairsList):
        self.master = master
        master.title("Zircon Shape Separation")
        master.geometry('1600x3000')

        self.myMenuFrame = tk.Frame(master, width=1600, height=50)
        self.myMenuFrame.pack(fill='both')
        self.myFrame = tk.Frame(master, width=1600, height=3000)
        self.myFrame.pack(expand=True, fill='both')
        self.myCanvas = Canvas(self.myFrame, bg="white")
        self.vScroll = Scrollbar(self.myFrame, orient='vertical', command=self.myCanvas.yview)
        self.hScroll = Scrollbar(self.myFrame, orient='horizontal', command=self.myCanvas.xview)
        self.vScroll.pack(side=RIGHT, fill=Y)
        self.hScroll.pack(side=BOTTOM, fill=X)
        self.myCanvas.configure(yscrollcommand=self.vScroll.set)
        self.myCanvas.configure(xscrollcommand=self.hScroll.set)
        self.myCanvas.bind("<Button-3>", self.DeleteObject)
        self.myCanvas.pack(side=LEFT, expand=True, fill=BOTH)

        # variables
        self.count = 0
        self.pairList = pairsList  # this should hold all the node pairs for the image
        self.lineStart_x = 0
        self.lineStart_y = 0
        self.updatedX = 0
        self.updatedY = 0

        # buttons
        self.breakLine = Button(self.myMenuFrame, text="Draw Break Line", command=self.DrawLine)
        self.breakLine.grid(column=0, row=0, padx=5, pady=10)
        self.saveChanges = Button(self.myMenuFrame, text="Save Changes", command=self.SaveChanges)
        self.saveChanges.grid(column=1, row=0, padx=5, pady=10)

        # Global bindings
        self.myCanvas.bind_all("<MouseWheel>", self.ScrollWithMouseWheel)
        self.myCanvas.bind("<Button-3>", self.DeleteObject)

        # autoload imageftre
        self.myCanvas.delete('all')
        img = Image.fromarray(threshold, 'L')
        img.save('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/threshold.png')
        self.img = ImageTk.PhotoImage(
            Image.open('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/threshold.png'))

        self.myCanvas.configure(scrollregion=[0, 0, self.img.width(), self.img.height()])
        self.myCanvas.create_image(0, 0, image=self.img, anchor=NW, tags="Image")

        for pair in self.pairList:
            x1 = pair[0][0]
            y1 = pair[0][1]
            x2 = pair[1][0]
            y2 = pair[1][1]
            ID = 'line_' + str(self.count)
            self.count += 1
            self.myCanvas.create_line(x1, y1, x2, y2, width=3, fill='red', activefill='yellow', tags=(ID))

    def SaveChanges(self):
        # print('saving changes')
        pairs = self.pairList
        # print(pairs)
        # print('--------------Pairs-----------')
        # for p in pairs:
        # print(p)
        # print('--------------pairList-----------')
        # for pl in self.pairList:
        # print(pl)
        dpi = 96
        height, width = threshold.shape
        fig = plt.figure(figsize=(float(width / dpi), float(height / dpi)))
        # ax =fig.add_axes([0, 0, 1, 1])
        # fig.add_subplot()
        plt.margins(0, 0)
        plt.axis('off')
        plt.imshow(threshold, cmap='Greys_r')
        # print('threshold shape: ',threshold.shape)

        for p in pairs:
            x1 = p[0][0]
            y1 = p[0][1]
            x2 = p[1][0]
            y2 = p[1][1]
            # pairsList.append([(x1,y1),(x2,y2)])
            plt.plot([x1, x2], [y1, y2], linestyle='solid', color='black', linewidth=3)

        # ax.set(xlim=[0,width], ylim=[0,height], aspect=1)
        # plt.savefig('C:/Users/20023951/Documents/PhD/Binarisation/_t.png', dpi=dpi)
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.savefig('C:/Users/20023951/Documents/PhD/GSWA/Geochem_Interrogate/Binarisation/_t.png', bbox_inches=None,
                    dpi=dpi, pad_inches=0)

    def ScrollWithMouseWheel(self, event):
        self.myCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def DrawLine(self):
        # print('DrawScale')
        self.myCanvas.unbind("<Button-1>")
        self.myCanvas.unbind("<ButtonPress-1>")
        self.myCanvas.unbind("<B1-Motion>")
        self.myCanvas.unbind("<ButtonRelease-1>")
        self.myCanvas.bind("<ButtonPress-1>", self.LineStart)
        self.myCanvas.bind("<B1-Motion>", self.LineUpdate)
        self.myCanvas.bind("<ButtonRelease-1>", lambda e: self.Save())

    def LineStart(self, event):
        # print('LineStart - line139')
        t_ID = 'line_' + str(datetime.datetime.now())
        ID = t_ID.replace(' ', '')
        # print('ID: ', ID)
        colour = 'red'
        self.lineStart_x = self.myCanvas.canvasx(event.x)
        self.lineStart_y = self.myCanvas.canvasy(event.y)
        # print('line 150 - self.lineStart_x: ', self.lineStart_x)
        # print('line 151 - self.lineStart_y: ', self.lineStart_y)
        self.Line = self.myCanvas.create_line(self.lineStart_x, self.lineStart_y, self.lineStart_x + 1,
                                              self.lineStart_y + 1, width=3, fill=colour, activefill='yellow',
                                              tags=(ID))

    def LineUpdate(self, moveEvent):
        self.myCanvas.unbind("<ButtonPress-1>")
        self.updatedX = self.myCanvas.canvasx(moveEvent.x)
        self.updatedY = self.myCanvas.canvasy(moveEvent.y)
        # print('line 160 - self.updatedX: ', self.updatedX)
        # print('line 161 - self.updatedY: ', self.updatedY)
        self.myCanvas.coords(self.Line, self.lineStart_x, self.lineStart_y, self.updatedX, self.updatedY)

    def Save(self):
        self.pairList.append([(self.lineStart_x, self.lineStart_y), (self.updatedX, self.updatedY)])

    # print('----------------coords to add to pairList---------------')
    # print(self.lineStart_x,self.lineStart_y, self.updatedX,self.updatedY)
    # print('---------------added to  pairlist-------------------------')
    # for pair in self.pairList:
    # print(pair)

    def DeleteObject(self, event):
        thisObj = event.widget.find_withtag('current')[0]  # get the object clicked on
        # print('thisObj: ', thisObj)
        thisObjID = self.myCanvas.gettags(thisObj)[0]  # find the group tag for the object clicked on
        # print('thisObjID: ', thisObjID)
        if thisObjID != "Image":  # make sure you haven't selected the image
            self.myCanvas.coords(thisObjID)
            # print(self.myCanvas.coords(thisObjID))
            coords = self.myCanvas.coords(thisObjID)
            x1 = coords[0]
            y1 = coords[1]
            x2 = coords[2]
            y2 = coords[3]
            #  print('----------------Coords to remove--------------')
            # print(coords)
            # print('---------------pairlist----------------------- ')
            #  for pair in self.pairList:
            #    print(pair)

            self.myCanvas.delete(thisObjID)  # delete everything with the same groupID
            self.pairList.remove([(x1, y1), (x2, y2)])
        # print('-------------------pairlist after removal----------------------')
        # for pair in self.pairList:
        #    print(pair)



