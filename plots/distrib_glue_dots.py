import matplotlib.pyplot as plt
from utility import plots
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
plots.bigger_plot()
pixel_to_um = 1.24
df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/240716_heaters/glue_std.csv")
print(df)
df = df.loc[(df["diameter"]<180)&(df["diameter"]>150)&(df["filename"].apply(lambda x:int(x[-10:-4]))>3)]

h = plots.slidded_bin_histogram(df["diameter"]*pixel_to_um,wbin=1.,x_range = [150*pixel_to_um,180*pixel_to_um],unit = "$\mu m$",linewidth=2)
h.ax.set_xlabel("radius in $\mu m$")
print(df["diameter"].mean()*pixel_to_um,(df["diameter"]*pixel_to_um).std())
print(len(df))
plots.show()