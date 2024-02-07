import numpy as np
import pandas as pd
path1 = r"C:\GluingRobotData\coord_correction\commends\1_dot_gluing_selected.xlsx"
path2 = r"C:\GluingRobotData\coord_correction\commends\1_dot_gluing_selected_up.xlsx"
def get_commend(commend_file_path):
    df = pd.read_excel(commend_file_path)
    commend = (df.iloc[[1,2]]).astype(float).values.T
    return commend
cmd_good = get_commend(path2)
cmd_new = get_commend(path1)
d = (cmd_new-cmd_good)[::3]
dXY_camera_glue = np.loadtxt(r"C:\GluingRobotData\coord_correction\dXY_camera_glue.txt")
dXY_camera_glue[:15] -= d
print(d)
np.savetxt(r"C:\GluingRobotData\coord_correction\dXY_camera_glue.txt",dXY_camera_glue)
