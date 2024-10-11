import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
x_c,y_c = 2241.0 , 1785.0
def get_central_dot(ds):
    d_center = np.sqrt((ds["center_x"]-x_c )**2+(ds["center_y"]-y_c)**2)
    return ds.loc[d_center.idxmin()]
def get_central_module(ds):
    ds_bis = ds.loc[ds["position"]=="m"]
    d_center = np.sqrt((ds_bis["center_x"]-x_c )**2+(ds_bis["center_y"]-y_c)**2)
    return ds_bis.loc[d_center.idxmin(),"filename"]
df = pd.read_csv(
    "/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T212046Z-001/analysis_2.csv")

central_dot = df.groupby("filename").apply(get_central_dot,include_groups=False)
filename_m_dots = df.groupby("module").apply(get_central_module,include_groups=False)
df = df.set_index('filename')
m_dots = df.loc[filename_m_dots]
central_dot = central_dot.set_index(["module","position"])
m_dots = m_dots.set_index(["module","position"])
print((m_dots-central_dot).groupby("position").mean())
print((m_dots-central_dot).groupby("position").std())