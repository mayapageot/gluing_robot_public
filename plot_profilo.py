import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
import cv2
path_left = r"C:\GluingRobotData\Data_gluing\FTP\lj-x2d\profile\SD1_000\240220_161429\HEAD_A"
A = []
for root,dir,files in os.walk(path_left):
    for name in files:
        file_path = os.path.join(root, name)
        df = pd.read_csv(file_path, header=None)
        A.append(df.values[:,0])
B = np.array(A)
coef_x,coef_y = np.shape(B)/np.array([16,50])
B[(B<-1000) | (B>10000) ]=np.nan
resized_image = B #cv2.resize(B, (3200,16000), interpolation=cv2.INTER_LINEAR)
z=B
print(z)
x = np.arange(resized_image.shape[1])/coef_y
y = np.arange(resized_image.shape[0])/coef_x
x, y = np.meshgrid(x, y)
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z,cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

# Set initial viewing angle
ax.view_init(elev=30, azim=30)
ax.set_xlim(0,40)
ax.set_ylim(0,40)
plt.show()