import tkinter as tk
from tksheet import Sheet
import pandas as pd
from tkinter import filedialog
import numpy as np
pixel_to_mm = 1.24e-3
XY_goal_gluing = [0., 0.]
XY_goal_alignment = [-300,-370]
def get_XY_camera_mean(file_path):
    data = np.loadtxt(file_path, delimiter=',')
    YX = np.array([np.mean(data[i::30, :2], axis=0) for i in range(30)])
    XY = YX[:, ::-1]
    return XY
def get_new_commend(XY, commend):
    mask = np.logical_not(np.any(XY==0, axis=1))
    dXY_commend_camera = -(XY_goal_alignment - XY)*pixel_to_mm
    new_commend = np.copy(commend.astype('float64') )
    new_commend[ mask] = new_commend[ mask] + dXY_commend_camera[mask]
    return new_commend


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("tksheet Example")
        self.geometry("1200x700")
        self.sheet_data = [[None for col in range(5)] for row in range(10)]
        self.frame = tk.Frame(self)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.sheet = Sheet(self.frame, data=self.sheet_data,expand_sheet_if_paste_too_big=True,
                           column_width=100,
                           height=200,
                           width=1000
                           )
        self.sheet.set_index_width(150)
        self.sheet.enable_bindings()
        self.sheet.set_index_data(['Type','X','Y','Z','Line Speed','Circle Angle','Condition Number',
                                   'Job before moving','Job while Moving','Job after Moving'])
        self.frame.grid(row=0, column=0,columnspan=5 ,sticky="nswe")
        self.sheet.grid(row=0, column=0, columnspan=5, sticky="nswe")
        self.sheet.bind("<<SheetModified>>", self.on_cell_change)
        self.selected_file_label = tk.Label(self, text="No file selected")
        self.selected_file_label.grid(row=2, column=0,columnspan=5)
        self.select_file_button = tk.Button(self, text="Camera Results file", command=self.select_file)
        self.select_file_button.grid(row=1, column=0,columnspan=5)
        self.selected_file_label = tk.Label(self, text="Select Modules")
        self.selected_file_label.grid(row=3, column=0, columnspan=5)
        k = 1
        self.module_buttons = []
        self.selected_modules = []
        for i in range(6):
            for j in range(5):
                button = tk.Button(self, text=str(k), command=lambda a=k: self.sel_module(a - 1), bg='red',
                                   height=1,
                                   width=2
                                   )
                button.grid(row=i+4, column=j, padx=5, pady=3)
                self.module_buttons.append(button)
                k += 1
        self.correct_button = tk.Button(self, text="Correct", command=self.correct_coordonate)
        self.correct_button.grid(row=11, column=0, columnspan=5)
        self.sheet_data_corrected = pd.DataFrame()
        self.sheet_corrected = Sheet(self, data=[], expand_sheet_if_paste_too_big=True,
                           column_width=100,
                           height=50,
                           width=1000
                           )
        self.sheet_corrected.set_index_width(150)
        self.sheet_corrected.enable_bindings()
        self.sheet_corrected.set_index_data(['Type', 'X', 'Y', 'Z', 'Line Speed', 'Circle Angle', 'Condition Number',
                                   'Job before moving', 'Job while Moving', 'Job after Moving'])
        self.sheet_corrected.grid(row=12, column=0, columnspan=5, sticky="nswe")

    def sel_module(self, mod):
        button = self.module_buttons[mod]
        if mod not in self.selected_modules:
            button.configure(bg='green')
            self.selected_modules.append(mod)
        else:
            self.selected_modules.remove(mod)
            button.configure(bg='red')
    # Configure grid expansion

    def on_cell_change(self, event):
        # Retrieve the edited cell's row, column, and new value
        self.sheet_data = pd.DataFrame( self.sheet[:].options(hdisp=False, header=True).data)

    def select_file(self):
        file_path = filedialog.askopenfilename(initialdir = r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\result\SD1_001")
        if file_path:
            self.selected_file_label.config(text=f"{file_path}")

    def correct_coordonate(self):
        XY = get_XY_camera_mean(self.selected_file_label['text'])
        commend = self.sheet_data.loc[[2,3]].T
        new_coor = get_new_commend(XY, commend)
        self.sheet_data_corrected = self.sheet_data.copy()
        self.sheet_data_corrected.loc[[2,3]] = new_coor.T
        print(self.sheet_data_corrected)
        self.sheet_corrected.set_sheet_data(list(self.sheet_data_corrected.to_numpy()[1:]))

if __name__ == "__main__":
    app = App()
    app.mainloop()
