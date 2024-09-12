from tksheet import Sheet
import tkinter as tk
import numpy as np
def test(module,arr):
    arr
class demo(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.frame = tk.Frame(self)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.sheet = Sheet(self.frame, data=[], expand_sheet_if_paste_too_big=True,
                           column_width=100,
                           height=200,
                           width=1000
                           )
        self.sheet.set_index_width(150)
        self.sheet.enable_bindings()
        self.sheet.set_index_data(['Type', 'X', 'Y', 'Z', 'Line Speed', 'Circle Angle', 'Condition Number',
                                   'Job before moving', 'Job while Moving', 'Job after Moving'])
        self.frame.grid(row=0, column=0, columnspan=5, sticky="nswe")
        self.sheet.grid(row=0, column=0, columnspan=5, sticky="nswe")

        self.sheet.set_sheet_data(list(np.random.random((10,10))))



app = demo()
app.mainloop()
