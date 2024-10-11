import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
from scipy.spatial import KDTree

# Define the curve points (example points)
# Replace these with your actual curve points
curve_x = np.array([0, 1, 2, 3, 4, 5])
curve_y = np.array([0, 1, 0, 1, 0, 1])

# Define the points to test (example points)
# Replace these with your actual test points
test_points = np.random.random((10000,2))
from scipy.interpolate import UnivariateSpline
from scipy.spatial import KDTree
def get_close_point(curve,test_points,threshold = 0.5)
# Create spline interpolation function for the curve
    spline = UnivariateSpline(curve[:,0], curve[:,1], k=3, s=0)

    # Define new x values to interpolate (sample points on the curve)
    x_curve = np.linspace(curve_x.min(), curve_x.max(), 100)  # Generate 100 points along the x-axis
    y_curve = spline(x_curve)

    # Create a KD-Tree for fast nearest-neighbor search
    curve_points = np.vstack((x_curve, y_curve)).T
    tree = KDTree(curve_points)

    # Query the KD-Tree to find the closest curve points to the test points
    distances, indices = tree.query(test_points, k=1)  # k=1 for the closest point

    # Define a distance threshold

    close_points_indices = distances.flatten() <= threshold
    close_points = test_points[close_points_indices]
    return close_points

# Plotting
fig, ax = plt.subplots(figsize=(8, 6))

# Plot the curve
ax.plot(x_curve, y_curve, 'b-', label='Curve')

# Plot the test points
ax.plot(test_points[:, 0], test_points[:, 1], 'go', label='Test Points')

# Plot the close points
if len(close_points) > 0:
    ax.plot(close_points[:, 0], close_points[:, 1], 'ro', label='Close Points')

plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.title('Curve and Close Points')
plt.grid(True)
plt.show()

print(f"Points close to the curve (within threshold {threshold}):\n{close_points}")


"""import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from matplotlib.patches import Circle
import scipy
import cv2
from matplotlib.patheffects import withStroke
royal_blue = [0, 20/256, 82/256]
rectangle = [656,2290, 1300,2900]
import matplotlib
matplotlib.use('tkagg')
def filter_heater(image,thr=100):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    n = 71
    blur = cv2.GaussianBlur(gray, (n, n), 0)
    ret3, th3 = cv2.threshold(blur, thr, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3
def filter(im,thr=80):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    # Threshold the image to create a binary image
    mask = cv2.inRange(blurred, 0, thr)
    return mask
def get_glue_dot(image,thr = 50):
   mask = filter(image,thr = thr)
   #Imshow(mask)
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
   return center_list,diameter_list,mask
initial_td2 = 14.17

def drawCircle(ax,xy,r):
    c = Circle(xy, radius = r, clip_on = False, zorder = 10, linewidth = 2.5,
               edgecolor = royal_blue + [0.6], facecolor = 'none',
               path_effects = [withStroke(linewidth = 7, foreground = 'white')])

    ax.add_artist(c)
    return c

def plot_image_with_c(ax,Im,center_list,diameter_list):
    image  = ax.imshow(Im)
    circles = []
    for xy,r in zip(center_list,diameter_list):
        circles.append(drawCircle(ax,xy,r))
    return circles,image
def update_circles(circles, center_list,diameter_list):
    if len(circles)>len(diameter_list):
        for i in range(len(circles)-len(center_list)):
            center_list.append(0)
            diameter_list.append((0,0))
    elif len(circles)<len(diameter_list):
        for i in range(len(diameter_list) - len(circles)):
            c = Circle((0,0), radius = 0., clip_on = False, zorder = 10, linewidth = 2.5,
               edgecolor = royal_blue + [0.6], facecolor = 'none',
               path_effects = [withStroke(linewidth = 7, foreground = 'white')])
            circles.append(c)
            ax.add_artist(c)

    for circle,xy,r in zip(circles,center_list,diameter_list):
        circle.set_center(xy)
        circle.set_radius(r)
        print(circle)

    return circles
fig, ax =plt.subplots()
plt.subplots_adjust(bottom=0.1)
Im = cv2.imread("/local/home/mp274748/Documents/data/Glue/240716_heaters/240716_112424_0000000040.bmp")
circles,image = plot_image_with_c(ax,Im,[(0.,0.)],[0.])
print(circles)
# Add sliders,r
axcolor = 'lightgoldenrodyellow'
ax_amp = plt.axes([0.25, 0.01, 0.65, 0.03], facecolor=axcolor)

s_amp = Slider(ax_amp, 'Amp', 0, 150, valinit=30)

# Function to update plot based on slider values
def update(val):
    global circles
    amp = s_amp.val

    center_list,diameter_list,mask = get_glue_dot(255-Im,thr=amp)
    print(diameter_list,center_list)
    if len(diameter_list)>0:
        circles = update_circles(circles, center_list, diameter_list)
        #print(circles)

    #mask = filter(255- Im, thr = amp)
    image.set_data(mask)
    fig.canvas.draw_idle()

# Attach sliders to update function
s_amp.on_changed(update)
update(1)
# Display the plot and sliders
plt.show()"""