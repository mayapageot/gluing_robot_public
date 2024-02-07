import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RectangleSelector
import inspect
import json
from PIL import Image
import pickle
import io
import matplotlib.gridspec as gridspec
import os
def get_res(res_path):
    for root, dirs, files in os.walk(res_path):
        # Print files in the current directory
        files = np.sort(files)
        res = os.path.join(root, files[-1])
        data = np.loadtxt(res, delimiter=',')
    return data
path = r"C:\GluingRobotData\Data_gluing\2024_02_06\192.168.200.2\SD2\cv-x"
res_path = path + r"\result\SD1_{:03d}".format(7)
data = get_res(res_path)
dx = data[:,0]-2316.263
print( (3.322-0.5,-57.078-0.5))
dy = data[:,1]-1829.806

dr = np.sqrt(dx**2+dy**2)
dr = np.concatenate((dr,[np.nan,np.nan,np.nan]))
print(dr.shape)
dr=dr.reshape((3,6))
fig , ax = plt.subplots()
ax.imshow(dr, cmap='bwr')
for i in range(3):
    for j in range(6):
        text = ax.text(j, i, round(dr[i, j],2),
                       ha="center", va="center", color="w")
print(dr)
plt.show()