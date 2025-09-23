"""
Analysis pipeline for glue images (independent from GUI).
"""

import cv2
import numpy as np
import pandas as pd
from utils import image_utils

def get_dot_pos(df):
    if len(df)==1:
        df["dot_pos"]="middle"
    if len(df)==5:
        idx = df.index
        df["dot_pos"] = ["m"]*5
        idx_tl = idx[np.argmax(-df["center_x"]**2-df["center_y"]**2)]
        idx_tr = idx[np.argmax(-df["center_x"]**2+df["center_y"]**2)]
        idx_bl = idx[np.argmax(df["center_x"]**2-df["center_y"]**2)]
        idx_br = idx[np.argmax(df["center_x"]**2+df["center_y"]**2)]
        df.loc[[idx_tl,idx_tr,idx_bl,idx_br],"dot_pos"] = ["top left","top right","bottom left","bottom right"]
        df.sort_values("dot_pos")
    return df

def analyze_image(
    path_glue: str,
    path_ref: str,
    crop: list,
    high_threshold: int,
    downsample_factor: int,
    fit_bool: bool,
    use_img_bool: bool,
    contour_bool: bool,
    fill_bool: bool,
    r_guess: int,
    n_dots: int,
    pxl_range: int,
    pxl_accuracy: int,
    objects_df: pd.DataFrame | None = None
) :
    """
    Perform full analysis on a glue image.

    Args:
        path_glue: Path to image.
        path_ref: Path to reference image.
        crop: [ymin, ymax, xmin, xmax] crop.
        high_threshold: Canny high threshold.
        downsample_factor: Downsampling factor.
        fit_bool: Whether to run circle fitting.
        use_img_bool: Use manual guess from UI.
        contour_bool: Apply contour filter.
        fill_bool: Fill detected circles.
        r_guess: Radius guess.
        n_dots: Number of circles.
        pxl_range: Pixel search range.
        pxl_accuracy: Pixel step size.
        objects_df: Optional DataFrame of manual guesses (from UI).

    Returns:
        im_result: Image with circles drawn.
        df_results: DataFrame with detected features.
    """
    # --- Difference & edges ---
    im_diff = image_utils.get_im_diff(path_glue, path_ref, crop)
    edges = image_utils.get_edges(im_diff, high_threshold, downsample_factor)

    # Optional contour filtering
    contours = None
    if contour_bool:
        edges, contours = image_utils.merge_circle(
            edges, n_dots, r_guess // downsample_factor, fill_bool
        )

    df = pd.DataFrame(columns=["x", "y", "radius", "accum", "dot_pos"])

    if fit_bool:
        im_diff = np.clip(im_diff, 0, 255).astype(np.uint8)
        im_result = cv2.cvtColor(im_diff, cv2.COLOR_GRAY2RGB)

        # --- Circle detection ---
        if use_img_bool and objects_df is not None and len(objects_df) > 0:
            accums, cx, cy, radii = np.array([]), np.array([], dtype=int), np.array([], dtype=int), np.array([], dtype=int)
            for _, row in objects_df.iterrows():
                centerx, centery, r = row["x"], row["y"], row["radius"]
                min_y, max_y = max(centery - r - pxl_range, 0), min(centery + r + pxl_range, edges.shape[0])
                min_x, max_x = max(centerx - r - pxl_range, 0), min(centerx + r + pxl_range, edges.shape[1])
                im_dot = edges[min_y:max_y, min_x:max_x]
                accum, x, y, radius = image_utils.get_circle(
                    im_dot, r_guess=int(row["radius"]), n_dots=1,
                    pxl_range=pxl_range, pxl_accuracy=pxl_accuracy
                )
                accums, cx, cy, radii = (
                    np.concatenate((accums, accum)),
                    np.concatenate((cx, x + min_x)),
                    np.concatenate((cy, y + min_y)),
                    np.concatenate((radii, radius)),
                )
            cx, cy, radii = cx * downsample_factor, cy * downsample_factor, radii * downsample_factor
        else:
            accums, cx, cy, radii = image_utils.get_circle(
                edges, r_guess=r_guess // downsample_factor,
                n_dots=n_dots, pxl_range=pxl_range, pxl_accuracy=pxl_accuracy
            )
            cx, cy, radii = cx * downsample_factor, cy * downsample_factor, radii * downsample_factor

        if contour_bool:
            radii = radii - downsample_factor

        for center_y, center_x, radius in zip(cy, cx, radii):
            cv2.circle(im_result, (center_x, center_y), int(radius), (255, 0, 0), 10)

        df = pd.DataFrame(dict(x=cx, y=cy, radius=radii, accum=accums))
        df = get_dot_pos(df)

        # Add contour areas if requested
        if contour_bool and contours is not None:
            df_area = pd.DataFrame(
                {"center_x": [], "center_y": [], "Area": []})
            for i, cnt in enumerate(contours):
                M = cv2.moments(cnt)
                df_area.loc[i, ["center_x", "center_y", "Area"]] = [M['m10'] / M['m00'], M['m01'] / M['m00'], M['m00']]
                df_area = get_dot_pos(df_area)
                df_area = df_area.drop(["center_x", "center_y"], axis = 1)
            df = pd.merge(df, df_area, on = "dot_pos")

    else:
        im_result = im_diff  # just show diff if no fitting
    im_diff = image_utils.get_im_diff(path_glue, path_ref, crop)
    edges = image_utils.get_edges(im_diff, high_threshold, downsample_factor)
    contours = []
    im_fit = im_result
    objects = pd.DataFrame(columns = ["center_x", "center_y", "radius_guess", "dot_pos"])
    # ... circle detection, merging contours, etc ...

    return {
        "im_diff": im_diff,
        "edges": edges,
        "df": df,
        "contours": contours,
        "im_fit": im_fit,
        "objects": objects
    }


def run_full_analysis(
    path_glue,
    path_ref,
    crop,
    high_threshold,
    downsample_factor,
    n_dots,
    r_guess,
    fit_bool,
    use_img_bool,
    contour_bool,
    fill_bool,
    pxl_range,
    pxl_accuracy
):
    """
    Wrapper around analyze_image() to adapt its outputs for Streamlit GUI.
    Returns:
        im_diff: np.ndarray, difference image
        edge: np.ndarray, edge map
        df: pd.DataFrame, detected circles info
        objects: pd.DataFrame, user-drawn guesses (empty for now)
        contours: list, detected contours if countour_bool=True
        im_fit: np.ndarray, image with detected circles drawn
    """

    # Call the core analysis function
    analysis_result = analyze_image(
        path_glue=path_glue,
        path_ref=path_ref,
        crop=crop,
        high_threshold=high_threshold,
        downsample_factor=downsample_factor,
        n_dots=n_dots,
        r_guess=r_guess,
        fit_bool=fit_bool,
        use_img_bool=use_img_bool,
        contour_bool=contour_bool,
        fill_bool=fill_bool,
        pxl_range=pxl_range,
        pxl_accuracy=pxl_accuracy
    )

    # Unpack results
    im_diff = analysis_result["im_diff"]
    edge = analysis_result["edges"]
    df = analysis_result.get("df", None)

    contours = analysis_result.get("contours", [])
    im_fit = analysis_result.get("im_fit", None)
    objects = analysis_result.get("objects", pd.DataFrame(columns=["center_x", "center_y", "radius_guess", "dot_pos"]))

    # Ensure dot positions are set
    if df is not None:
        df = get_dot_pos(df)
    return im_diff, edge, df, objects, contours, im_fit