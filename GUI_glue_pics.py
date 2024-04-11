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


def convert_time(hours, minutes="00"):
    return int('{:02d}{:02d}00'.format(int(hours), int(minutes)))
def get_dates():
    start_date = start_cal.get_date()
    start_time = convert_time(start_time_hour_combobox.get(),start_time_min_combobox.get())
    end_time = convert_time(end_time_hour_combobox.get(),end_time_min_combobox.get())

    file_sel = []
    for file in os.listdir(path_img):
        time = int(file[7:13])
        if time < end_time and time >start_time :
            file_sel.append(file)
    """image_prev = tk.Toplevel(root)
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
        buttons.append(button)"""
def get_image(*args):
    start_date = start_cal.get_date()
    start_time = convert_time(start_time_hour_combobox.get(), start_time_min_combobox.get())
    end_time = convert_time(end_time_hour_combobox.get(), end_time_min_combobox.get())
    file_sel = []
    for file in os.listdir(path_img):
        if file[-4:] == ".bmp":
            time = int(file[7:13])
            if time < end_time and time > start_time:
                file_sel.append(file)
    if len(file_sel) > 0:
        file_sel = list(np.sort(file_sel))
        image_combobox.configure(values = file_sel)
        image_combobox.set(file_sel[0])
    else:
        image_combobox.configure(values = [])
        image_combobox.set([])

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
start_cal.grid(row=1, columnspan=4, padx=5, pady=5)


# Combobox for Start Time
start_time_label = ttk.Label(root, text="Select Start Time:")
start_time_label.grid(row=4, column=0,columnspan=2, padx=5, pady=5)

start_time_hour_var = tk.StringVar()
start_time_hour_combobox = ttk.Combobox(root, textvariable=start_time_hour_var, width=5,
                                        values=[f"{i:02d}" for i in range(24)])
start_time_hour_combobox.bind("<<ComboboxSelected>>", func = get_image)
start_time_hour_combobox.grid(row=5, column=0, padx=5, pady=5)
start_time_hour_combobox.set("09")

start_time_min_var = tk.StringVar()
start_time_min_combobox = ttk.Combobox(root, textvariable=start_time_min_var,width=5,
                                 values=[f"{i*5:02d}" for i in range(12)])
start_time_min_combobox.bind("<<ComboboxSelected>>",func = get_image)
start_time_min_combobox.grid(row=5, column=1, padx=5, pady=5)
start_time_min_combobox.set("00")

# Combobox for End Time
end_time_label = ttk.Label(root, text="Select End Time:")
end_time_label.grid(row=4, column=2,columnspan=2, padx=5, pady=5)

end_time_hour_var = tk.StringVar()
end_time_hour_combobox = ttk.Combobox(root, textvariable=end_time_hour_var,width=5,
                                 values=[f"{i:02d}" for i in range(24)])
end_time_hour_combobox.bind("<<ComboboxSelected>>",func = get_image)
end_time_hour_combobox.grid(row=5, column=2, padx=5, pady=5)
end_time_hour_combobox.set("17")

end_time_min_var = tk.StringVar()
end_time_min_combobox = ttk.Combobox(root, textvariable=end_time_min_var,width=5,
                                 values=[f"{i*5:02d}" for i in range(12)])
end_time_min_combobox.bind("<<ComboboxSelected>>",func = get_image)
end_time_min_combobox.grid(row=5, column=3, padx=5, pady=5)
end_time_min_combobox.set("00")


image_var = tk.StringVar()
image_combobox = ttk.Combobox(root, textvariable=image_var,
                                 values=[],width=40)
image_combobox.bind("<<ComboboxSelected>>",func = update_val)
image_combobox.grid(row=6, columnspan=4, padx=10, pady=5)

plot_img_button = ttk.Button(root, text="Plot image", command=plot_images)
plot_img_button.grid(row=7, columnspan=4, padx=5, pady=5)

sheet = tksheet.Sheet(root,column_width = 75,
                        height=100,
                        width=6*75+5,
                        show_x_scrollbar=False,
                        show_y_scrollbar=False,
                        row_index_width=80,
                        header_font=("Calibri",8,"normal"),
                        index_font=("Calibri",9,"normal")
                      )

sheet.grid(row=11, columnspan=4, padx=5, pady=5)
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
