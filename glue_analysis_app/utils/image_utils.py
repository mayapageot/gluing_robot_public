"""
Image processing utilities for glue analysis app.
"""

import cv2
import numpy as np
from skimage.feature import canny
from skimage.morphology import dilation, disk
from skimage.measure import block_reduce, find_contours
from skimage.transform import hough_circle, hough_circle_peaks, hough_ellipse
from joblib import Parallel, delayed

def get_radius(x,y):
    return (x.max()-x.min()+y.max()-y.min())/2
def orientation_of_consecutive_vectors(x, y):
    # Calculate the cross product between consecutive vectors
    x_start = np.append(x[1:],x[0])
    y_start = np.append(y[1:],y[0])
    cross_products = x * y_start - y * x_start

    # Determine orientation based on the sign of the cross product
    orientation = cross_products > 0
    return orientation
def get_im_diff(path: str, path_ref: str, crop=None) -> np.ndarray:
    """
    Compute normalized absolute difference between an image and its reference.

    Args:
        path: Path to input image.
        path_ref: Path to reference image.
        crop: Optional [ymin, ymax, xmin, xmax] crop coordinates.

    Returns:
        Normalized difference image (uint8).
    """
    imag = cv2.imread(path)
    if crop is None:
        crop = [0, imag.shape[0], 0, imag.shape[1]]

    imag = imag[crop[0]: crop[1], crop[2]: crop[3]]
    im = np.array(cv2.cvtColor(imag, cv2.COLOR_BGR2GRAY), dtype=np.int32)

    im_ref = cv2.imread(path_ref)
    im_ref = np.array(cv2.cvtColor(im_ref, cv2.COLOR_BGR2GRAY), dtype=np.int32)
    im_ref = im_ref[crop[0]: crop[1], crop[2]: crop[3]]

    im_diff = np.abs(im_ref - im)
    return cv2.normalize(im_diff, None, 0, 255, cv2.NORM_MINMAX)


def get_edges(image: np.ndarray, high_threshold: float, downsample_factor: int = 10) -> np.ndarray:
    """
    Compute Canny edges and downsample.

    Args:
        image: Grayscale image.
        high_threshold: Upper threshold for Canny.
        downsample_factor: Factor for block reduce downsampling.

    Returns:
        Downsampled edge map.
    """
    edges = canny(image, sigma=5, low_threshold=5, high_threshold=high_threshold)
    downsampled = block_reduce(edges, (downsample_factor, downsample_factor), np.max)
    downsampled = dilation(downsampled, disk(1))
    return downsampled


def get_circle(edges: np.ndarray, r_guess: int = 400, n_dots: int = 1,
               pxl_range: int = 10, pxl_accuracy: int = 5):
    """
    Detect circles using Hough Circle Transform.

    Args:
        edges: Edge map.
        r_guess: Approximate radius.
        n_dots: Number of circles to detect.
        pxl_range: Radius search range.
        pxl_accuracy: Step size for radius search.

    Returns:
        Tuple (accums, cx, cy, radii).
    """
    hough_radii = np.arange(r_guess - pxl_range, r_guess + pxl_range, pxl_accuracy)
    hough_results = np.concatenate(
        Parallel(n_jobs=-1)(delayed(hough_circle)(edges, r) for r in hough_radii)
    )
    accums, cx, cy, radii = hough_circle_peaks(
        hough_results, hough_radii, total_num_peaks=n_dots,
        min_xdistance=r_guess, min_ydistance=r_guess
    )
    return accums, cx, cy, radii


def fit_ellipse(edges: np.ndarray, min_size: int = 100):
    """
    Fit ellipse to edge map using Hough Ellipse.

    Args:
        edges: Edge map.
        min_size: Minimum size of detected ellipse.

    Returns:
        Best ellipse parameters dict or None.
    """
    result = hough_ellipse(edges, accuracy=20, threshold=50,
                           min_size=min_size, max_size=None)
    if len(result) == 0:
        return None
    best = sorted(result, key=lambda x: -x[1])[0]
    return {
        "xc": best[3],
        "yc": best[4],
        "a": best[1],
        "b": best[2],
        "orientation": best[5]
    }


def detect_contours(image: np.ndarray, level: float = 0.5):
    """
    Detect contours in an image.

    Args:
        image: Input grayscale or edge map.
        level: Value at which to find contours (0–1 for normalized).

    Returns:
        List of contour arrays.
    """
    if image.max() > 1:
        norm_image = image / 255.0
    else:
        norm_image = image
    contours = find_contours(norm_image, level=level)
    return contours

def fill_gap(contour):
    x_contour, y_contour = contour[:, 1], contour[:, 0]
    orientation = orientation_of_consecutive_vectors(x_contour - x_contour.mean(), y_contour - y_contour.mean())
    np.min(x_contour[orientation])
    r1 = get_radius(x_contour[orientation], y_contour[orientation])
    r2 = get_radius(x_contour[~orientation], y_contour[~orientation])
    if r1<r2:
        orientation=~orientation
    x_contour = x_contour[orientation]
    y_contour = y_contour[orientation]
    center_x = np.mean(x_contour)
    center_y = np.mean(y_contour)
    angles = np.arctan2(y_contour - center_y, x_contour - center_x)
    sorted_indices = np.argsort(angles)
    existing_x_sorted = x_contour[sorted_indices]
    existing_y_sorted = y_contour[sorted_indices]
    angles_sorted = angles[sorted_indices]
    angle_diff = np.abs(np.append(angles_sorted[1:], angles_sorted[0]+2*np.pi) - angles_sorted)
    gap_length = 5/np.mean(1/angle_diff)
    gap_indices = np.where(angle_diff > gap_length)[0]
    for gap_indice in gap_indices:
        start_index = gap_indice
        try:
            radius = np.mean(np.sqrt((existing_x_sorted[start_index - 4] - center_x) ** 2 + (
                    existing_y_sorted[start_index - 4] - center_y) ** 2))
        except:
            radius = np.mean(np.sqrt(
                (existing_x_sorted[start_index] - center_x) ** 2 + (existing_y_sorted[start_index] - center_y) ** 2))
        if gap_indice + 1 < len(angles_sorted):
            end_index = gap_indice + 1
            angle_interp = np.linspace(angles_sorted[start_index], angles_sorted[end_index], 1000)
        else:
            end_index = 0
            angle_interp = np.linspace(angles_sorted[start_index], angles_sorted[end_index] + 2 * np.pi, 1000)
        interp_x = radius * np.cos(angle_interp) + center_x
        interp_y = radius * np.sin(angle_interp) + center_y
        existing_x_sorted = np.insert(existing_x_sorted, start_index, interp_x)
        existing_y_sorted = np.insert(existing_y_sorted, start_index, interp_y)
    c = np.empty((existing_x_sorted.shape[0], 1, 2), dtype = np.float32)
    c[:, 0, 0] = existing_x_sorted
    c[:, 0, 1] = existing_y_sorted
    return c


def merge_circle(edges,n_dots,r_guess,fill_bool=False):
    contours = find_contours(edges)
    contours = sorted(contours, key = len, reverse = True)
    # [len(c) for c in contours]
    new_edges = np.zeros_like(edges,dtype=np.uint8)
    cxs = []
    cys = []
    sel_contour = []
    for contour in contours:
        _, tot_radius = cv2.minEnclosingCircle(contour.astype(int))
        if tot_radius < r_guess * 0.7:
            continue
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = np.mean(contour[:,1])#int(M['m10'] / M['m00'])
            cy = np.mean(contour[:,0])#int(M['m01'] / M['m00'])
            is_near = False
            for cx_prev,cy_prev in zip(cxs,cys):
                if (cx-cx_prev)**2+(cy-cy_prev)**2<r_guess/2:
                    is_near = True
                    continue
            if is_near:
                continue
            else:
                if fill_bool:
                    contour = fill_gap(contour)
                else:
                    contour = contour[:, ::-1]
                cv2.drawContours(new_edges, [contour.astype(int)], contourIdx = -1, color = 255, thickness = 2)
                cxs.append(cx)
                cys.append(cy)
                sel_contour.append(contour)
        if len(cxs)>=n_dots:
            break
    return new_edges.astype(bool), sel_contour