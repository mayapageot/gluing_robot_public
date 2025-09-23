import numpy as np
from skimage.measure import find_contours

def concat_large_contours(edge_image, length_threshold):
    contours = find_contours(edge_image, 0.5)

    # Filter and concatenate all contours larger than the threshold
    large_contours = [contour for contour in contours if len(contour) > length_threshold]

    if len(large_contours) == 0:
        return np.empty((0, 2))  # No large contours, return empty array

    # Concatenate all selected contours into one big array
    concatenated_contour = np.concatenate(large_contours, axis=0)

    return concatenated_contour
def orientation_of_consecutive_vectors(x, y):
    # Calculate the cross product between consecutive vectors
    x_start = np.append(x[1:],x[0])
    y_start = np.append(y[1:],y[0])
    cross_products = x * y_start - y * x_start

    # Determine orientation based on the sign of the cross product
    orientation = cross_products > 0
    return orientation
def fill_gap(contour, gap_length=np.pi / 10):
    x_contour, y_contour = contour[:, 1], contour[:, 0]
    orientation = orientation_of_consecutive_vectors(x_contour - x_contour.mean(), y_contour - y_contour.mean())
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
