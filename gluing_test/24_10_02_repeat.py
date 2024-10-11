import pandas as pd
from pptx import Presentation
from pptx.util import Inches
from pptx.dml.color import RGBColor
import matplotlib.pyplot as plt
pixel_to_um = 1.24
import os
import cv2
import numpy as np
import matplotlib
import scipy
matplotlib.use('TkAgg')
dir =  "/media/mp274748/Transcend/data/Glue_Files/241007_101305/CAM1/"
df = pd.DataFrame({"files":os.listdir(dir)})
df["num"]= df["files"].str[-14:-4].astype('int')
df["path"]= "/media/mp274748/Transcend/data/Glue_Files/241007_101305/CAM1/" + df["files"]
f = lambda num :  df.loc[df["num"]==num,"path"].values[0]
from matplotlib.widgets import Slider
im_ref =  np.array(cv2.cvtColor(cv2.imread(f(1)) ,cv2.COLOR_BGR2GRAY),dtype = np.int32)

def get_dots(path,path_ref=None,plot=False):
    imag = cv2.imread(path)
    im = np.array(cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY),dtype = np.int32)
    if path_ref!=None:
        im_ref = np.array(cv2.cvtColor(cv2.imread(path_ref), cv2.COLOR_BGR2GRAY), dtype = np.int32)
    # Initialize dx and dy
    """dx_init = -48
    dy_init = 107"""
    dx_init = 0
    dy_init = 0
    xmin,xmax,ymin,ymax = 0,0,0,0
    # Display the images with initial dx and dy
    image1 = np.abs(im_ref-im)
    image1 = scipy.ndimage.uniform_filter(image1,100)
    mask = image1<np.max(image1)*0.4#6
    image1[mask] = 0
    plt.imshow(image1)
    plt.show()
    image_array_normalized = cv2.normalize(image1, None, 0, 255, cv2.NORM_MINMAX)
    image_array_normalized = image_array_normalized.astype(np.uint8)
    color_im =  cv2.cvtColor(image_array_normalized,cv2.COLOR_GRAY2RGB)
    thr = cv2.inRange(image_array_normalized, 0, 100)
    contours, hierarchy = cv2.findContours(thr, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    ellipse_list = []
    center_list = []
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
                    error_list.append(error)
                    minmaxes.append(minmax)

                    cv2.circle(imag, center, int(equi_diameter), (255,0,0), 10)
                    #cv2.ellipse(imag, ellipse, (0,255, 0), 10)
    if plot :
        fig,ax = plt.subplots()
        ax.imshow(image1)
    return diameter_list,center_list,error_list,minmaxes
df["center_x"] = -np.ones(len(df))
df["center_y"] = -np.ones(len(df))
df["radius"] = -np.ones(len(df))
df["fit_error"] = -np.ones(len(df))
"""for i in [43]:
    diameter_list,center_list,error_list,minmaxes = get_dots(f(i))
    print(diameter_list[0]*pixel_to_um,center_list,error_list,minmaxes )
    plt.show()"""
#for i in [42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,80,83,85,87,89]:
for i in [60]:
    j=i-1
    if i ==42:
        j=37
    diameter_list,center_list,error_list,minmaxes = get_dots(f(i),f(j))
    print(center_list[0][0],center_list[0][1],diameter_list[0],error_list[0])
    #if len(diameter_list)>0:
        #df.loc[df["num"] == i, ["center_x", "center_y", "radius", "fit_error"]] = [center_list[0][0],center_list[0][1],diameter_list[0],error_list[0]]

    #print(df.loc[df["num"] == i,["center_x","center_y","radius","fit_error"]])
from utility import plots
#plots.slidded_bin_histogram(df.loc[df["center_x"]>0,"radius"])
df["time"]= df["files"].str[7:13].astype('float').apply(lambda x: x//1000*60+(x%1000//10)+(x%10/60))
"""plt.scatter(df.loc[df["center_x"]>0,"radius"]*pixel_to_um,df.loc[df["center_x"]>0,"fit_error"]*pixel_to_um)
print(df.loc[df["center_x"]>0,["num","radius","fit_error"]])
plt.xlabel("radius [$\mu m$]")
plt.ylabel("root mean square deviation of the fit[$\mu m$]")
plt.show()"""

#df.to_csv("/media/mp274748/Transcend/data/Glue_Files/241007_101305/241007_101305.csv",index = None)