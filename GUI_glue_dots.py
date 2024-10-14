import tkinter as tk
from customtkinter import filedialog
from PIL import Image, ImageTk
import tksheet
import cv2
import os
import pandas as pd
import numpy as np
import scipy
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


def get_dots(path, path_ref, crop=None, blur=100, threshold=0.4):
    imag = cv2.imread(path)
    if crop is None:
        crop = [0,imag.shape[0],0,imag.shape[1]]
    crop, center_chip = get_chip(path_ref,crop)
    imag=imag[crop[0]: crop[1], crop[2]: crop[3]]
    im = np.array(cv2.cvtColor(imag, cv2.COLOR_BGR2GRAY),dtype = np.int32)
    im_ref = np.array(cv2.cvtColor(cv2.imread(path_ref), cv2.COLOR_BGR2GRAY),dtype = np.int32)
    im_ref=im_ref[crop[0]: crop[1], crop[2]: crop[3]]
    im_diff = np.abs(im_ref-im)
    im_uniform = scipy.ndimage.uniform_filter(im_diff,blur)
    im_masked = np.copy(im_uniform)
    mask = im_masked < np.max(im_masked) * threshold#6
    im_masked[mask] = 0
    image_array_normalized = cv2.normalize(im_masked, None, 0, 255, cv2.NORM_MINMAX)
    image_array_normalized = image_array_normalized.astype(np.uint8)
    im_thr = cv2.inRange(image_array_normalized, 0, 100)
    contours, hierarchy = cv2.findContours(im_thr, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    ellipse_list = []
    center_list = []
    center_corrected_list = []
    diameter_list = []
    error_list=[]
    minmaxes = []
    for cnt in contours:
        adding = True
        if len(cnt)>4:

            ellipse = cv2.fitEllipse(cnt)
            if np.abs(ellipse[1][0]-ellipse[1][1])<100 and ellipse[1][0]>300:
                ellipse_list.append(ellipse)
                M = cv2.moments(cnt)
                x0 , y0 = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                center = (x0,y0)
                area = cv2.contourArea(cnt)
                equi_diameter = np.sqrt(4 * area / np.pi) / 2
                x = cnt[:,:,0]
                y = cnt[:,:,1]
                radiuses_2 = (x-x0)**2 + (y-y0)**2
                error = (np.mean(np.abs(radiuses_2 - equi_diameter**2)))**0.5
                minmax =(np.max(radiuses_2) - np.min(radiuses_2)) / equi_diameter ** 2
                for i, (c_b, mm_b) in enumerate(zip(center_list, minmaxes)):
                    if ((x0 - c_b[0]) ** 2 + (y0 - c_b[1]) ** 2 < 2000):
                        if mm_b>minmax:
                            diameter_list.pop(i)
                            center_list.pop(i)
                            error_list.pop(i)
                        else :
                            adding = False
                if adding and error <150:
                    diameter_list.append(equi_diameter)
                    center_list.append(center)
                    center_corrected_list.append((x0 - center_chip[0], y0 - center_chip[1]))
                    error_list.append(error)
                    minmaxes.append(minmax)
                    cv2.circle(imag, center, int(equi_diameter), (255,0,0), 10)
    return (diameter_list,center_corrected_list,error_list,minmaxes,crop,
            [convert_arr_2_img(im_diff),convert_arr_2_img(im_uniform),convert_arr_2_img(im_thr),convert_arr_2_img(imag)])

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
            text_label = Ctk.CTkLabel(self, text=label, text_color="blue", cursor="hand2")
            text_label.pack(pady=1)
            text_label.bind("<Button-1>", lambda e, text=label: self.on_click(text))
    def add_label(self,label):
        text_label = Ctk.CTkLabel(self, text = label, text_color = "blue", cursor = "hand2")
        text_label.pack(pady = 1)
        text_label.bind("<Button-1>", lambda e, text = label: self.on_click(text))
    def on_click(self, text):
        self.function(text)


class ImageSelector:
    def __init__(self, root):

        self.root = root
        self.root.title("Image Selector")
        self.dir = "/media/mp274748/Transcend/data/Glue_Files/241009_101103/CAM1"
        #self.root.geometry("320x220")
        row = 0
        self.dir_label = Ctk.CTkLabel(self.root, text = self.dir , text_color = "blue")
        self.dir_label.grid(row=row, column=0,columnspan = 4)
        self.dir_label.bind("<Button-1>", lambda x:self.select_directory())

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

        self.blurLabel = Ctk.CTkLabel(self.root, text = "Blur")
        self.blurLabel.grid(row = row, column = 3, padx = 0, pady = 0)

        self.acceptanceLabel = Ctk.CTkLabel(self.root, text = "Threshold")
        self.acceptanceLabel.grid(row = row, column = 4, padx = 0, pady = 0)

        self.canvas_axes = Ctk.CTkCanvas(self.root, width = 70, height = 70, background = root["bg"],highlightthickness = 0)
        self.canvas_axes.grid(row = row, column = 0,rowspan=2, padx = 0, pady = 0)
        self.draw_axes(70)

        analyse_btn = Ctk.CTkButton(self.root, text = "Analyse", command = self.analyse)
        analyse_btn.grid(row = row, column = 1,rowspan=2, padx = 0, pady = 0)

        row+=1

        self.chip_combobox = Ctk.CTkComboBox(root, width = 80,
                                          values = ["NTD", "heater"])
        self.chip_combobox.grid(row = row, column = 2, padx = 10, pady = 0)
        self.chip_combobox.set("NTD")

        self.blur_combobox = Ctk.CTkComboBox(root, width = 80,
                                          values = ["{:.0f}".format(i*10) for i in range(11)],
                                                  command = lambda x: self.analyse())
        self.blur_combobox.grid(row = row, column = 3, padx = 10, pady = 0)
        self.blur_combobox.set("0")

        self.threshold_combobox = Ctk.CTkComboBox(root, width = 80,
                                                  values = ["{:.1f}".format(i * 0.1) for i in range(1,11)],
                                                  command = lambda x: self.analyse())
        self.threshold_combobox.grid(row = row, column = 4, padx = 10, pady = 0)
        self.threshold_combobox.set("0.4")
        row +=1
        self.canvas_diff = Ctk.CTkCanvas(self.root,width = 230, height = 230, background = root["bg"])
        self.canvas_diff.grid(row = row, column = 0,columnspan=2, padx = 10, pady = 10)

        self.canvas_uniform = Ctk.CTkCanvas(self.root,width = 230, height = 230, background = root["bg"])
        self.canvas_uniform.grid(row = row, column = 2,columnspan=3, padx = 10, pady = 10)
        row+=1
        self.canvas_thr = Ctk.CTkCanvas(self.root,width = 230, height = 230, background = root["bg"])
        self.canvas_thr.grid(row = row, column = 0,columnspan=2, padx = 10, pady = 10)

        self.canvas_circle = Ctk.CTkCanvas(self.root,width = 230, height = 230, background = root["bg"])
        self.canvas_circle.grid(row = row, column = 2,columnspan=3, padx = 10, pady = 10)
        row+=1
        self.sheet = tksheet.Sheet(root, column_width = 90, height = 40, width = 5 * 90+40,
                              show_x_scrollbar = False,show_y_scrollbar = False,row_index_width = 0,
                              header_font = ("Calibri", 8, "normal"),
                              index_font = ("Calibri", 9, "normal"))
        ts = [0, 0, 0, 0, 2]
        self.sheet.set_sheet_data([[f"{val:.{t}f}" for val, t in zip(arr, ts)] for arr in [[0,0,0,0,0]]])
        self.sheet.grid(row = row, column = 0, columnspan = 5, padx = 5, pady = 5)
        self.sheet.enable_bindings(("single_select", "row_select", "column_width_resize","arrowkeys",
                               "right_click_popup_menu", "rc_select", "rc_insert_row", "rc_delete_row",
                               "copy","cut","paste","delete", "undo","edit_cell"))
        self.sheet.headers(["radius","X","Y","fit error","(max-min)/max"], )
        self.sheet.change_theme("dark")
        self.sheet.table_align("c")
        row+=1
        save_btn = Ctk.CTkButton(self.root, text = "Save", command = self.save)
        save_btn.grid(row = row, column = 1, rowspan = 2, padx = 0, pady = 0)
        self.image1 = None
        self.image2 = None
        self.im_diff = None
        self.im_uniform = None
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


    def draw_axes(self,length=40):
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
        df = pd.DataFrame({"file":os.listdir(dir)})
        df = df[df["file"].str[-4:]==".bmp"]
        df["num"] = df["file"].str[-14:-4].astype('int')
        df["file_path"] = dir + "/" + df["file"]
        df = df.set_index("file")
        if os.path.isfile(dir+"/"+"data.csv"):
            df_saved = pd.read_csv(dir+"/"+"data.csv")
            df_saved = df_saved.set_index("file")
            df.loc[df_saved.index,df_saved.columns] = df_saved
        self.df = df
        self.update_history()

    def update_history(self):
        df = self.df.loc[self.df["radius"]>0]
        df.sort_values(by=['num'])
        self.History.create_labels(df.index)

    def select_directory(self):
        self.dir = filedialog.askdirectory(initialdir="/media/mp274748/Transcend/data/Glue_Files/241009_101103/CAM1")
        self.dir_label.configure(text=self.dir)


    def select_image1(self,file_path=None):
        if file_path is None :
            file_path = filedialog.askopenfilename(initialdir="/media/mp274748/Transcend/data/Glue_Files/241009_101103/CAM1"
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
            num = self.df.loc[self.df["file_path"]==self.path1,"num"].values[0]
            prev_path = self.df.loc[self.df["num"]==num-1,"file_path"]
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

    def analyse(self):
        crop = [600,2610, 1370,3520] if self.chip_combobox.get() == "NTD" else [600, 2010, 1370, 2820]
        blur = int(self.blur_combobox.get())
        threshold = float(self.threshold_combobox.get())
        diameter_list,center_list,error_list,minmaxes,crop,list_img = get_dots(self.path1, self.path2, crop = crop, blur=blur,
                                                                          threshold = threshold)
        self.crop = crop
        center_list = np.array(center_list)
        im_diff, im_uniform, im_thr, imag = list_img
        self.im_diff = self.plot_image(im_diff)
        self.canvas_diff.create_image(0, 0, anchor=tk.NW, image=self.im_diff)
        self.im_uniform =self.plot_image(im_uniform)
        self.canvas_uniform.create_image(0, 0, anchor=tk.NW, image=self.im_uniform)
        self.im_thr =self.plot_image(255-im_thr)
        self.canvas_thr.create_image(0, 0, anchor=tk.NW, image=self.im_thr)
        self.im_circle =self.plot_image(imag)
        self.canvas_circle.create_image(0, 0, anchor=tk.NW, image=self.im_circle)
        self.data = np.array([diameter_list,center_list[:,0],center_list[:,1],error_list,minmaxes]).T
        ts = [0,0,0,0,2]
        self.sheet.set_sheet_data([[f"{val:.{t}f}" for val,t in zip(arr,ts)]for arr in self.data])
        for i,arr in enumerate(self.data):
            if arr[3]>50:
                self.sheet[i, 3].bg = "red"
            if arr[4]>0.2:
                self.sheet[i, 4].bg = "red"
    def history_sel(self,x):
        df = self.df.loc[x]
        self.select_image1(df["file_path"])
        self.select_image2(self.dir + "/" + df["Reference_image"])
        self.threshold_combobox.set("{:.1f}".format(df["threshold"]))
        self.blur_combobox.set("{:.0f}".format(df["blur"]))
        self.chip_combobox.set(df["Glue"])

    def save(self):
        self.df.loc[os.path.basename(self.path1),["radius","X","Y","fit error","(max-min)/max"]]=self.data[0]
        self.df.loc[os.path.basename(self.path1),["Glue","blur","threshold"]] = [self.chip_combobox.get(),self.blur_combobox.get(), self.threshold_combobox.get()]
        self.df.loc[os.path.basename(self.path1), "Reference_image"] = os.path.basename(self.path2)
        self.df.loc[os.path.basename(self.path1), ["crop_top","crop_bottom","crop_left","crop_right"]] = self.crop
        self.df.to_csv(os.path.dirname(self.path1)+"/"+"data.csv")
        self.update_history()


if __name__ == "__main__":
    root = Ctk.CTk()
    app = ImageSelector(root)
    root.mainloop()
