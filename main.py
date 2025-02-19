import tkinter as tk

import matplotlib.pyplot as plt
from customtkinter import filedialog
from PIL import Image, ImageTk
import tksheet
import cv2
import os
import pandas as pd
import numpy as np
import scipy
from skimage.transform import hough_circle, hough_circle_peaks
from skimage.morphology import dilation, disk
from skimage.measure import find_contours
from skimage.feature import canny
import customtkinter as Ctk
def convert_arr_2_img(arr):
    image_array_normalized = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX)
    image_array_normalized = image_array_normalized.astype(np.uint8)
    if len(image_array_normalized.shape)==2:
        return cv2.cvtColor(image_array_normalized,cv2.COLOR_GRAY2RGB)
    else :
        return image_array_normalized
def resize_image(img, new_width, new_height):
    h, w = img.shape[:2]

    # Calculate aspect ratios
    img_ratio = w / h
    target_ratio = new_width / new_height

    if target_ratio > img_ratio:
        # If target aspect ratio is wider, resize based on width
        new_w = new_width
        new_h = int(new_width / img_ratio)
    else:
        # If target aspect ratio is taller, resize based on height
        new_h = new_height
        new_w = int(new_height * img_ratio)

    # Resize the image
    resized_img = cv2.resize(img, (new_w, new_h), interpolation = cv2.INTER_AREA)

    # Calculate coordinates to crop the center
    x_start = (new_w - new_width) // 2
    y_start = (new_h - new_height) // 2

    # Crop the center of the image
    cropped_img = resized_img[y_start:y_start + new_height, x_start:x_start + new_width]

    return cropped_img


def get_chip(path_ref,crop):
    im = cv2.imread(path_ref)
    im_slice = im[crop[0]: crop[1], crop[2]: crop[3],1]
    tot = im_slice.size
    cum_hist = np.cumsum(np.bincount(im_slice.ravel(), minlength = 256))
    j = int(np.searchsorted(cum_hist, tot * 0.9)) + 1
    im_g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im_thr = cv2.inRange(im_g, 0, j + 1)
    contours, hierarchy = cv2.findContours(im_thr, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key = len)
    rect = cv2.minAreaRect(largest_contour)
    box = cv2.boxPoints(rect)
    box = np.intp(box)
    crop = [np.min(box[:,1]),np.max(box[:,1]),np.min(box[:,0]),np.max(box[:,0])]
    center_chip = rect[0][0]-np.min(box[:,0]),rect[0][1]-np.min(box[:,1])
    return crop,center_chip


def get_dots(path, path_ref, crop=None, r_guess=400, n_dots=1, pxl_accuracy=5):
    imag = cv2.imread(path)
    if crop is None:
        crop = [0,imag.shape[0],0,imag.shape[1]]
    #crop, center_chip = get_chip(path_ref,crop)
    imag=imag[crop[0]: crop[1], crop[2]: crop[3]]
    im = np.array(cv2.cvtColor(imag, cv2.COLOR_BGR2GRAY), dtype = np.int32)
    im_ref = np.array(cv2.cvtColor(cv2.imread(path_ref), cv2.COLOR_BGR2GRAY), dtype = np.int32)
    im_ref = im_ref[crop[0]: crop[1], crop[2]: crop[3]]
    im_diff = np.abs(im_ref - im)
    image = cv2.normalize(im_diff, None, 0, 255, cv2.NORM_MINMAX)
    # dvlp : make the high_threshold a selectable param + split the edges from the dot reco
    edges = canny(image, sigma = 5, low_threshold = 5, high_threshold = 30)
    edges_thick = dilation(edges, disk(10))
    contour = find_contours(edges_thick)
    contour = max(contour, key = lambda c: len(c)).astype(int)
    area = [cv2.contourArea(contour)]
    hough_radii = np.arange(r_guess-30, r_guess+30, pxl_accuracy)
    # min_x ,max_x, min_y,max_y = np.min(contour[:,0]),np.max(contour[:,0]),np.min(contour[:,1]),np.max(contour[:,1])
    # contour_img = np.zeros((max_y-min_y+1,max_x-min_x+1))
    # contour_img[contour[:,1]-min_y,contour[:,0]-min_x] = 255
    hough_res = hough_circle(edges_thick, hough_radii)
    min_dist = r_guess
    accums, cx, cy, radii = hough_circle_peaks(hough_res, hough_radii, total_num_peaks = n_dots, min_xdistance=min_dist,min_ydistance=min_dist)
    # cx ,cy = cy+min_y,cx+min_x
    # print(cx, cy, radii)
    for center_y, center_x, radius in zip(cy, cx, radii):
        cv2.circle(imag, (center_x, center_y), int(radius), (255, 0, 0), 10)
    return (radii,cx,cy,accums,area,crop,
            [convert_arr_2_img(im_diff),convert_arr_2_img(edges_thick*255),convert_arr_2_img(imag)])

def plot_dots(path, path_ref, crop, cy, cx, radii):
    imag = cv2.imread(path)
    imag = imag[crop[0]: crop[1], crop[2]: crop[3]]
    im = np.array(cv2.cvtColor(imag, cv2.COLOR_BGR2GRAY), dtype = np.int32)
    im_ref = np.array(cv2.cvtColor(cv2.imread(path_ref), cv2.COLOR_BGR2GRAY), dtype = np.int32)
    im_ref = im_ref[crop[0]: crop[1], crop[2]: crop[3]]
    im_diff = np.abs(im_ref - im)
    image = cv2.normalize(im_diff, None, 0, 255, cv2.NORM_MINMAX)
    edges = canny(image, sigma = 5, low_threshold = 10, high_threshold = 50)
    edges_thick = dilation(edges, disk(10))
    for center_y, center_x, radius in zip(cy, cx, radii):
        cv2.circle(imag, (int(center_x), int(center_y)), int(radius), (255, 0, 0), 10)
    return [convert_arr_2_img(im_diff),convert_arr_2_img(edges_thick*255),convert_arr_2_img(imag)]


class MyScrollableCheckboxFrame(Ctk.CTkScrollableFrame):
    def __init__(self, master, title, values, function):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.checkboxes = []
        self.create_labels(self.values)
        self.function = function
    def create_labels(self,values):
        self.values = values
        for widget in self.winfo_children():
            widget.destroy()
        for label in values:
            text_label = Ctk.CTkLabel(self, text=label, text_color="light sky blue", cursor="hand2")
            text_label.pack(pady=1)
            text_label.bind("<Button-1>", lambda e, text=label: self.on_click(text))
    def add_label(self,label):
        text_label = Ctk.CTkLabel(self, text = label, text_color = "light sky blue", cursor = "hand2")
        text_label.pack(pady = 1)
        text_label.bind("<Button-1>", lambda e, text = label: self.on_click(text))
    def on_click(self, text):
        self.function(text)


class ImageSelector:
    def __init__(self, root):

        self.root = root
        self.root.title("Image Selector")
        self.dir = "/media/mp274748/Transcend/data/Glue_Files/250206_110255/CAM1"#"/media/mp274748/Transcend/data/Glue_Files/241015_145732/CAM1"
        #self.root.geometry("320x220")
        row = 0

        self.dir_label = Ctk.CTkLabel(self.root, text = self.dir , text_color = "light sky blue")
        self.dir_label.grid(row=row, column=0,columnspan = 4)
        self.dir_label.bind("<Button-1>", lambda x:self.select_directory())

        row+=1

        self.Chip_label = Ctk.CTkLabel(self.root, text = "Name of the Chip :", font = ("TkDefaultFont", 20, "bold"))
        self.Chip_label.grid(row = row, column = 0)

        self.Chip_textbox = Ctk.CTkTextbox(master = self.root, width = 100, height = 30, corner_radius = 0,
                                                font = ("TkDefaultFont", 20, "bold"))
        self.Chip_textbox.grid(row = row, column = 1, columnspan = 1, padx=10, pady=10)

        self.support_label = Ctk.CTkLabel(self.root, text = "Name of the Support :", font = ("TkDefaultFont", 20, "bold"))
        self.support_label.grid(row = row, column = 2)

        self.support_textbox = Ctk.CTkTextbox(master = self.root, width = 100, height = 30, corner_radius = 0,
                                      font = ("TkDefaultFont", 20, "bold"))
        self.support_textbox.grid(row = row, column = 3, columnspan = 1, padx = 10, pady = 10)

        row+=1

        self.canvas1 = Ctk.CTkCanvas(self.root,width = 250, height = 200, background = root["bg"])
        self.canvas1.grid(row=row, column=0, columnspan = 2, padx=0, pady=0)

        self.canvas2 = Ctk.CTkCanvas(self.root,width = 250, height = 200, background = root["bg"])
        self.canvas2.grid(row=row, column = 2,columnspan=3, padx=0, pady=0)
        row+=1
        self.filename1 = Ctk.CTkLabel(self.root , text = "")
        self.filename1.grid(row=row, column = 0, columnspan = 2,padx=0, pady=0)

        self.filename2 = Ctk.CTkLabel(self.root, text = "")
        self.filename2.grid(row = row, column = 2, columnspan = 3, padx = 0, pady = 0)
        row+=1
        select_btn1 = Ctk.CTkButton(self.root, text="Glue Dot", command=self.select_image1)
        select_btn1.grid(row=row, column=0, columnspan = 2, padx=10, pady=10)

        select_btn2 = Ctk.CTkButton(self.root, text="Reference", command=self.select_image2)
        select_btn2.grid(row=row, column = 2,columnspan=3, padx=10, pady=10)
        row+=1

        self.chipLabel = Ctk.CTkLabel(self.root, text = "Chip")
        self.chipLabel.grid(row = row, column = 2, padx = 0, pady = 0)

        self.radiusLabel = Ctk.CTkLabel(self.root, text = "Radius guess")
        self.radiusLabel.grid(row = row, column = 3, padx = 0, pady = 0)

        self.numberdotsLabel = Ctk.CTkLabel(self.root, text = "# dots")
        self.numberdotsLabel.grid(row = row, column = 4, padx = 0, pady = 0)

        self.pxlaccuLabel = Ctk.CTkLabel(self.root, text = "pxl\naccuracy")
        self.pxlaccuLabel.grid(row = row, column = 5, padx = 0, pady = 0)

        self.canvas_axes = Ctk.CTkCanvas(self.root, width = 70, height = 70, background = root["bg"],
                                         highlightthickness = 0)
        self.canvas_axes.grid(row = row, column = 0,rowspan=2, padx = 0, pady = 0)
        self.__init_ax__(70)

        analyse_btn = Ctk.CTkButton(self.root, text = "Analyse", command = self.analyse)
        analyse_btn.grid(row = row, column = 1,rowspan=2, padx = 0, pady = 0)

        row+=1

        self.chip_combobox = Ctk.CTkComboBox(root, width = 80,
                                          values = ["NTD", "LUMI NTD","heater"])
        self.chip_combobox.grid(row = row, column = 2, padx = 0, pady = 0)
        self.chip_combobox.set("NTD")

        self.radius_combobox = Ctk.CTkComboBox(root, width = 80,
                                               values = ["{:.0f}".format(i*10) for i in range(45,71)])
        self.radius_combobox.grid(row = row, column = 3, padx = 0, pady = 0)
        self.radius_combobox.set("400")
        
        self.numberdots_combobox = Ctk.CTkComboBox(root, width = 40,
                                                   values = ["{:.0f}".format(i) for i in range(1,10)])
        self.numberdots_combobox.grid(row = row, column = 4, padx = 10, pady = 0)
        self.numberdots_combobox.set("1")

        self.pxlaccu_combobox = Ctk.CTkComboBox(root, width = 40,
                                                   values = ["{:.0f}".format(i) for i in range(1, 10)])
        #                                           command = lambda x: self.analyse())
        self.pxlaccu_combobox.grid(row = row, column = 5, padx = 10, pady = 0)
        self.pxlaccu_combobox.set("5")

        row +=1
        self.canvas_diff = Ctk.CTkCanvas(self.root,width = 230, height = 230, background = root["bg"])
        self.canvas_diff.grid(row = row, column = 0,columnspan=2, padx = 10, pady = 10)
        self.canvas_edge = Ctk.CTkCanvas(self.root, width = 230, height = 230, background = root["bg"])
        self.canvas_edge.grid(row = row, column = 2, columnspan=3, padx = 10, pady = 10)
        row+=1
        self.canvas_circle = Ctk.CTkCanvas(self.root,width = 230, height = 230, background = root["bg"])
        self.canvas_circle.grid(row = row, column = 0,columnspan=4, padx = 10, pady = 10)
        row+=1
        self.sheet = tksheet.Sheet(root, column_width = 90, height = 40, width = 7 * 90+30,
                              show_x_scrollbar = False,show_y_scrollbar = False,row_index_width = 0,
                              header_font = ("Calibri", 8, "normal"),
                              index_font = ("Calibri", 9, "normal"))
        self.sheet.grid(row = row, column = 0, columnspan = 5, padx = 5, pady = 5)
        self.sheet.enable_bindings("single_select", "row_select", "column_width_resize","arrowkeys",
                               "right_click_popup_menu", "rc_select", "rc_insert_row", "rc_delete_row",
                               "copy","cut","paste","delete", "undo","edit_cell")
        self.sheet.headers(["Radius","X","Y","dX","dY","Accum","area"], )
        self.sheet.change_theme("dark")
        self.sheet.table_align("c")
        self.__init_sheet__()
        row+=1
        save_btn = Ctk.CTkButton(self.root, text = "Save", command = self.save)
        save_btn.grid(row = row, column = 1, rowspan = 2, padx = 0, pady = 0)
        rmv_btn = Ctk.CTkButton(self.root, text = "Remove", command = self.remove,fg_color='red',hover_color="#8B0000")
        rmv_btn.grid(row = row, column = 2, rowspan = 2, padx = 0, pady = 0)
        self.image1 = None
        self.image2 = None
        self.im_diff = None
        self.im_edge = None
        self.im_thr = None
        self.im_circle = None
        self.path1 = None
        self.path2 = None
        self.df = pd.DataFrame()

        self.data = np.array([])
        self.crop = [600,2610, 1370,3520]
        self.History = MyScrollableCheckboxFrame(self.root, title = "History", values = [],
                                                 function = self.history_sel)
        self.History.grid(row = 0, column = 10, rowspan=10, padx = (0, 10), pady = (10, 0), sticky = "nse")
        self.load_df()

    def __init_sheet__(self):
        self.sheet.set_sheet_data([[f"{val:.{t}f}" for val, t in zip(arr, [0, 0, 0, 0, 0, 2, 0])] for arr in [[0, 0, 0, 0, 0, 0, 0]]])
        for i,_ in enumerate(self.sheet.data):
            self.sheet[i, 5].bg = "black"


    def __init_ax__(self, length=40):
        start = 4
        self.canvas_axes.create_line(start, start, length-start, start, arrow=tk.LAST, width=2, fill="white")
        self.canvas_axes.create_line(start, start, start,  length-start, arrow=tk.LAST, width=2, fill="white")
        self.canvas_axes.create_text(length-4, start+10, text="X", fill="white")
        self.canvas_axes.create_text(start+10 ,length-4, text="Y", fill="white")

    def resize_with_aspect_ratio(self, img, max_size = (250, 250)):
        """Resize the image while keeping the aspect ratio."""
        if img.dtype != np.uint8:
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
            img = img.astype(np.uint8)

        aspect_ratio = img.shape[1] / img.shape[0]

        if img.shape[1] > img.shape[0]:
            new_w = max_size[0]
            new_h = int(new_w / aspect_ratio)
        else:
            new_h = max_size[1]
            new_w = int(new_h * aspect_ratio)

        resized_img = cv2.resize(img, (new_w, new_h))
        return resized_img

    def plot_image(self, image):
        image = resize_image(image, 230, 230)  # Resize the image using cv2  # Convert from BGR (OpenCV default) to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)  # Convert cv2 image (numpy array) to PIL Image
        return ImageTk.PhotoImage(image)

    def load_df(self):
        dir = self.dir
        if os.path.isfile(dir+"/"+"data.csv"):
            dtype = {"radius":float,"X":float,"Y":float,"dX":float,"dY":float,"accum":float,"radius_goal":float,"n_dots":float,
                     "crop_top":float,"crop_bottom":float,"crop_left":float,"crop_right":float,"pxl_accuracy":float,"area":float}
            df = pd.read_csv(dir+"/"+"data.csv",dtype=dtype)
        else :
            df = pd.DataFrame({"file": os.listdir(dir)})
            df = df[df["file"].str[-4:] == ".bmp"]
            df["num"] = df["file"].str[-14:-4].astype('int')
            df["file_path"] = df["file"].apply(lambda x: os.path.join(dir, str(x)))
            df["radius"] = None
            df["Reference_image"] = None
        if "dot_nums" not in df.columns:
            df["dot_nums"] = 0
        df = df.set_index(["file","dot_nums"])
        self.df = df
        self.update_history()

    def update_history(self):
        df = self.df.loc[~self.df["Reference_image"].isnull()]
        df.sort_values(by=['num'])
        self.History.create_labels(df.index.get_level_values(0).unique())

    def select_directory(self):
        dir = filedialog.askdirectory(initialdir=self.dir)
        if dir != '':
            self.dir = dir
            self.dir_label.configure(text=self.dir)
            self.load_df()

    def select_image1(self,file_path=None):
        self.__init_sheet__()
        if file_path is None :
            file_path = filedialog.askopenfilename(initialdir=self.dir
                                               ,filetypes=[("Image files", "*.bmp")])
        if file_path:
            self.filename1.configure(text=os.path.basename(file_path))
            img = cv2.imread(file_path)  # Read the image using cv2
            img = self.resize_with_aspect_ratio(img)  # Resize the image using cv2
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV default) to RGB
            img = Image.fromarray(img)  # Convert cv2 image (numpy array) to PIL Image
            self.path1 = file_path
            self.image1 = ImageTk.PhotoImage(img)  # Convert to ImageTk for display in Tkinter
            self.canvas1.create_image(0, 0, anchor=tk.NW, image=self.image1)
            self.load_df()
            num = self.df.loc[os.path.basename(file_path),"num"].values[0]
            prev_path = self.df.loc[self.df.loc[:,"num"]==num-1,"file_path"]
            if len(prev_path)>0:
                self.select_image2(file_path=prev_path.values[0])
    def select_image2(self,file_path=None):
        if file_path is None :
            file_path = filedialog.askopenfilename(initialdir=self.dir
                                               ,filetypes=[("Image files", "*.bmp")])
        if file_path:
            self.filename2.configure(text = os.path.basename(file_path))
            img = cv2.imread(file_path)  # Read the image using cv2
            img = self.resize_with_aspect_ratio(img)  # Resize the image using cv2
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV default) to RGB
            img = Image.fromarray(img)  # Convert cv2 image (numpy array) to PIL Image
            self.path2 = file_path
            self.image2 = ImageTk.PhotoImage(img)  # Convert to ImageTk for display in Tkinter
            self.canvas2.create_image(0, 0, anchor=tk.NW, image=self.image2)

    def __analysis_images__(self,list_img):
        im_diff, im_edge, imag = list_img
        self.im_diff = self.plot_image(im_diff)
        self.canvas_diff.create_image(0, 0, anchor = tk.NW, image = self.im_diff)
        self.im_edge = self.plot_image(im_edge)
        self.canvas_edge.create_image(0, 0, anchor = tk.NW, image = self.im_edge)
        self.im_circle = self.plot_image(imag)
        self.canvas_circle.create_image(0, 0, anchor = tk.NW, image = self.im_circle)

    def analyse(self):
        crop = [600,2610, 1370,3520] if self.chip_combobox.get() == "NTD" else [600, 2010, 1370, 2820]
        if self.chip_combobox.get() == "LUMI NTD":
            crop = [600, 3010, 1370, 3620]
        radius_guess = int(self.radius_combobox.get())
        numberdots = int(self.numberdots_combobox.get())
        pxlaccu = int(self.pxlaccu_combobox.get())
        radius_list,xs,ys,accums_list,area,crop,list_img = get_dots(self.path1, self.path2, crop = crop, r_guess = radius_guess,
                                                                          n_dots = numberdots, pxl_accuracy = pxlaccu)
        dx = xs - (crop[3] - crop[2]) // 2
        dy = ys - (crop[1] - crop[0]) // 2
        self.crop = crop
        self.__analysis_images__(list_img)
        if len(accums_list)>len(area):
            area = [area[0]]*len(accums_list)
        self.data = np.array([radius_list,xs,ys,dx,dy,accums_list,area]).T
        self.__update_sheet__()


    def __update_sheet__(self):
        self.sheet.set_sheet_data([[f"{val:.{t}f}" for val,t in zip(arr,[0,0,0,0,0,2,0])]for arr in self.data])
        for i,arr in enumerate(self.data):
            if arr[5]<0.15:
                self.sheet[i, 5].bg = "red"
            else:
                self.sheet[i, 5].bg = "black"
    def history_sel(self,x):
        df = self.df.loc[(x,0)]
        self.select_image1(os.path.join(self.dir,df.name[0]))
        self.select_image2(os.path.join(self.dir,df["Reference_image"]))
        self.numberdots_combobox.set("{:.0f}".format(df["n_dots"]))
        self.radius_combobox.set("{:.0f}".format(df["radius_goal"]))
        self.chip_combobox.set(df["Chip"])
        self.pxlaccu_combobox.set("{:.0f}".format(df["pxl_accuracy"]))
        self.support_textbox.delete("1.0", 'end-1c')
        if not pd.isnull(df["support_name"]):
            self.support_textbox.insert("0.0", df["support_name"])
        self.Chip_textbox.delete("1.0", 'end-1c')
        if not pd.isnull(df["Chip_name"]):
            self.Chip_textbox.insert("0.0", df["Chip_name"])
        self.crop = self.df.loc[(x,0),["crop_top","crop_bottom","crop_left","crop_right"]].to_numpy(int)
        cy,cx,dx,dy,radii,area = self.df.loc[x, ["Y", "X", "dX", "dY","radius","area"]].to_numpy(np.int32).T
        # for i in df.index:
        #     if not self.df.loc[(x,i), ["radius","area"]].isna().sum():
        #         radii,area = self.df.loc[x, ["radius","area"]].to_numpy(np.int32).reshape(-1,1)
        accums_list = self.df.loc[x, ["accum"]].to_numpy(float).reshape(-1)
        list_img = plot_dots(os.path.join(self.dir,df.name[0]), os.path.join(self.dir,df["Reference_image"]),self.crop, cy,cx,radii)
        self.__analysis_images__(list_img)
        self.data = np.array([radii, cx, cy, dx, dy, accums_list,area]).T
        self.__update_sheet__()

    def save(self):
        for i,data in enumerate(self.data):
            if i not in self.df.index.get_level_values(1):
                self.df.loc[(os.path.basename(self.path1), i),:] = [float('nan')] * len(self.df.columns)
            self.df.loc[(os.path.basename(self.path1),i),["radius","X","Y","dX","dY","accum","area"]] = data
        self.df.loc[os.path.basename(self.path1),["Chip","radius_goal","n_dots","pxl_accuracy"]] = [self.chip_combobox.get(),
                                                                                     int(self.radius_combobox.get()),
                                                                                     int(self.numberdots_combobox.get()),
                                                                                     int(self.pxlaccu_combobox.get())]
        self.df.loc[os.path.basename(self.path1), "Reference_image"] = os.path.basename(self.path2)
        self.df.loc[os.path.basename(self.path1), ["crop_top","crop_bottom","crop_left","crop_right"]] = self.crop
        self.df.loc[os.path.basename(self.path1), ["Chip_name","support_name"]]=[self.Chip_textbox.get("1.0",'end-1c'),self.support_textbox.get("1.0",'end-1c')]
        self.df.to_csv(os.path.dirname(self.path1)+"/"+"data.csv")
        self.update_history()
    def remove(self):
        self.df = self.df[self.df.index.get_level_values(0) != os.path.basename(self.path1)]
        self.df.to_csv(os.path.dirname(self.path1) + "/" + "data.csv")
        self.update_history()
def auto_analysis():
    df_b = pd.read_csv(os.path.join("/media/mp274748/Transcend/data/Glue_Files/241211_140213/CAM1/","data.csv"))
    df_b = df_b.set_index("file")
    df = df_b.loc[np.logical_not(df_b["radius"].isnull())]
    for i in df.index:
        if df.loc[i,"radius"] != np.nan:
            path1 = df.loc[i,"file_path"]
            path2 = os.path.join("/media/mp274748/Transcend/data/Glue_Files/241015_145732/CAM1",df.loc[i,'Reference_image'])
            crop = [600, 2610, 1370, 3520]
            radius_guess = 500
            numberdots = 1
            pxlaccu = 1
            radius_list, xs, ys, accums_list, area, crop, list_img = get_dots(path1, path2, crop = crop,
                                                                        r_guess = radius_guess,
                                                                        n_dots = numberdots, pxl_accuracy = pxlaccu)
            dx = xs - (crop[3] - crop[2]) // 2
            dy = ys - (crop[1] - crop[0]) // 2
            df_b.loc[i, ["radius", "X", "Y", "dX", "dY", "accum","area"]] = np.array([radius_list,xs,ys,dx,dy,accums_list,area]).T
            df_b.loc[i, ["crop_top", "crop_bottom", "crop_left", "crop_right"]]=crop
            df_b.loc[i,["radius_goal","pxl_accuracy"]]=[radius_guess,pxlaccu]
    df_b.to_csv(os.path.join("/media/mp274748/Transcend/data/Glue_Files/241015_145732/CAM1","data.csv"))
def inherit_previous():
    df = pd.read_csv(os.path.join("/media/mp274748/Transcend/data/Glue_Files/241211_140213/CAM1", "data.csv"),
                     index_col = 1)
    big_dot_idx = df[~df["radius"].isnull()].index + 1
    df.loc[big_dot_idx, ["Chip", "n_dots", "pxl_accuracy", "Reference_image", "crop_top", "crop_bottom", "crop_left",
                         "crop_right", "Chip_name", "support_name"]] = df.loc[
        big_dot_idx - 1, ["Chip", "n_dots", "pxl_accuracy", "Reference_image", "crop_top", "crop_bottom", "crop_left",
                          "crop_right", "Chip_name", "support_name"]].values
    df = df.reset_index()
    df = df.set_index("file")
    df.to_csv(os.path.join("/media/mp274748/Transcend/data/Glue_Files/241211_140213/CAM1", "data.csv"))


if __name__ == "__main__":
    root = Ctk.CTk()
    app = ImageSelector(root)
    root.mainloop()
    # auto_analysis()
