import cv2
import numpy as np
import glob
import os
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
import os
conf_dict = {'2':80,'3':70,'4':80,'5':25,'6':60,'7':80,'12':80}
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scipy.interpolate import griddata
df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/240607_104955/CAM1/analysis_2.csv")
df = df[df["diameter"] < 400]
df_diam_correction = df[(df["num"] < 319) & (df["num"] > 218)]
def interpo_function(x,y):
    return griddata(df_diam_correction.loc[:, ["center_x", "center_y"]], df_diam_correction["diameter"] / df_diam_correction["diameter"].max(), ([x], [y]))[0]


def correct_diameter(center, diameter ):
    factor = interpo_function(center[0],center[1])
    return diameter* factor if factor is not None else 0.

def find_pos_pic(df):
    #delta_pos = {"position":["br","bl","m","tr","tl"],"x":[500,-500,0,500,-500],"y":[500,500,0,-500,-500]}
    #central_coo = [2367.0,1726.0]
    df["distance_center"] = (df["center_x"]-2367.0)**2 + (df["center_y"] - 1726.0)**2
    pos_center = df.groupby("filename").apply(lambda x : x.loc[x["distance_center"].idxmin(),"position"],include_groups=False)
    df["pos_center_dot"] = pos_center[df["filename"]].values
    df = df.drop("distance_center", axis = 'columns')
    return df


def load_temp():
    templates = {}
    for i in range(1,13):
        template_path = r"C:\GluingRobotData\coord_correction\template_numbers\{}.bmp".format(i)  # Replace with the path to your template images
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        templates[str(i)] = template
    return templates
def detect_numbers(image_path, templates):
    templates = load_temp
    # Read the image
    image = cv2.imread(image_path)[1600:3200, :1200]
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Define a dictionary to store the results for each template
    results = {}

    # Iterate over each template
    for digit, template in templates.items():
        # Apply template matching
        result = cv2.matchTemplate(image_gray, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8  # Adjust threshold as needed
        loc = np.where(result >= threshold)

        # Store the locations where the template is found
        results[digit] = loc
        if len(loc[0]>0):
            return digit
    return 0

def filter(im,thr=80):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur to reduce noise

    blurred = cv2.GaussianBlur(gray, (9,9), 0) #(11, 11)
    #Imshow(median)
    # Threshold the image to create a binary image
    mask = cv2.inRange(blurred, 0, thr)
    n = 18
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n,n))
    median = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return median

def filter_heater(image,thr=100):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    n = 71
    blur = cv2.GaussianBlur(gray, (n, n), 0)
    ret3, th3 = cv2.threshold(blur, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3
def Imshow(image):
    screen_res = 1280, 720  # Adjust these values according to your screen resolution
    scale_width = screen_res[0] / image.shape[1]
    scale_height = screen_res[1] / image.shape[0]
    scale = min(scale_width, scale_height)
    window_width = int(image.shape[1] * scale)
    window_height = int(image.shape[0] * scale)
    x = (screen_res[0] - window_width) // 2
    y = (screen_res[1] - window_height) // 2

    # Move window to the center of the screen

    cv2.namedWindow("Result", cv2.WINDOW_NORMAL)  # Create resizable window
    cv2.resizeWindow("Result", window_width, window_height)
    # Display the result
    cv2.imshow("Result", image)
    cv2.moveWindow("Result", x, y)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

rectangle = [656,2290, 1300,2900]
def get_glue_dot(image,thr=60):
    im = image

    mask = filter(im,thr) #for ntd : 50
    Imshow(mask)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(image, contours, -1, (0, 255, 0), 3)
    ellipse_list = []
    center_list = []
    diameter_list = []
    for cnt in contours:
       try :
           ellipse = cv2.fitEllipse(cnt)
           if np.abs(ellipse[1][0]-ellipse[1][1])<100 and ellipse[1][0]>300:
               ellipse_list.append(ellipse)
               M = cv2.moments(cnt)
               center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
               area = cv2.contourArea(cnt)
               equi_diameter = np.sqrt(4 * area / np.pi) / 2
               diameter_list.append(equi_diameter)
               center_list.append(center)

       except:
           pass
    """
    if len(center_list)>0:
        plot_image_with_circle(image, center_list, diameter_list)"""
    if len(center_list)!=5:
        pom = input("+ or -")
        try:
            thr = int(pom)
            return get_glue_dot(image,thr)
        except ValueError:
            pass


    return center_list,diameter_list


def plot_image_with_ellipse(image,ellipse_list):
   for ellipse in ellipse_list:
       cv2.ellipse(image,ellipse,(255,0,0),2)
   Imshow(image)




def plot_image_with_circle(image_with_keypoints,center_list,diameter_list):
   # Draw contours on the original image
   for center,dimeter in zip(center_list,diameter_list):
       cv2.circle(image_with_keypoints,center,int(dimeter),(0, 0, 255) ,10)
       font = cv2.FONT_HERSHEY_SIMPLEX
       text = f'Radius: {int(dimeter)}'
       text_size = cv2.getTextSize(text, font, 1, 2)[0]
       text_position = (center[0] - text_size[0] // 2, center[1] + int(dimeter) + text_size[1] + 20)
       cv2.putText(image_with_keypoints, text, text_position, font, 1, (0, 255, 0), 2, cv2.LINE_AA)

   # Resize the image to fit the screen
   screen_res = 1280, 720  # Adjust these values according to your screen resolution
   scale_width = screen_res[0] / image_with_keypoints.shape[1]
   scale_height = screen_res[1] / image_with_keypoints.shape[0]
   scale = min(scale_width, scale_height)
   window_width = int(image_with_keypoints.shape[1] * scale)
   window_height = int(image_with_keypoints.shape[0] * scale)
   # Output positions and diameters of detected glue dots
   # Display the result
   try :
    cv2.destroyWindow('Detected Glue Dots')
   except:
       pass
   cv2.namedWindow('Detected Glue Dots', cv2.WINDOW_NORMAL)  # Create resizable window
   cv2.resizeWindow('Detected Glue Dots', window_width, window_height)
   cv2.imshow('Detected Glue Dots', image_with_keypoints)
   cv2.waitKey(0)
   #cv2.destroyAllWindows()

def get_num(image_path):
    image = cv2.imread(image_path)[1800:3000, 200:1000]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    test = cv2.bilateralFilter(gray,9,75,75)
    data = pytesseract.image_to_data(
            test, config='--psm 13 --oem 3 -c tessedit_char_whitelist=0123456789',output_type='dict')
    txt = data['text']
    if txt[-1] in conf_dict and conf_dict[txt[-1]]< data['conf'][-1] :
        print(txt[-1])
        '''n_boxes = len(data['level'])
        for i in range(n_boxes):
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            print(data['left'][i], data['top'][i], data['width'][i], data['height'][i])'''


#dir_path= r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240404_122817\CAM1"
#dirs = os.listdir(dir_path)

def get_info_dir(dir_path,df=None):
   if df is None:
       df = pd.DataFrame({'filename':[],'center_x':[],'center_y':[],'diameter':[],'module':[]})
   dirs = os.listdir(dir_path)
   module_prec = 0
   for file in dirs:
       _, extension = os.path.splitext(file)
       if extension.lower() ==".bmp":
           path = os.path.join(dir_path,file)
           print(path)
           im = cv2.imread(path)
           center_list, diameter_list = get_glue_dot(im)
           """module = detect_numbers(path, templates)
           if module==0:
               module = module_prec"""
           module = 0
           #plot_image_with_circle(im, center_list, diameter_list)
           for center, diameter in zip(center_list, diameter_list):
               diameter_corrected = correct_diameter( center, diameter )
               df = pd.concat([df, pd.DataFrame(
                   {'filename': [file], 'center_x': [center[0]], 'center_y': [center[1]], 'diameter': [diameter],'module':[module]})])
   return df



def get_mod_from_cam(df_py=None,df_cam=None,path_py=None,path_cam=None):
    if df_py is None:
        df_py = pd.read_csv(path_py)
    if df_cam is None:
        df_cam = pd.read_csv(path_cam, header = None)
    df_py = df_py.sort_values("filename")
    df = df_cam.iloc[:, 3:16] == 0
    last_true_positions = df.apply(lambda row: row[row].index[0] - 2 if any(row) else 0, axis = 1)
    previous = 0
    for line in range(len(last_true_positions)):
        if last_true_positions[line] == 0:
            last_true_positions[line] = previous
        previous = last_true_positions[line]
    df_cam["module"] = last_true_positions
    mod = []
    for i in range(len(df_py)):
        print(df_cam.loc[df_cam.loc[:, 17] == int(df_py.loc[i, "filename"][-14:-4]), "module"].values[0])
        mod.append(df_cam.loc[df_cam.loc[:, 17] == int(df_py.loc[i, "filename"][-14:-4]), "module"].values[0])
    df_py["module"] = mod
    print(df_py)
    return df_py


def get_info_zip(zip_file_path, df=None):
   if df is None:
       df = pd.DataFrame({'filename':[],'center_x':[],'center_y':[],'diameter':[]})
   with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
       # Check if the file exists in the ZIP archive
       for file_to_read in zip_ref.namelist():
           if '.bmp' in file_to_read:
               # Open the file within the ZIP archive
               with zip_ref.open(file_to_read) as image_file:
                   # Read the contents of the file
                   image_bytes = image_file.read()


                   # Convert bytes data to a NumPy array
                   image_nparray = np.frombuffer(image_bytes, np.uint8)


                   # Decode the image from the NumPy array
                   image = cv2.imdecode(image_nparray, cv2.IMREAD_COLOR)
                   center_list, diameter_list = get_glue_dot(image)
                   for center, diameter in zip(center_list,diameter_list):
                       print(file_to_read,center[0], center[1], diameter )
                       df = pd.concat([df, pd.DataFrame({'filename':[file_to_read],'center_x':[center[0]],'center_y':[center[1]],'diameter':[diameter]})])
                   #plot_image_with_circle(image, center_list, diameter_list)
   return df




def multiple_zip(dir_path,name):
   dirs = os.listdir(dir_path)
   df = pd.DataFrame({'filename': [], 'center_x': [], 'center_y': [], 'diameter': []})
   for filename in dirs:
       if name in filename:
           zip_file_path = os.path.join(dir_path, filename)
           df =get_info_zip(zip_file_path, df=df)
   return df



def hhmmss_to_seconds(hhmmss):
   hours = int(hhmmss[:2])
   minutes = int(hhmmss[2:4])
   seconds = int(hhmmss[4:])
   total_seconds = hours * 3600 + minutes * 60 + seconds
   return total_seconds



def post_analysis_dir(dir_path = r'C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240403_131011\CAM1'):
    save_path = os.path.join(dir_path,'analysis_2.csv')
    df = get_info_dir(dir_path)
    df.to_csv(save_path,index = False)


class NewFileHandler(FileSystemEventHandler):
    def __init__(self,df,path):
        super().__init__()
        self.df = df
        self.path = path
    def on_created(self, event):
        # This function is called when a file is created
        if not event.is_directory:  # Check if the event is for a file
            path = event.src_path  # Print the path of the new file
            print(path)
            image = cv2.imread(path)
            center_list, diameter_list = get_glue_dot(image)
            for center, diameter in zip(center_list, diameter_list):
                self.df = pd.concat([self.df, pd.DataFrame(
                    {'filename': [path], 'center_x': [center[0]], 'center_y': [center[1]], 'diameter': [diameter]})])
            print(center_list)
            print(diameter_list)
            plot_image_with_circle(image, center_list, diameter_list)
            self.df.to_csv(self.path,columns=None)

def continuous_analysis(dir_path,save_name = r'\analysis_log.csv'):
    save_path = dir_path + save_name
    try :
        df = pd.read_csv(save_path)
    except :
        df = pd.DataFrame({'filename': [], 'center_x': [], 'center_y': [], 'diameter': []})
    event_handler = NewFileHandler(df,save_path)
    observer = Observer()
    observer.schedule(event_handler, dir_path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def sort_key(row):
    x, y = row['center_x'], row['center_y']
    thr = 200
    if x < -thr and y > thr:
        return "tl"  # Top left
    elif x > thr and y > thr:
        return "tr" # Top right
    elif x > thr and y < -thr:
        return "br"  # Bottom right
    elif x < -thr and y < -thr:
        return "bl"  # Bottom left
    else :
        return "m"

def get_dot_pos_from(df):
    df_xy = df.loc[:, ("center_x", "center_y")]
    df_sort = df_xy - df_xy.mean()
    index_sort = df_sort.apply(sort_key, axis = 1)
    return index_sort

def get_glue_dot_pos(df_py=None,path_py=None):
    if df_py is None:
        df_py = pd.read_csv(path_py)
    df = df_py.loc[(df_py["diameter"]-270).abs()<100]
    group = df.groupby("filename").apply(get_dot_pos_from,include_groups=False).to_numpy()
    df['position']=group
    print(df)
    return df

def correct_pos_after(df):
    df["corrected_diameter"] = df.apply(lambda x: correct_diameter((x["center_x"], x["center_y"]), x["diameter"]),
                                        axis = 1)
    #df = find_pos_pic(df)
    return df
if __name__=="__main__":
   """dir_path = "/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T212046Z-001/"
   #post_analysis_dir(dir_path)
   path_py = dir_path + "analysis_2.csv"
   path_cam = dir_path + glob.glob("*.txt",root_dir = "/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T212046Z-001/")[0]
   df = get_mod_from_cam(df_py = None, df_cam = None, path_py = path_py, path_cam = path_cam)
   df = get_glue_dot_pos(df)
   df.sort_values("filename").to_csv(path_py,index = False)
   #continuous_analysis(dir_path)
   #df = pd.read_csv(save_path)"""
   """post_analysis_dir("/local/home/mp274748/Documents/data/Glue/240716_heaters")
   df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/240716_heaters/analysis_2.csv")
   df = get_glue_dot_pos(df)
   df = correct_pos_after(df)

   df.to_csv("/local/home/mp274748/Documents/data/Glue/240716_heaters/analysis_2.csv",index = None)"""
   df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/test.csv")
   df["filename"]= df["filename"].apply(lambda x : x.split("/")[-1])


   group = df.groupby("filename").apply(get_dot_pos_from, include_groups = False).to_numpy()
   df['position'] = group

   df = correct_pos_after(df)
   df.to_csv("/local/home/mp274748/Documents/data/Glue/240716_heaters/test_c.csv", index = None)



