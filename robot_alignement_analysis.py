import numpy as np
import matplotlib.pyplot as plt
file_path = r"C:\GluingRobotData\coord_correction\data_correction\192.168.200.2\SD2\cv-x\result\SD1_011\231206_160749.txt"
data = np.loadtxt(file_path, delimiter=',')
XY_goal_alignment = [-300,-370]
YX = np.array([np.mean(data[i::30, :2], axis=0) for i in range(30)])
YX_std = np.array([np.std(data[i::30, :2], axis=0) for i in range(30)])
plt.imshow((YX[:,1]-XY_goal_alignment[0]).reshape((6,5)), cmap='hot')
print(YX_std.T)
file_path = r"C:\GluingRobotData\coord_correction\data_correction\192.168.200.2\SD2\cv-x\result\SD1_011\231206_155901.txt"
data = np.loadtxt(file_path, delimiter=',')
XY_goal_alignment = [-300,-370]
YX = np.array([np.mean(data[i::30, :2], axis=0) for i in range(30)])
YX_std = np.array([np.std(data[i::30, :2], axis=0) for i in range(30)])
plt.imshow((YX[:,1]-XY_goal_alignment[0]).reshape((6,5)), cmap='hot')
print(YX_std.T)
