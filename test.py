import cv2
import numpy as np
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
    #Imshow(image)
    """# Draw rectangles around the matched regions for each digit
    for digit, loc in results.items():
        print(digit,loc)
        template = templates[digit]
        h, w = template.shape  # Reverse the shape to match OpenCV convention
        for pt in zip(*loc[::-1]):
            cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)

    # Display the result
    """
import os
if __name__ == "__main__":
    image_path = r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240404_122817\CAM1\240404_123523_0000000010.bmp"  # Replace with the path to your image

    # Load all 12 templates for digits 0-9
    templates = {}
    for i in range(1,13):
        template_path = r"C:\GluingRobotData\coord_correction\template_numbers\{}.bmp".format(i)  # Replace with the path to your template images
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        print(template.shape)
        templates[str(i)] = template

    # Perform digit detection
    dir_path = r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_003\240404_122817\CAM1"
    dirs = os.listdir(dir_path)
    for file in dirs:
        _, extension = os.path.splitext(file)
        print(extension)
        '''path = os.path.join(dir_path, file)
        detect_numbers(path, templates)'''
