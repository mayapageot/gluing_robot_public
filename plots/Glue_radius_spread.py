import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
#path = r"C:\GluingRobotData\Data_gluing\23_12_14\192.168.200.2\SD2\cv-x\result\SD1_007\231214_143555.txt"
#path = input("path")
path = r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\result\SD1_003\240403_160638.txt"

data = np.loadtxt(path, delimiter=',')
data = data[30:]
radius = data[:,2]
mask = (radius < 300 ) & (radius>220)
radius = radius[mask]
wbin =1
bins = np.arange(radius.min(),radius.max(),wbin)
hist,bins = np.histogram(radius,bins)
bins_c = (bins[:-1]+bins[1:])/2
plt.plot(bins_c, hist,ds = 'steps-mid',linewidth=.5)
print(len(data[np.logical_not(mask),2]))
print(np.mean(radius), np.std(radius))

print(np.mean(radius)*1.2, np.std(radius)*1.2)

plt.show()