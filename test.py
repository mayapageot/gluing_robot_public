import cv2
import numpy as np
import pandas as pd
from utility import plots
import os
if __name__ == "__main__":
    dir_path = r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240503_105626\CAM1"
    path_py = dir_path + r"\analysis_2.csv"
    df = pd.read_csv(path_py)
    x = df["center_x"]
    y = df["center_y"]
    h = 200
    centered_dot = df.loc[(x<2390.0+h)&(x>2350.0-h)&(y>1680.0-h)&(y<1725.0+h)]
    radius = centered_dot["diameter"].mean()
    rms = centered_dot["diameter"].std()
    print(radius, rms)
    print(len(centered_dot["diameter"]))
    plots.slidded_bin_histogram(centered_dot["diameter"],wbin=1)
    plots.show()
