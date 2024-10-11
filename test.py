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
matplotlib.use('TkAgg')
df = pd.read_csv("/media/mp274748/Transcend/data/Glue_Files/241007_101305/mass_infos.csv")
def cmap_ot(x):
    if x == 450:
        return "y"
    elif x == 400:
        return "g"
    elif x==500:
        return "r"
    else:
        return "b"

subdf = df[df["chip_type"]=="NTD"]
#fit_error,dm,radius
plt.scatter(subdf["dm"],subdf["radius"],c=subdf["opentime"].apply(cmap_ot),marker = "v")
subdf = df[df["chip_type"]=="heater"]
plt.scatter(subdf["dm"],subdf["radius"],c=subdf["opentime"].apply(cmap_ot),marker = "P")
plt.show()
