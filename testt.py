import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime
import os
path = r'C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003'
dirs = os.listdir(path)
def get_date():
    date = cal.get_date()
    time = time_var.get().split(':')
    time = time[0]+time[1]+'00'
    files = [dir for dir in dirs if dir[:6]==date]
    if len(files) == 0 :
        print('no mesurement this day')
        return
    elif len(files) > 1:
        good_file = files[0]
        for  file in files:
            time_file = int(file[-6:])
            if time_file > int(good_file[-6:]) and time_file<int(time) :
                good_file = file
        files = [good_file]
    imgs_path = os.path.join(path,files[0],'CAM1')
    print(imgs_path)


root = tk.Tk()
root.title("Date and Time Picker")

# Date Picker
cal = Calendar(root, selectmode="day", date_pattern='yymmdd')
cal.grid(row=0, columnspan=2,padx=5, pady=5)
time_var = tk.StringVar()
time_combobox = ttk.Combobox(root, textvariable=time_var,values=["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"])
time_combobox.grid(row=1, column=0,pady=5,padx=5)
time_combobox.set("08:00")
time_var_end = tk.StringVar()
time_combobox_end = ttk.Combobox(root, textvariable=time_var,values=["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"])
time_combobox_end.grid(row=1, column=1,padx=5)
time_combobox_end.set("08:00")
date_button = ttk.Button(root, text="Get Date", command=get_date)
date_button.grid(row=6, columnspan=2, padx=5, pady=5)

root.mainloop()
