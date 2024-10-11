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

def get_dots(path,path_ref,crop=None, blur=100, acceptance=0.4):
    imag = cv2.imread(path)
    if crop is None:
        crop = [0,imag.shape[0],0,imag.shape[1]]
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
                    center_corrected_list.append((x0 - 0.5 * (crop[1] - crop[0]), y0 - 0.5 * (crop[3] - crop[2])))
                    error_list.append(error)
                    minmaxes.append(minmax)
                    cv2.circle(imag, center, int(equi_diameter), (255,0,0), 10)
    return (diameter_list,center_corrected_list,error_list,minmaxes,
            [convert_arr_2_img(im_diff),convert_arr_2_img(im_uniform),convert_arr_2_img(im_thr),convert_arr_2_img(imag)])


class ImageSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Selector")

        self.canvas1 = tk.Label(self.root)
        self.canvas1.grid(row=0, column=0, padx=10, pady=10)

        self.canvas2 = tk.Label(self.root)
        self.canvas2.grid(row=0, column = 1,columnspan=3, padx=10, pady=10)

        select_btn1 = tk.Button(self.root, text="Glue Dot", command=self.select_image1)
        select_btn1.grid(row=1, column=0, padx=10, pady=10)

        select_btn2 = tk.Button(self.root, text="Reference", command=self.select_image2)
        select_btn2.grid(row=1, column = 1,columnspan=3, padx=10, pady=10)

        analyse_btn = tk.Button(self.root, text="Analyse", command=self.analyse)
        analyse_btn.grid(row=2, column=0, padx=10, pady=10)

        self.crop_var = tk.StringVar()
        self.crop_combobox = ttk.Combobox(root, textvariable = self.crop_var, width = 5,
                                               values = ["NTD", "heater"])
        self.crop_combobox.grid(row = 2, column = 1, padx = 5, pady = 5)
        self.crop_combobox.set("NTD")

        self.blur_var = tk.StringVar()
        self.blur_combobox = ttk.Combobox(root, textvariable = self.blur_var, width = 5,
                                          values = ["{:.0f}".format(i*10) for i in range(1,11)])
        self.blur_combobox.grid(row = 2, column = 2, padx = 5, pady = 5)
        self.blur_combobox.bind("<<ComboboxSelected>>", func = lambda x: self.analyse())
        self.blur_combobox.set("100")

        self.acceptance_var = tk.StringVar()
        self.acceptance_combobox = ttk.Combobox(root, textvariable = self.acceptance_var, width = 5,
                                          values = ["{:.1f}".format(i * 0.1) for i in range(1,11)])
        self.acceptance_combobox.grid(row = 2, column = 3, padx = 5, pady = 5)
        self.acceptance_combobox.bind("<<ComboboxSelected>>", func = lambda x: self.analyse())
        self.acceptance_combobox.set("0.4")

        self.canvas_diff = tk.Label(self.root)
        self.canvas_diff.grid(row = 3, column = 0, padx = 10, pady = 10)

        self.canvas_uniform = tk.Label(self.root)
        self.canvas_uniform.grid(row = 3, column = 1,columnspan=3, padx = 10, pady = 10)

        self.canvas_thr = tk.Label(self.root)
        self.canvas_thr.grid(row = 4, column = 0, padx = 10, pady = 10)

        self.canvas_circle = tk.Label(self.root)
        self.canvas_circle.grid(row = 4, column = 1,columnspan=3, padx = 10, pady = 10)

        self.sheet = tksheet.Sheet(root, column_width = 90, height = 40, width = 5 * 90+40,
                              show_x_scrollbar = False,show_y_scrollbar = False,row_index_width = 0,
                              header_font = ("Calibri", 8, "normal"),
                              index_font = ("Calibri", 9, "normal"))
        self.sheet.grid(row = 5, columnspan = 4, padx = 5, pady = 5)
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
            img = cv2.imread(file_path)  # Read the image using cv2
            img = self.resize_with_aspect_ratio(img)  # Resize the image using cv2
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV default) to RGB
            img = Image.fromarray(img)  # Convert cv2 image (numpy array) to PIL Image
            self.path1 = file_path
            self.image1 = ImageTk.PhotoImage(img)  # Convert to ImageTk for display in Tkinter
            self.canvas1.config(image = self.image1)
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
            img = cv2.imread(file_path)  # Read the image using cv2
            print(img.dtype)
            img = self.resize_with_aspect_ratio(img)  # Resize the image using cv2
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV default) to RGB
            img = Image.fromarray(img)  # Convert cv2 image (numpy array) to PIL Image
            self.path2 = file_path
            self.image2 = ImageTk.PhotoImage(img)  # Convert to ImageTk for display in Tkinter
            self.canvas2.config(image = self.image2)

    def analyse(self):
        crop = [500,2710,1270,3520] if self.crop_combobox.get() == "NTD" else [500,2410,1270,3420]
        blur = int(self.blur_combobox.get())
        acceptance = float(self.acceptance_combobox.get())
        diameter_list,center_list,error_list,minmaxes,list_img = get_dots(self.path1, self.path2,crop = crop, blur=blur,
                                                                          acceptance = acceptance)
        center_list = np.array(center_list)
        im_diff, im_uniform, im_thr, imag = list_img
        self.im_diff = self.plot_image(im_diff)
        self.canvas_diff.config(image = self.im_diff)
        self.im_uniform =self.plot_image(im_uniform)
        self.canvas_uniform.config(image = self.im_uniform)
        self.im_thr =self.plot_image(im_thr)
        self.canvas_thr.config(image = self.im_thr)
        self.im_circle =self.plot_image(imag)
        self.canvas_circle.config(image = self.im_circle)
        data = np.array([diameter_list,center_list[:,0],center_list[:,1],error_list,minmaxes]).T
        ts = [0,0,0,0,2]
        self.sheet.set_sheet_data([[f"{val:.{t}f}" for val,t in zip(arr,ts)]for arr in data])

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSelector(root)
    root.mainloop()
