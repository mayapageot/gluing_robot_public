import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

file_path = "/media/mp274748/Transcend/data/Glue_Files/250506_101037/CAM1/250506_104502_0000000014.bmp"


# Load the saved image and display it
img = plt.imread(file_path)
plt.imshow(img)
plt.scatter(1370,800)
plt.axis('off')  # hide axes
plt.title('Loaded Image')
plt.show()