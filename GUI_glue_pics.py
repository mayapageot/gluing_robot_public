import os
import tkinter as tk
from tkinter import ttk

import cv2
from tkcalendar import Calendar
from datetime import datetime
import matplotlib.pyplot as plt
import locale
import numpy as np
import pandas as pd
# Set the locale to French
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
path_img = r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240506_131040\CAM1"
from PIL import Image, ImageTk
import tksheet
#df = pd.read_csv("/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T215728Z-001/analysis_2.csv")
df = pd.read_csv(r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240506_131040\CAM1\analysis_2.csv")

sorting_order = { 'br': 0, 'bl': 1,'m': 2, 'tr': 3, 'tl': 4}
sorting_key = lambda x: sorting_order.get(x, float('inf'))
def convert_time(hours, minutes="00"):
    return int('{:02d}{:02d}00'.format(int(hours), int(minutes)))

def plot_img(image_with_keypoints,center_list,diameter_list):
    fig,ax =  plt.subplots(figsize=(10,7))
    for center, dimeter in zip(center_list, diameter_list):
        Drawing_colored_circle = plt.Circle(center, int(dimeter), fill=None, color='g', lw=2)
        ax.add_artist(Drawing_colored_circle)
        text = f'R = {int(dimeter)}'
        ax.text(center[0]-dimeter,center[1]-dimeter*1.1,text,c='g')
    ax.imshow(image_with_keypoints)
    ax.set_aspect(1)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.show()

def get_image(*args):
    start_date = start_cal.get_date()
    start_time = convert_time(start_time_hour_combobox.get(), start_time_min_combobox.get())
    end_time = convert_time(end_time_hour_combobox.get(), end_time_min_combobox.get())
    module = module_combobox.get()
    file_sel = []
    for file in os.listdir(path_img):
        if file[-4:] == ".bmp":
            time = int(file[7:13])
            if time < end_time and time > start_time:
                file_sel.append(file)
    if len(file_sel) > 0:
        modules = list(df.loc[df["filename"].isin(file_sel),"module"].unique())
        modules.append("all")
        module_combobox.configure(values = modules)
    if module != "all":
        df_bis = df.loc[df["module"] == int(module), 'filename']
        file_sel = df_bis[df_bis.isin(file_sel)].unique()

    if len(file_sel) > 0:
        file_sel = list(np.sort(file_sel))
        image_combobox.configure(values = file_sel)
        image_combobox.set(file_sel[0])
        update_val()
    else:
        image_combobox.configure(values = [])
        image_combobox.set([])


def update_val(*arg):
    file = image_combobox.get()
    df_file = df.loc[df['filename'] == file]
    data = df_file.sort_values(by='position', key=lambda x: x.map(sorting_key)).loc[:,('center_x','center_y','diameter','module')].to_numpy().T
    sheet.set_sheet_data([[f"{val:.0f}" for val in arr] for arr in data])
def plot_images():
    file = image_combobox.get()
    image = cv2.imread(os.path.join(path_img, file))
    df_filename = df.loc[df['filename'] == file]
    center_list = df_filename.loc[:,('center_x','center_y')].to_numpy()
    print(center_list)
    diameter_list = df_filename.loc[:,'diameter'].to_numpy()
    print(diameter_list)
    plot_img(image, center_list, diameter_list)
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

module_var = tk.StringVar()
module_combobox = ttk.Combobox(root, textvariable=module_var,
                                 values=["all"],width=10)
module_combobox.bind("<<ComboboxSelected>>",func = get_image)
module_combobox.grid(row=6,column=0 ,columnspan=1, padx=10, pady=5)
module_combobox.set("all")

image_var = tk.StringVar()
image_combobox = ttk.Combobox(root, textvariable=image_var,
                                 values=[],width=40)
image_combobox.bind("<<ComboboxSelected>>",func = update_val)
image_combobox.grid(row=6 ,column=1, columnspan=3, padx=10, pady=5)

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
