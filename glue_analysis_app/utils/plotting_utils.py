"""
Plotting utilities for glue analysis app.
"""
import cv2
import numpy as np

def draw_circles(image, cx, cy, radii, color=(255, 0, 0)):
    im = image.copy()
    for center_x, center_y, radius in zip(cx, cy, radii):
        cv2.circle(im, (center_x, center_y), int(radius), color, 2)
    return im
