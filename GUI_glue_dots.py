import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import tksheet
import cv2
import os
import pandas as pd
import numpy as np
import scipy
def convert_arr_2_img(arr):
    image_array_normalized = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX)
    image_array_normalized = image_array_normalized.astype(np.uint8)
    if len(image_array_normalized.shape)==2:
        return cv2.cvtColor(image_array_normalized,cv2.COLOR_GRAY2RGB)
    else :
        return image_array_normalized


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


def get_dots(path,path_ref,crop=None, blur=100, acceptance=0.4):
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
    mask = im_masked<np.max(im_masked)*acceptance#6
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
    return (diameter_list,center_corrected_list,error_list,minmaxes,
            [convert_arr_2_img(im_diff),convert_arr_2_img(im_uniform),convert_arr_2_img(im_thr),convert_arr_2_img(imag)])


class ImageSelector:
    def __init__(self, root):

        self.root = root
        self.root.title("Image Selector")
        #self.root.geometry("320x220")
        row = 0
        self.canvas1 = tk.Canvas(self.root,width = 250, height = 200)
        self.canvas1.grid(row=row, column=0, columnspan = 2, padx=0, pady=0)

        self.canvas2 = tk.Canvas(self.root,width = 250, height = 200)
        self.canvas2.grid(row=row, column = 2,columnspan=3, padx=0, pady=0)
        row+=1
        self.filename1 = tk.Label(self.root , text = "")
        self.filename1.grid(row=row, column = 0, columnspan = 2,padx=0, pady=0)

        self.filename2 = tk.Label(self.root, text = "")
        self.filename2.grid(row = row, column = 2, columnspan = 3, padx = 0, pady = 0)
        row+=1
        select_btn1 = tk.Button(self.root, text="Glue Dot", command=self.select_image1)
        select_btn1.grid(row=row, column=0, columnspan = 2, padx=10, pady=10)

        select_btn2 = tk.Button(self.root, text="Reference", command=self.select_image2)
        select_btn2.grid(row=row, column = 2,columnspan=3, padx=10, pady=10)
        row+=1
        self.anaLabel = tk.Label(self.root, text = "")
        self.anaLabel.grid(row = row, column = 1, padx = 0, pady = 0)

        self.chipLabel = tk.Label(self.root, text = "Chip")
        self.chipLabel.grid(row = row, column = 2, padx = 0, pady = 0)

        self.blurLabel = tk.Label(self.root, text = "Blur")
        self.blurLabel.grid(row = row, column = 3, padx = 0, pady = 0)

        self.acceptanceLabel = tk.Label(self.root, text = "Threshold")
        self.acceptanceLabel.grid(row = row, column = 4, padx = 0, pady = 0)

        self.canvas = tk.Canvas(self.root, width = 70, height = 70)
        self.canvas.grid(row = row, column = 0,rowspan=2, padx = 0, pady = 0)
        self.draw_axes(70)
        analyse_btn = tk.Button(self.root, text = "Analyse", command = self.analyse)
        analyse_btn.grid(row = row, column = 1,rowspan=2, padx = 0, pady = 0)

        row+=1


        self.chip_var = tk.StringVar()
        self.chip_combobox = ttk.Combobox(root, textvariable = self.chip_var, width = 5,
                                          values = ["NTD", "heater"])
        self.chip_combobox.grid(row = row, column = 2, padx = 0, pady = 0)
        self.chip_combobox.set("NTD")

        self.blur_var = tk.StringVar()
        self.blur_combobox = ttk.Combobox(root, textvariable = self.blur_var, width = 5,
                                          values = ["{:.0f}".format(i*10) for i in range(11)])
        self.blur_combobox.grid(row = row, column = 3, padx = 0, pady = 0)
        self.blur_combobox.bind("<<ComboboxSelected>>", func = lambda x: self.analyse())
        self.blur_combobox.set("0")

        self.acceptance_var = tk.StringVar()
        self.acceptance_combobox = ttk.Combobox(root, textvariable = self.acceptance_var, width = 5,
                                          values = ["{:.1f}".format(i * 0.1) for i in range(1,11)])
        self.acceptance_combobox.grid(row = row, column = 4, padx = 0, pady = 0)
        self.acceptance_combobox.bind("<<ComboboxSelected>>", func = lambda x: self.analyse())
        self.acceptance_combobox.set("0.4")
        row +=1
        self.canvas_diff =  tk.Canvas(self.root,width = 250, height = 250)
        self.canvas_diff.grid(row = row, column = 0,columnspan=2, padx = 10, pady = 10)

        self.canvas_uniform = tk.Canvas(self.root,width = 250, height = 250)
        self.canvas_uniform.grid(row = row, column = 2,columnspan=3, padx = 10, pady = 10)
        row+=1
        self.canvas_thr = tk.Canvas(self.root,width = 250, height = 250)
        self.canvas_thr.grid(row = row, column = 0,columnspan=2, padx = 10, pady = 10)

        self.canvas_circle =  tk.Canvas(self.root,width = 250, height = 250)
        self.canvas_circle.grid(row = row, column = 2,columnspan=3, padx = 10, pady = 10)
        row+=1
        self.sheet = tksheet.Sheet(root, column_width = 90, height = 40, width = 5 * 90+40,
                              show_x_scrollbar = False,show_y_scrollbar = False,row_index_width = 0,
                              header_font = ("Calibri", 8, "normal"),
                              index_font = ("Calibri", 9, "normal"))
        self.sheet.grid(row = row, column = 0, columnspan = 5, padx = 5, pady = 5)
        self.sheet.enable_bindings(("single_select", "row_select", "column_width_resize","arrowkeys",
                               "right_click_popup_menu", "rc_select", "rc_insert_row", "rc_delete_row",
                               "copy","cut","paste","delete", "undo","edit_cell"))
        self.sheet.headers(["radius","X","Y","fit error","(max-min)/max"], )
        self.image1 = None
        self.image2 = None
        self.im_diff = None
        self.im_uniform = None
        self.im_thr = None
        self.im_circle = None
        self.path1 = None
        self.path2 = None
        self.df = None

    def draw_axes(self,length=40):
        start = 4
        self.canvas.create_line(start, start, length-start, start, arrow=tk.LAST, width=2)
        self.canvas.create_line(start, start, start,  length-start, arrow=tk.LAST, width=2)
        self.canvas.create_text(length-4, start+10, text="X", font=("Arial", 1, "bold"))
        self.canvas.create_text(start+10 ,length-4, text="Y", font=("Arial", 1, "bold"))
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
        image = self.resize_with_aspect_ratio(image)  # Resize the image using cv2  # Convert from BGR (OpenCV default) to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)  # Convert cv2 image (numpy array) to PIL Image
        return ImageTk.PhotoImage(image)

    def load_df(self,dir=None):
        df = pd.DataFrame({"file":os.listdir(dir)})
        df = df[df["file"].str[-4:]==".bmp"]
        df["num"] = df["file"].str[-14:-4].astype('int')
        df["file_path"] = dir + "/" + df["file"]
        self.df = df


    def select_image1(self):
        file_path = filedialog.askopenfilename(initialdir="/media/mp274748/Transcend/data/Glue_Files/241009_101103/CAM1"
                                               ,filetypes=[("Image files", "*.bmp")])
        if file_path:
            self.filename1.config(text=os.path.basename(file_path))
            img = cv2.imread(file_path)  # Read the image using cv2
            img = self.resize_with_aspect_ratio(img)  # Resize the image using cv2
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV default) to RGB
            img = Image.fromarray(img)  # Convert cv2 image (numpy array) to PIL Image
            self.path1 = file_path
            self.image1 = ImageTk.PhotoImage(img)  # Convert to ImageTk for display in Tkinter
            self.canvas1.create_image(0, 0, anchor=tk.NW, image=self.image1)
            self.load_df(os.path.dirname(file_path))
            num = self.df.loc[self.df["file_path"]==self.path1,"num"].values[0]
            prev_path = self.df.loc[self.df["num"]==num-1,"file_path"]
            if len(prev_path)>0:
                self.select_image2(file_path=prev_path.values[0])



    def select_image2(self,file_path=None):
        if file_path is None :
            file_path = filedialog.askopenfilename(initialdir="/media/mp274748/Transcend/data/Glue_Files/241009_101103/CAM1"
                                               ,filetypes=[("Image files", "*.bmp")])
        if file_path:
            self.filename2.config(text = os.path.basename(file_path))
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
        acceptance = float(self.acceptance_combobox.get())
        diameter_list,center_list,error_list,minmaxes,list_img = get_dots(self.path1, self.path2,crop = crop, blur=blur,
                                                                          acceptance = acceptance)
        center_list = np.array(center_list)
        im_diff, im_uniform, im_thr, imag = list_img
        self.im_diff = self.plot_image(im_diff)
        self.canvas_diff.create_image(0, 0, anchor=tk.NW, image=self.im_diff)
        self.im_uniform =self.plot_image(im_uniform)
        self.canvas_uniform.create_image(0, 0, anchor=tk.NW, image=self.im_uniform)
        self.im_thr =self.plot_image(im_thr)
        self.canvas_thr.create_image(0, 0, anchor=tk.NW, image=self.im_thr)
        self.im_circle =self.plot_image(imag)
        self.canvas_circle.create_image(0, 0, anchor=tk.NW, image=self.im_circle)
        data = np.array([diameter_list,center_list[:,0],center_list[:,1],error_list,minmaxes]).T
        ts = [0,0,0,0,2]
        self.sheet.set_sheet_data([[f"{val:.{t}f}" for val,t in zip(arr,ts)]for arr in data])
        for i,arr in enumerate(data):
            print(arr[3])
            if arr[3]>50:
                self.sheet[i, 3].bg = "red"
            if arr[4]>0.2:
                self.sheet[i, 4].bg = "red"



if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSelector(root)
    root.mainloop()
