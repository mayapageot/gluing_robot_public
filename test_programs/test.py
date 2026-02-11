import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import glob
import PIL
path = "/Users/av285030/Documents/CEA/Manuel_gluing_app/data/Pictures/analysis/2025-02-04.csv"
df = pd.read_csv(path)
df["path"] = df["image_file"].apply(lambda x: glob.glob(path[:-23]+"**/"+x,recursive=True)[0])
img = np.asarray(PIL.Image.open(df.loc[0,"path"]))
plt.imshow(img)
plt.show()