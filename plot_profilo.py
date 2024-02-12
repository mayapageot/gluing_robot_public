import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
import cv2
path_left = r"C:\GluingRobotData\Data_gluing\FTP\lj-x2d\profile\SD1_000\240212_145826\left"
path_img = r"C:\GluingRobotData\Data_gluing\2024_02_06\192.168.200.3\SD2\lj-x3d\image\SD1_009\240212_145255\240212_145255_0000000001_IMG_HEIGHT_OK.png"
A = []
for root,dir,files in os.walk(path_left):
    for name in files:
        file_path = os.path.join(root, name)
        df = pd.read_csv(file_path, header=None)
        A.append(df.values[:,0])
B = np.array(A)
B[(B<-0.5) | (B>0.25) ]=np.nan
resized_image = B #cv2.resize(B, (3200,16000), interpolation=cv2.INTER_LINEAR)
z=B
cv2.imwrite(os.path.join(path_img,'grayscale_left.jpg'), resized_image)
x = np.arange(resized_image.shape[1])
y = np.arange(resized_image.shape[0])
x, y = np.meshgrid(x, y)
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z)

# Set initial viewing angle
ax.view_init(elev=30, azim=30)
plt.show()