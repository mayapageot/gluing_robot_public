import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
pixel_to_um = 1.24
lims = [[3,14],[16,27],[29,40],[42,53]]
dir = "/media/mp274748/Transcend/data/Glue_Files/250206_110255/CAM1/"
df = pd.read_csv(os.path.join(dir,"data.csv"))
df = df.set_index("file")
df = df.sort_values("num")
colors = ["b","r","g","orange"]
for lim,c in zip(lims,colors):
    sub_df = df.loc[(df["num"]>=lim[0])&(df["num"]<=lim[1])].copy()
    t = (sub_df.index.str[7:13]).astype(int)
    sub_df.loc[:,"time"] = t- np.min(t)
    plt.plot(sub_df.loc[:, "time"], sub_df.loc[:, "area"] * pixel_to_um,ls="",marker=".",c=c)
    for index in sub_df.index:
        if sub_df.loc[index,"accum"]<0.8:
            col = "r"
        else:
            col = "b"
        plt.text(sub_df.loc[index,"time"] ,sub_df.loc[index,"area"]* pixel_to_um,str(sub_df.loc[index,"num"]),dict(size=10),c=col)

plt.show()

