import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RectangleSelector
import inspect
import json
from PIL import Image
import pickle
import io
import matplotlib.gridspec as gridspec
def copy_figure(fig):
    buf = io.BytesIO()
    pickle.dump(fig, buf)
    buf.seek(0)
    fig2 = pickle.load(buf)
    return fig2
class bigger_axis_on_clic:
    def __init__(self,fig):
        self.fig=fig
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
    def on_click(self,event):
        if not event.inaxes: return
        inx = list(self.fig.axes).index(event.inaxes)
        fig2 = copy_figure(self.fig)
        for i, ax in enumerate(fig2.axes):
            if i != inx:
                fig2.delaxes(ax)
            else:
                axes=ax
        gs = gridspec.GridSpec(1, 1)
        axes.set_position(gs[0].get_position(fig2))
        axes.set_subplotspec(gs[0])  # only necessary if using tight_layout()
        fig2.show()

def get_files(im_path,start_string):
    for root, dirs, files in os.walk(im_path):
        for file in files:
        # Print files in the current directory
            if file.startswith(start_string):
                # Print or perform operations on the file
                file_path = os.path.join(root, file)
                return file_path
def get_res(res_path):
    for root, dirs, files in os.walk(res_path):
        # Print files in the current directory
        files = np.sort(files)
        res = os.path.join(root, files[-1])
        data = np.loadtxt(res, delimiter=',')
    return data
def plot_image(path, ax):
    try :
        img = np.asarray(Image.open(path))
    except FileNotFoundError:
        path = path[:-17] + str(int(path[-17:-15])+1) + path[-15:]
        img = np.asarray(Image.open(path))
    implot = ax.imshow(img, cmap='grey')
def plot_img(ax, line,path):
    x, y = line[0], line[1]
    r = line[2]
    Drawing_colored_circle = plt.Circle((x, y), r, fill=None, color='g', lw=2)
    ax.add_artist(Drawing_colored_circle)
    plot_image(path, ax)
    center_ntd_x, center_ntd_y = line[3], line[4]
    ax.plot([center_ntd_x],[center_ntd_y],marker="+",ms=10,markeredgewidth=1)
    ax.set_aspect(1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.invert_yaxis()


def plot_all_image(path,num_prog):
    im_path = path + r"\image\SD1_{:03d}".format(num_prog)
    res_path = path + r"\result\SD1_{:03d}".format(num_prog)
    data = get_res(res_path)
    num_im = len(data)
    num_rows = int(num_im ** 0.5)
    num_cols = (num_im + num_rows - 1) // num_rows
    fig, axs = plt.subplots(num_rows, num_cols)
    for i,line in enumerate(data):
        j,k = i//num_rows, i%num_rows
        start_string = "{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}_{:010d}".format(int(line[-6]), int(line[-5]),
                                                                          int(line[-4]), int(line[-3]),
                                                                          int(line[-2]), int(line[-1]),int(line[-7]))[:-1]
        file_path = get_files(im_path, start_string)
        plot_img(axs[k,j], line, file_path)
    return fig

import os
path = r"C:\GluingRobotData\Data_gluing\2024_02_06\192.168.200.2\SD2\cv-x"
fig = plot_all_image(path,7)
zoom = bigger_axis_on_clic(fig)
zoom.fig.canvas.mpl_connect('button_press_event', zoom.on_click)
plt.show()
