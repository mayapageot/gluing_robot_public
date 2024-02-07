import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

pxl_mm = 0.001243163

def plot_image(path, ax):
    try :
        img = np.asarray(Image.open(path))
    except FileNotFoundError:
        path = path[:-17] + str(int(path[-17:-15])+1) + path[-15:]
        img = np.asarray(Image.open(path))
    implot = ax.imshow(img, cmap='grey')
def plot(data,sel,ax,name=""):
    img_name = "{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}_{:010d}.bmp".format(int(data[sel, -6]), int(data[sel, -5]),
                                                                          int(data[sel,-4]), int(data[sel, -3]),
                                                                          int(data[sel, -2]), int(data[sel, -1]),
                                                                          int(data[sel,-7]))
    circle = plt.Circle((data[sel, 0], data[sel, 1]),
                        data[sel, 2])
    plot_image(path_pics + img_name, ax)
    x, y = data[sel, 0],data[sel, 1]
    r =  data[sel, 2]
    r_mm = pxl_mm*r
    color = "orangered" if data[sel, -8]==1 else 'lime'
    Drawing_colored_circle = plt.Circle((x,y), r, fill=None, color=color,lw=2)
    ax.add_artist(Drawing_colored_circle)

    added_pxl = 50
    ax.set_xlim(x-r-added_pxl,x+r+added_pxl)
    ax.set_ylim(y - r - added_pxl, y + r + added_pxl)
    ax.set_aspect( 1 )
    ax.set_title("{}\nVolume: {:.2f}nL Radius: {:.0f}$\mu$m".format(name,2/3*np.pi*r_mm**3*1e3,r_mm*1e3))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.invert_yaxis()
def plot_5dots_picture(data,first_pic_index=0):
    names = ["center", "top left", "top right", "btm right", "btm left"]
    for i in range(5):
        j = i // 3
        k = i % 3
        plot(data, i + first_pic_index, axs[j, k], names[i])
    plot(data, 4 + first_pic_index, axs[1, 2])
    axs[1, 2].set_ylim(0, 4092)
    axs[1, 2].set_xlim(0, 5104)
    axs[1, 2].invert_yaxis()
    axs[1, 2].set_title("global picture")
    plt.show()
if __name__ == "__main__":
    fig, axs = plt.subplots(2,3)
    fig.set_size_inches((12, 7))
    path_result = r"C:\GluingRobotData\Data_gluing\23_12_19\192.168.200.2\SD2\cv-x\result\SD1_003\231219_101149.txt"
    path_pics = r"C:/GluingRobotData/Data_gluing/23_12_19/192.168.200.2/SD2/cv-x/image/SD1_003/231219_101359/CAM1/"
    data = np.loadtxt(path_result, delimiter=',')
    plot_5dots_picture(data,first_pic_index=0)


