import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *


class SaveSpotDialog():
    def __init__(self, view,drawing,spot, is_new_spot):
        self.view = view
        self.drawing=drawing
        self.spotCaptureWindow = Toplevel(self.view.master)
        self.spotCaptureWindow.title("Capture Spot Number")
        self.spotCaptureWindow.minsize(300, 100)
        self.spotCaptureWindow.lift()
        self.spotCaptureWindow.grab_set()
        self.spotCaptureWindow.focus_set()


        self.is_new_spot = is_new_spot
        self.spot = spot

        self.currentSpotNumber = tk.StringVar()
        self.note_text = tk.StringVar()
        self.cl_texture_text = tk.StringVar()

        if self.is_new_spot:
            self.currentSpotNumber.set('')
            self.note_text.set('')
            self.cl_texture_text.set('')

        else:
            self.currentSpotNumber.set(spot.group_tag.replace('spot_',''))
            self.note_text.set(spot.notes)
            self.cl_texture_text.set(spot.cl_texture)

        self.spotCaptureLabel = Label(self.spotCaptureWindow, text='Spot ID')
        self.spotCaptureLabel.grid(column=0, row=0, padx=2, pady=2, sticky='EW')

        self.currentSpotTextBox = Entry(self.spotCaptureWindow, width=20, textvariable=self.currentSpotNumber)
        self.currentSpotTextBox.grid(column=1, row=0, padx=2, pady=2, sticky='W')
        self.currentSpotTextBox.focus()

        self.CL_texture_label = Label(self.spotCaptureWindow, text='CL texture')
        self.CL_texture_label.grid(column=0, row=1, padx=2, pady=2, sticky='W')
        self.CL_texture_combobox = Combobox (self.spotCaptureWindow, width=20, textvariable=self.cl_texture_text, values=['homogenous',
                                                                                                                            'oscillitory',
                                                                                                                            'patchy',
                                                                                                                            'sector',
                                                                                                                            'other'])

        self.CL_texture_combobox.grid(column=1, row=1, padx=2, pady=2, sticky='W')

        # Added to address reviewer comments: Freeform notes:
        self.notes_label = Label(self.spotCaptureWindow, text='Comments:', width=50)
        self.notes_label.grid(column=0, row=2, padx=2, pady=2, sticky='W')

        self.notes_textbox = Entry(self.spotCaptureWindow, textvariable=self.note_text)
        self.notes_textbox.grid(column=1, row=2, padx=2, pady=2, sticky='W')

        self.saveSpotNo = Button(self.spotCaptureWindow, text='Save', command=self.save_spot, width=10)
        self.spotCaptureWindow.bind('<Return>', lambda e: self.save_spot())
        self.saveSpotNo.grid(column=1, row=3, padx=2, pady=2, sticky='W')

        self.spotCaptureWindow.protocol("WM_DELETE_WINDOW", self.on_closing)

    def save_spot(self):
        self.spot.cl_texture = self.CL_texture_combobox.get()
        self.spot.notes = self.notes_textbox.get().strip()
        if self.currentSpotNumber.get().strip() == '':
            messagebox.showinfo("Error", "No spot ID provided.")
            self.spotCaptureWindow.lift()
            return

        try:
            if self.is_new_spot:
                self.spot.group_tag = self.currentSpotNumber.get().strip()
                self.view.model.add_new_spot(self.spot)
                self.is_new_spot = False
                self.spotCaptureWindow.destroy()
            else:
                userText = self.currentSpotNumber.get()
                self.view.model.update_spot_id(self.spot, userText)
                self.spotCaptureWindow.destroy()
        except Exception as e:
            messagebox.showinfo("Error", str(e))
            return None

    def on_closing(self):
        self.spotCaptureWindow.destroy()
        self.view.model.DeleteObject(self.spot.group_tag)
        self.view.drawing.myCanvas.delete(self.spot.group_tag)


