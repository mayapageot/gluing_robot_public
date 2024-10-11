import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy
import cv2
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN,KMeans
from scipy.interpolate import UnivariateSpline,splev,splprep
from scipy.spatial import KDTree

def get_close_point(curve, test_points, threshold = 0.5):
    # Create spline interpolation function for the curve
    curve_x = curve[:, 0]
    curve_y = curve[:, 1]
    tck, u = splprep([curve_x, curve_y], s = 0, k = 3)  # s=0 for interpolation, k=3 for cubic spline
    u_fine = np.linspace(0, 1, 100)  # Generate 100 points along the spline
    x_fine, y_fine = splev(u_fine, tck)


    # Create a KD-Tree for fast nearest-neighbor search
    curve_points = np.vstack((x_fine, y_fine)).T
    tree = KDTree(curve_points)

    # Query the KD-Tree to find the closest curve points to the test points
    distances, indices = tree.query(test_points, k = 1)  # k=1 for the closest point

    # Define a distance threshold

    close_points_indices = distances.flatten() <= threshold
    close_points = test_points[close_points_indices]
    return close_points
def rotation_matrix(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


def filter(im,thr=80,ks=11):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    #kernel2 = np.ones((ks, ks), np.float32) / 40 ** 2
    #img = cv2.filter2D(src = gray, ddepth = -1, kernel = kernel2)
    #rms = np.sqrt(np.mean(img.astype(np.float32)**2))
    img = cv2.GaussianBlur(gray,(ks,ks),0.)
    # Threshold the image to create a binary image
    mask = cv2.inRange(img, 0, thr)
    return mask
def circle_residuals(params, x, y):
    a, b, R = params
    return np.sqrt((x - a) ** 2 + (y - b) ** 2) - R


def fit_circle(x, y):
    # Initial guess for the center and radius
    x_m = np.mean(x)
    y_m = np.mean(y)
    R_guess = np.mean(np.sqrt((x - x_m) ** 2 + (y - y_m) ** 2))
    params_initial = [x_m, y_m, R_guess]

    result = scipy.optimize.least_squares(circle_residuals, params_initial, args = (x, y))

    a, b, R = result.x
    return a, b, R
class circle_on_tk:
    def __init__(self,canvas,center,r,**kwargs):
        self.canvas ,self.center, self.r ,self.kwargs = canvas,center, r,kwargs
        self.x,self.y = center[0], center[1]
        x1, y1, x2, y2 = center[0]-r,center[1]-r,center[0]+r,center[1]+r
        self.id = canvas.create_oval(x1, y1, x2, y2,**kwargs)

class point_on_tk:
    def __init__(self,canvas,center,**kwargs):
        self.canvas ,self.center ,self.kwargs = canvas,center,kwargs
        r=2
        x1, y1, x2, y2 = center[0]-r,center[1]-r,center[0]+r,center[1]+r
        self.id = canvas.create_oval(x1, y1, x2, y2,**kwargs)
class ShapeDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Shape Drawer")

        # Create Canvas
        self.canvas1 = tk.Canvas(root, width=800, height=800, bg='white')
        self.canvas1.grid(row=0, column=0, padx=10, pady=10)

        # Buttons to load images
        self.load_btn1 = tk.Button(root, text="Load Image 1", command=self.load_image1)
        self.load_btn1.grid(row=1, column=0, pady=10)


        # Button to calculate and display 2D shape
        self.calculate_btn = tk.Button(root, text="Calculate 2D Shape", command=self.calculate_shape)
        self.calculate_btn.grid(row=2, column=0, pady=10)

        self.calculate_btn = tk.Button(root, text = "Save", command = self.save)
        self.calculate_btn.grid(row = 3, column = 0, pady = 10)
        self.file_path = None
        self.image1 = None
        # Store the points
        self.points1 = []
        self.circles = []
        self.z, self.min, self.max = None, None, None
        # Bind mouse events to the canvas
        self.canvas1.bind("<Button-1>", self.draw_point1)
        self.imagecv=None
        self.factor = 3
    def load_image1(self):
        file_path = filedialog.askopenfilename(initialdir= "/local/home/mp274748/Documents/data/Glue/")
        self.file_path = file_path
        if file_path:
            self.imagecv =  cv2.imread(file_path)[450:2850, 1250:3650]
            self.image1 = Image.open(file_path).crop((1250, 450, 3650, 2850))
            self.image1 = self.image1.resize((800, 800), Image.LANCZOS)
            self.tk_image1 = ImageTk.PhotoImage(self.image1)
            self.canvas1.create_image(0, 0, anchor=tk.NW, image=self.tk_image1)

    def draw_point1(self, event):
        #if len(self.points1)==0:
            #self.canvas1.delete('all')
            #self.canvas1.create_image(0, 0, anchor = tk.NW, image = self.tk_image1)
        x, y = event.x, event.y
        for circle in self.circles:
            if (circle.center[0]-x)**2 + (circle.center[1]-y)**2<20**2:
                print((circle.center[0]-x)**2 + (circle.center[1]-y)**2)
                self.canvas1.delete(circle.id)
        self.points1.append(point_on_tk(self.canvas1,(x,y), fill='red'))
        #if len(self.points1) ==2:
        #    self.calculate_circle()


    def calculate_shape(self):
        points = np.array([pts.center for pts in self.points1])
        for pts in self.points1:
            self.canvas1.delete(pts.id)
        self.points1 = []
        clustering = KMeans(n_clusters = 5).fit(points)
        for i in range(5):
            group = points[np.where(clustering.labels_==i)]
            x = group[:, 0]
            y = group[:, 1]
            center_x, center_y, radius = fit_circle(x, y)
            center = (center_x, center_y)
            print(center,radius)
            self.circles.append(circle_on_tk(self.canvas1,center,radius, width = 1))
    def calculate_circle(self):
        points_inf = np.array([pts.center for pts in self.points1])*self.factor
        for pts in self.points1:
            self.canvas1.delete(pts.id)
        self.points1 = []
        center_dot=points_inf[0]
        print(center_dot)
        if len(points_inf)>1:
            side_dot = points_inf[1]
            r = int(np.linalg.norm(center_dot- side_dot))
        else :
            r =200
        Im_b = self.imagecv[center_dot[1] - r:center_dot[1] + r, center_dot[0] - r:center_dot[0] + r]

        Im_b = filter(-Im_b, thr = 40, ks = 61)

        edges = cv2.Canny(Im_b, 100, 200)
        points = np.vstack(np.where(edges)).T
        n_x, n_y = np.shape(Im_b)
        points = points[np.linalg.norm(points - [n_x // 2, n_y // 2], axis = 1) < r]
        hull = ConvexHull(points)
        vertices = hull.vertices
        sel_point = get_close_point(points[vertices], points, 10)
        plt.imshow(Im_b, cmap = 'gray')
        plt.scatter(sel_point[:,1],sel_point[:,0])
        plt.show()
        x, y = sel_point[:, 1], sel_point[:, 0]
        center_x, center_y, radius = fit_circle(x, y)
        center = (center_x, center_y)
        center_canvas =( center[0]+center_dot[0] - r)//self.factor,(center[1]+center_dot[1] - r)//self.factor
        self.circles.append(circle_on_tk(self.canvas1, center_canvas, radius//self.factor,width = 1))
        return center, radius
    def save(self):
        try :
            df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/test.csv",header=0)
        except :
            df = pd.DataFrame(columns=["filename","center_x",	"center_y"	,"diameter"])
        centers_x = [cir.x*self.factor + 1250 for cir in self.circles]
        centers_y = [cir.y * self.factor + 450 for cir in self.circles]
        radiuses = [cir.r * self.factor for cir in self.circles]
        df = pd.concat([df, pd.DataFrame({"filename":[self.file_path]*len(centers_y),"center_x":centers_x,	"center_y":centers_y	,"diameter":radiuses})], ignore_index = True)
        df.to_csv("/local/home/mp274748/Documents/data/Glue/test.csv",index=False)

root = tk.Tk()
ShapeDrawer(root)
root.mainloop()