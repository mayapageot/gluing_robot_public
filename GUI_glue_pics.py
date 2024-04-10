import os
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime
import locale
import numpy as np
import pandas as pd
# Set the locale to French
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
path_img = "/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T215728Z-001"
from PIL import Image, ImageTk
import tksheet
df = pd.read_csv("/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T215728Z-001/analysis.csv")


def convert_time(time_str):
    # Split the time string into hours and minutes
    hours, minutes = map(int, time_str.split(':'))

    # Return the time in "hhmmss" format
    return int('{:02d}{:02d}00'.format(hours, minutes))
def get_dates():
    start_date = start_cal.get_date()
    start_time = convert_time(start_time_combobox.get())
    end_time = convert_time(end_time_combobox.get())
    print(start_time,end_time)
    file_sel = []
    for file in os.listdir(path_img):
        time = int(file[7:13])
        if time < end_time and time >start_time :
            file_sel.append(file)
    print(file_sel)
    image_prev = tk.Toplevel(root)
    image_prev.title("New Window")
    image_prev.geometry("200x200")
    p = int(np.sqrt(len(file_sel)))
    buttons = []
    for i,file in enumerate(file_sel):
        image = Image.open(os.path.join(path_img,file))
        image = image.crop((100, 100, 120, 120))
        photo = ImageTk.PhotoImage(image)
        button = tk.Button(image_prev, text = 'Click Me !', command=lambda f=file:print(f))
        button.grid(row=i%p, column=i//p, padx=5, pady=5)
        buttons.append(button)
def get_image(*args):
    start_date = start_cal.get_date()
    start_time = convert_time(start_time_combobox.get())
    end_time = convert_time(end_time_combobox.get())
    print(start_time, end_time)
    file_sel = []
    for file in os.listdir(path_img):
        if file[-4:]==".bmp":
            time = int(file[7:13])
            if time < end_time and time > start_time:
                file_sel.append(file)
    file_sel = list(np.sort(file_sel))
    image_combobox.configure(values=file_sel)
    image_combobox.set(file_sel[0])

def update_val(*arg):
    file = image_combobox.get()
    df_file = df.loc[df['filename'] == file]
    """radius_arr_label.configure(text = '\t'.join([f'{item:4.0f}' for item in df_file['diameter'].array]))
    xposes_arr_label.configure(text = '\t'.join([f'{item:4.0f}' for item in df_file['center_x'].array]))
    yposes_arr_label.configure(text = '\t'.join([f'{item:4.0f}' for item in df_file['center_y'].array]))
    module_arr_label.configure(text = str(df_file['module'].array[0]))"""
    data = df_file.loc[:,('center_x','center_y','diameter','module')].to_numpy().T
    sheet.set_sheet_data([[f"{val:.0f}" for val in arr] for arr in data])
def plot_images():
    file = image_combobox.get()
    image = Image.open(os.path.join(path_img, file))
    image.show()
root = tk.Tk()
root.title("Date Range Picker")

start_cal = Calendar(root, selectmode="day", date_pattern='yyyy-mm-dd')
start_cal.grid(row=1, columnspan=2, padx=5, pady=5)


# Combobox for Start Time
start_time_label = ttk.Label(root, text="Select Start Time:")
start_time_label.grid(row=4, column=0, padx=5, pady=5)

start_time_var = tk.StringVar()
start_time_combobox = ttk.Combobox(root, textvariable=start_time_var,
                                   values=["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"])
start_time_combobox.bind( "<<ComboboxSelected>>",func = get_image)
start_time_combobox.grid(row=5, column=0, padx=5, pady=5)
start_time_combobox.set("10:00")

# Combobox for End Time
end_time_label = ttk.Label(root, text="Select End Time:")
end_time_label.grid(row=4, column=1, padx=5, pady=5)

end_time_var = tk.StringVar()
end_time_combobox = ttk.Combobox(root, textvariable=end_time_var,
                                 values=["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"])
end_time_combobox.bind("<<ComboboxSelected>>",func = get_image)
end_time_combobox.grid(row=5, column=1, padx=5, pady=5)
end_time_combobox.set("14:00")

"""# Get Dates Button
date_button = ttk.Button(root, text="Get Dates", command=get_dates)
date_button.grid(row=6, columnspan=2, padx=5, pady=5)"""
image_var = tk.StringVar()
image_combobox = ttk.Combobox(root, textvariable=image_var,
                                 values=[],width=40)
image_combobox.bind("<<ComboboxSelected>>",func = update_val)
image_combobox.grid(row=6, columnspan=2, padx=10, pady=5)

plot_img_button = ttk.Button(root, text="Plot image", command=plot_images)
plot_img_button.grid(row=7, columnspan=2, padx=5, pady=5)

sheet = tksheet.Sheet(root,column_width = 75,
                        height=100,
                        width=6*75+5,
                        show_x_scrollbar=False,
                        show_y_scrollbar=False,
                        row_index_width=80,
                        header_font=("Calibri",8,"normal"),
                        index_font=("Calibri",9,"normal")
                      )

sheet.grid(row=11, columnspan=2, padx=5, pady=5)
# table enable choices listed below:
sheet.enable_bindings(("single_select",
                       "row_select",
                       "column_width_resize",
                       "arrowkeys",
                       "right_click_popup_menu",
                       "rc_select",
                       "rc_insert_row",
                       "rc_delete_row",
                       "copy",
                       "cut",
                       "paste",
                       "delete",
                       "undo",
                       "edit_cell"))
sheet.headers(["bottom right","bottom left","center","top right","top left"],)
sheet.row_index(['center_x','center_y','diameter','module'])

get_image()
update_val()
root.mainloop()
