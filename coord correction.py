import numpy as np
import pandas as pd
import os
from utility.file_management import save_xlsx

pixel_to_mm = 1.24e-3
XY_goal_gluing = [0., 0.]
XY_goal_alignment = [-300,-370]

array_matrix_module = np.array([1,2,3,4,5,6,12,11,10,9,8,7,13,14,15,16,17,18,24,23,22,21,20,19,25,26,27,28,29,30])

dXY_camera_glue = np.loadtxt(r"C:\GluingRobotData\coord_correction\dXY_camera_glue.txt")

dXY_camera_uv = (87.699,-52.838)
Z_glue = 186.4
Z_camera = 180.423
Z_profilometer = 179.188
five_dot_matrix = [[0.,0.,0.],[-0.65,-0.65,0],[-0.65,0.65,0],[0.65,0.65,0],[0.65,-0.65,0]]
one_dot_matrix = [[0.,0.,0.]]
matrix_dict = {1:one_dot_matrix,5:five_dot_matrix}

def move_to_glue_coordonnate(XY):
    return XY + dXY_camera_glue

def move_to_uv_coordonate(XY):
    return XY + dXY_camera_uv

def move_to_profil_coordonnate(XY):
    return XY - (62.823,9.794)

def get_glue_coordonate(XY_glue_center,XY_camera,dots_number=5):
    dot_matrix = matrix_dict[dots_number]
    num_rows, num_columns = XY_glue_center.shape
    n_column = dots_number*3
    xy_glue = np.empty((num_rows*n_column, 9))
    xy_glue.fill(np.NaN)
    XYZ_glue_center = np.concatenate((XY_glue_center, Z_glue*np.ones((num_rows,1))),axis=1)
    XYZ_camera = np.concatenate((XY_camera, Z_camera*np.ones((num_rows,1))),axis=1)
    for i in range(dots_number):
        xy_glue[2*i::n_column, :3] = XYZ_glue_center + dot_matrix[i]
        xy_glue[2 * i::n_column, 8] = 5
        xy_glue[2 * i + 1::n_column, :3] = XYZ_glue_center + dot_matrix[i]
        xy_glue[2*dots_number+i::n_column, :3] = XYZ_camera + dot_matrix[i]
        xy_glue[2*dots_number+i::n_column, 8] = 1
    return xy_glue

def get_header(dots_number):
    header = ['Wait Start Point', 'Point Dispense']*dots_number + ['Wait Start Point']*dots_number
    return header

def get_commend(commend_file_path):
    df = pd.read_excel(commend_file_path,header=None)
    commend = (df.values).T
    return commend[:,1:3]


def get_XY_camera(file_path):
    data = np.loadtxt(file_path, delimiter=',')
    YX=data[:,:2]
    XY = YX[:,::-1]
    return XY


def get_XY_camera_mean(file_path):
    data = np.loadtxt(file_path, delimiter=',')
    YX = np.array([np.mean(data[i::30, :2], axis=0) for i in range(30)])
    XY = YX[:, ::-1]
    return XY


def get_new_commend(XY, commend, commend_file_path, save_name ='/corrected_commend.xlsx'):
    dXY_commend_camera = -(XY_goal_alignment-XY)*pixel_to_mm
    new_commend = commend + dXY_commend_camera
    save_xlsx(new_commend.T, os.path.dirname(commend_file_path)+save_name)
    return os.path.dirname(commend_file_path)+save_name


def correct_commend(commend_file_path,camera_file_path,save_name ='/corrected_commend.xlsx'):
    XY = get_XY_camera_mean(camera_file_path)
    commend = get_commend(commend_file_path)
    print(commend)
    save_path = get_new_commend(XY, commend, commend_file_path, save_name)
    return save_path


def get_XY_glue_5spots_selected_module(commend_alinement_path, gluing_module = np.arange(30) ,dots_number=5, file_name='_dot_gluing_selected.xlsx'):
    position_module = array_matrix_module[np.array(gluing_module) - 1] - 1
    XY_camera_central = get_commend(commend_alinement_path)
    XY_glue_center = move_to_glue_coordonnate(XY_camera_central)
    XY_glue_5spots_selected_module = get_glue_coordonate(XY_glue_center[position_module],XY_camera_central[position_module],dots_number=dots_number).T
    head = get_header(dots_number)* len(gluing_module)
    save_xlsx(XY_glue_5spots_selected_module, os.path.dirname(commend_file_path) + "/{}".format(dots_number)+file_name,header=head)


def scan_profile_modules(commend_alinement_path, gluing_module = np.arange(30),file_name='_scan_profile_selected.xlsx'):
    position_module = array_matrix_module[np.array(gluing_module) - 1] - 1
    XY_camera_central = get_commend(commend_alinement_path)
    XY_profil_top_left = move_to_profil_coordonnate(XY_camera_central)[gluing_module]
    XY_profil_bottom_left = XY_profil_top_left + (37.385,0.)
    XY_profil_top_right =  XY_profil_top_left + (0., 14.27)
    XY_profil_bottom_right = XY_profil_top_left + (37.385, 14.27)
    xy_profil = np.empty((4 * len(gluing_module), 9))
    xy_profil.fill(np.NaN)
    xy_profil[::4,:2] = XY_profil_top_left
    xy_profil[1::4,:2] = XY_profil_bottom_left
    xy_profil[2::4,:2] = XY_profil_top_right
    xy_profil[3::4,:2] = XY_profil_bottom_right
    xy_profil[::2, 8] = 3
    xy_profil[::2, 3] = 10.
    xy_profil[:, 2] = Z_profilometer
    head = ["CP Start Point","CP End Point"]*2*len(gluing_module)
    save_xlsx(xy_profil.T,
              os.path.dirname(commend_file_path) + "/" + file_name, header=head)


if __name__=='__main__':
    camera_file_path=r"C:\GluingRobotData\Data_gluing\2024_02_06\192.168.200.2\SD2\cv-x\result\SD1_001\240206_102537.txt"
    commend_file_path= r"C:\GluingRobotData\coord_correction\commends\commend.xlsx"
    new_commend_file_path = correct_commend(commend_file_path, camera_file_path, save_name='/corrected_commend.xlsx')
    get_XY_glue_5spots_selected_module(new_commend_file_path, gluing_module=np.arange(1,16),dots_number=5, file_name='_dot_gluing_selected.xlsx')
    scan_profile_modules(new_commend_file_path)
    """modules_to_glue = [22]
    XY = get_XY_camera_mean(file_path)
    commend = get_commend(commend_file_path)
    get_new_commend(XY, commend, commend_file_path, "/corrected_commend.xlsx")
    get_uv_pos(XY, commend, commend_file_path, gluing_module=[i for i in range(19,25)],filename='uv_19_to_24.xlsx')"""

#np.arange(7,25,1)






