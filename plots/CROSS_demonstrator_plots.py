import pandas as pd
import os
from utility.plots import bigger_plot
bigger_plot()
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import pandas as pd
import matplotlib.pyplot as plt
pixel_to_um = 1.24
import matplotlib
def mass_plot():
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

def Initial_vs_late_area():
    df_1 = pd.read_csv(os.path.join("/media/mp274748/Transcend/data/Glue_Files/241128_112132/CAM1","data.csv"),index_col = 1)
    df_2 = pd.read_csv(os.path.join("/media/mp274748/Transcend/data/Glue_Files/241211_140213/CAM1", "data.csv"),
                     index_col = 1)
    df = pd.concat((df_1,df_2))
    plt.plot(df.groupby("support_name").min("radius")["area"].values*1e-6,
             df.groupby("support_name").max("radius")["area"].values*1e-6,
             ls="",marker=".",ms=10)
    font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }
    offset = 10
    for x,y,t in zip(df.groupby("support_name").min("radius")["area"].values*1e-6,
             df.groupby("support_name").max("radius")["area"].values*1e-6,
             df.groupby("support_name").max("radius")["area"].index.array):

        plt.annotate(t,(x,y),xytext=(offset,offset),textcoords='offset pixels', fontsize=16,
                     bbox=dict(facecolor='white',edgecolor='black',boxstyle='round',alpha=0.8))
    plt.xlabel("initial radius [pxl]")
    plt.ylabel("late radius [pxl]")
    tick_intervals = 0.01
    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(tick_intervals*2))
    ax.xaxis.set_major_formatter('{x:.2f}')
    ax.xaxis.set_minor_locator(MultipleLocator(tick_intervals))
    ax.yaxis.set_major_locator(MultipleLocator(tick_intervals*2))
    ax.yaxis.set_major_formatter('{x:.2f}')
    ax.yaxis.set_minor_locator(MultipleLocator(tick_intervals))
    ax.grid(True, which = 'major')
    ax.grid(True, which = 'minor',linestyle = (0,(5,10)) )
    plt.show()
def Initial_vs_late_radius(path = "/media/mp274748/Transcend/data/Glue_Files/241128_112132/CAM1",ax=None,name="28th November"):
    df = pd.read_csv(os.path.join(path,"data.csv"),index_col = 1)
    ax = plt.subplots()[1] if ax is None else ax
    lines,= ax.plot(df.groupby("support_name").min("radius")["radius"].values,
             df.groupby("support_name").max("radius")["radius"].values,
             ls="",marker=".",ms=10,label=name)
    font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }
    offset = 10
    for x,y,t in zip(df.groupby("support_name").min("radius")["radius"].values,
             df.groupby("support_name").max("radius")["radius"].values,
             df.groupby("support_name").max("radius")["radius"].index.array):

        ax.annotate(t,(x,y),xytext=(offset,offset),textcoords='offset pixels', fontsize=16,bbox=dict(
        facecolor='white',  # Background color
        edgecolor=lines.get_c(),  # Border color
        boxstyle='round',   # Rounded box style
        alpha=0.8           # Transparency of the box
    ))
    ax.set_xlabel("initial radius [pxl]")
    ax.set_ylabel("late radius [pxl]")
    tick_intervals = 5
    ax.xaxis.set_major_locator(MultipleLocator(tick_intervals*2))
    ax.xaxis.set_major_formatter('{x:.0f}')
    ax.xaxis.set_minor_locator(MultipleLocator(tick_intervals))
    ax.yaxis.set_major_locator(MultipleLocator(tick_intervals*2))
    ax.yaxis.set_major_formatter('{x:.0f}')
    ax.yaxis.set_minor_locator(MultipleLocator(tick_intervals))
    ax.grid(True, which = 'major')
    ax.grid(True, which = 'minor',linestyle = (0,(5,10)))
    return ax
ax = Initial_vs_late_radius("/media/mp274748/Transcend/data/Glue_Files/241211_140213/CAM1",name = "11th December")
#Initial_vs_late_radius("/media/mp274748/Transcend/data/Glue_Files/241211_140213/CAM1",ax,name = "11th December")
plt.legend()
plt.show()