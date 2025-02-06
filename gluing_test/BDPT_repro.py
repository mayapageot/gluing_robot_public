import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from utility.plots import slidded_bin_histogram
path = "/local/home/mp274748/Documents/data/Glue/BDPT_v2/240403_142647.txt"
df = np.loadtxt(path,delimiter=",")
data = df[:,2]
pixel_to_um = 1.24
data = data[data>260]
V_um3 =  0.42*(data*pixel_to_um)**3
V_m3 =  0.42*(data*pixel_to_um)**3 * 1e-18
V_uL =  0.42*(data*pixel_to_um)**3 * 1e-15 *1e9 #uL
slidded_bin_histogram(V_uL,unit = "$\mu L$")

Mass=V_m3*( 997*1.1) #kg
Mass_ug = V_m3*( 997*1.1)  * 1e3 *1e6
print(np.std(Mass_ug),np.mean(Mass_ug))