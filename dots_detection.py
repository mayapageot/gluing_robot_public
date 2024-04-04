import cv2
import numpy as np
import os
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
#from python_files.utility.plots import slidded_bin_histogram,create_calibrated_ax, bigger_plot
import pytesseract
import os
# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\admin-local\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
conf_dict = {'2':80,'3':70,'4':80,'5':25,'6':60,'7':80,'12':80}
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
templates = {}
for i in range(1,13):
    template_path = r"C:\GluingRobotData\coord_correction\template_numbers\{}.bmp".format(i)  # Replace with the path to your template images
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    templates[str(i)] = template
def detect_numbers(image_path, templates):
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
def get_glue_dot(image):
   # Load the image
   # Convert the image to grayscale
   gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
   # Apply Gaussian blur to reduce noise
   blurred = cv2.GaussianBlur(gray, (11, 11), 0)
   # Threshold the image to create a binary image
   mask = cv2.inRange(blurred, 0, 100)
   # Find contours
   contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
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
   return center_list,diameter_list


def plot_image_with_ellipse(image_with_keypoints,ellipse_list):
   for ellipse in ellipse_list:
       cv2.ellipse(image_with_keypoints,ellipse,(255,0,0),2)


   # Resize the image to fit the screen
   screen_res = 1280, 720  # Adjust these values according to your screen resolution
   scale_width = screen_res[0] / image_with_keypoints.shape[1]
   scale_height = screen_res[1] / image_with_keypoints.shape[0]
   scale = min(scale_width, scale_height)
   window_width = int(image_with_keypoints.shape[1] * scale)
   window_height = int(image_with_keypoints.shape[0] * scale)
   # Output positions and diameters of detected glue dots
   # Display the result
   cv2.namedWindow('Detected Glue Dots', cv2.WINDOW_NORMAL)  # Create resizable window
   cv2.resizeWindow('Detected Glue Dots', window_width, window_height)
   cv2.imshow('Detected Glue Dots', image_with_keypoints)
   cv2.waitKey(0)
   cv2.destroyAllWindows()




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


dir_path= r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240404_122817\CAM1"
dirs = os.listdir(dir_path)

def get_info_dir(dir_path,df=None):
   if df is None:
       df = pd.DataFrame({'filename':[],'center_x':[],'center_y':[],'diameter':[],'module':[]})
   dirs = os.listdir(dir_path)
   module_prec = 0
   for file in dirs:
       _, extension = os.path.splitext(file)
       if extension.lower() ==".bmp":
           path = os.path.join(dir_path,file)
           im = cv2.imread(path)
           center_list, diameter_list = get_glue_dot(im)
           module = detect_numbers(path, templates)
           if module==0:
               module = module_prec
           #plot_image_with_circle(im, center_list, diameter_list)
           for center, diameter in zip(center_list, diameter_list):
               df = pd.concat([df, pd.DataFrame(
                   {'filename': [path], 'center_x': [center[0]], 'center_y': [center[1]], 'diameter': [diameter],'module':[module]})])
   return df
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


def glue_dots_analysis(df):
   data = df["diameter"].to_numpy()
   number = df["filename"].apply(lambda x : int(os.path.split(x)[1][-14:-4])).to_numpy()
   time = df["filename"].apply(lambda x : hhmmss_to_seconds(os.path.split(x)[1][7:13])/60-689-40).to_numpy()
   plt.scatter(time, data, s = 20)
   plt.xlabel("time in minutes")
   plt.ylabel("radius size in pixel")
   #plt.scatter(number,data,s=1)
   plt.show()
   """histo = slidded_bin_histogram(data[(time>37)&(time<45)&(data<250)&(data>200)], wbin = 1, n_min = 10, n_max = 1000)
   histo.ax.set_xlabel('radius of the dots in pxl')
   histo.ax.set_ylabel('count / pixel')
   calib = create_calibrated_ax(histo.ax, np.poly1d([0.001243163, 0]))
   calib.ax.set_xlabel('radius of the dots in mm')
   print(np.mean(data[(time>37)&(time<45)&(data<250)&(data>200)]), np.std(data[(time>37)&(time<45)&(data<250)&(data>200)]))
   print(np.mean(data[(time>37)&(time<45)&(data<250)&(data>200)])*0.001243163, np.std(data[(time>37)&(time<45)&(data<250)&(data>200)])*0.001243163)
   print(data[(time>37)&(time<45)&(data<250)&(data>200)])
   #print(np.mean(data) * (0.001243163) ** 3 * 1000, np.std(data) * (0.001243163) ** 3 * 1000)
   histo.histoline.set(linewidth = 1.)
   plt.show()"""

def post_analysis_dir(dir_path = r'C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240403_131011\CAM1'):
    save_path = dir_path + r'\analysis.csv'
    name = 'glueing_bdpt_2024_04_03'
    df = get_info_dir(dir_path)
    print(df)
    df.to_csv(save_path)
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


if __name__=="__main__":
   """path_test = '/local/home/mp274748/Documents/glue_robot/240322/240322_124905_0000000373.bmp'


   image = cv2.imread(path_test)
   center_list,diameter_list = get_glue_dot(path_test)
   plot_image_with_circle(path_test, center_list, diameter_list)"""
   save_path = r'C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240403_131011\CAM1\analysis.csv'
   dir_path = r'C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240404_122817\CAM1'
   post_analysis_dir(
       dir_path=r'C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240404_122817\CAM1')
   #continuous_analysis(dir_path)
   #df = pd.read_csv(save_path)
   """df = df[(df['diameter'] >= 200) & (df['diameter'] <= 300)]
   grouped = df.groupby('filename').mean()


   threshold = grouped['center_x'] + 600


   # Filtering for filenames with count greater than the threshold
   filtered_groups = grouped[grouped['center_x'] < threshold]


   # Getting the rows corresponding to these filenames
   result = df[df['filename'].isin(filtered_groups.index)]


   grouped = result.groupby('filename').count()
   filtered_groups = grouped[grouped['center_x'] == 5]
   result = result[result['filename'].isin(filtered_groups.index)]"""
   '''bigger_plot()
   df = df[(df['center_x'].apply(lambda x:np.abs(x-2300)) < 200 ) & (df['center_y'].apply(lambda x:np.abs(x-1760)) < 200 )]
   glue_dots_analysis(df)'''

