import streamlit as st
from datetime import date
from PIL import Image
import cv2
import os
import pandas as pd
import numpy as np
from streamlit_drawable_canvas import st_canvas
import json
import time
from utils import image_utils, session_utils, io_utils, plotting_utils
from config.settings import BASEDIR, DEFAULT_PARAMS
from utils.session_utils import initial_state_value,save_session_state,load_session_state
def crop_to_canvas_json(crop, factor):
    top, bottom, left, right = crop
    return {
        "objects": [
            {
                "type": "rect",
                "left": int(left * factor),
                "top": int(top * factor),
                "width": int((right - left) * factor),
                "height": int((bottom - top) * factor),
                "fill": "rgba(255, 0, 0, 0.1)",
                "stroke": "rgba(255, 0, 0, 1)",
                "strokeWidth": 3,
            }
        ]
    }
def rect_from_canvas(rect_crop, factor):
    """Convert canvas rect object to [top, bottom, left, right]."""
    return [
        int(rect_crop["top"] / factor),
        int((rect_crop["top"] + rect_crop["height"]) / factor),
        int(rect_crop["left"] / factor),
        int((rect_crop["left"] + rect_crop["width"]) / factor),
    ]

def image_path(image_options,num_option,num):
    return image_options[num_option.index(num)]


from analysis.image_analysis import (
    run_full_analysis,
    get_dot_pos
)


def page1():
    st.set_page_config(layout="centered")
    selected_date = st.sidebar.date_input(
        "Select a date",
        date.fromisoformat('2025-09-17'),
        key="selected_date"
    )

    # --- Find directories for selected date ---
    list_dirs = [d for d in os.listdir(BASEDIR) if selected_date.strftime("%y%m%d") == d[:6]]
    if len(list_dirs) == 0:
        st.warning("No images found for this date.")
        return
    dir = os.path.join(BASEDIR, list_dirs[0], "CAM1")
    image_options = [
        os.path.join(dir, file) for file in os.listdir(dir) if file.endswith("bmp")
    ]
    num_option = [int(img[-14:-4]) for img in image_options]
    image_options = [img for _, img in sorted(zip(num_option, image_options))]
    num_option = sorted(num_option)
    selected_num = st.sidebar.selectbox(
        "Select a image number:", num_option, num_option[1], key="selected_num"
    )
    w, h = 5104, 4092
    factor_main_image = 300 / w
    with open(os.path.join(BASEDIR, "test.json"), 'r') as json_file:
        json_data = json.load(json_file)
    # --- Session state loading ---
    if st.sidebar.button("Load previous session state"):
        print("Loading session state...")
        load_session_state()
        json_data["objects"][0]["left"]= int(st.session_state.crop[2] * factor_main_image),
        json_data["objects"][0]["top"]=int(st.session_state.crop[0] * factor_main_image),
        json_data["objects"][0]["width"]= int((st.session_state.crop[3] - st.session_state.crop[2]) * factor_main_image),
        json_data["objects"][0]["height"]= int((st.session_state.crop[1] - st.session_state.crop[0]) * factor_main_image),
    # --- Reference image ---
    delta_ref = 1
    selected_num_ref_val = selected_num - delta_ref
    # Clamp to valid numbers in num_option
    if selected_num_ref_val not in num_option:
        selected_num_ref_val = min(num_option, key = lambda x: abs(x - selected_num_ref_val))
    initial_state_value("selected_num_ref", selected_num_ref_val)
    # Force session state to this value
    st.session_state.selected_num_ref = selected_num_ref_val
    selected_num_ref = st.sidebar.selectbox(
        "Select a ref number:", num_option, num_option.index(selected_num_ref_val), key="selected_num_ref"
    )
    # --- Sidebar parameters ---
    initial_state_value("high_threshold", 30)
    high_threshold = st.sidebar.slider('Edge high_threshold', 10, 100, step=1, value=st.session_state.high_threshold,key="high_threshold")

    initial_state_value("downsample_factor", 7)
    downsample_factor = st.sidebar.slider('downsample factor', 1, 20, step=1, value=int(st.session_state.downsample_factor),key = "downsample_factor")

    initial_state_value("fit_bool", False)
    fit_bool = st.sidebar.checkbox('Fit circle', value=st.session_state.fit_bool,key ="fit_bool")

    initial_state_value("use_img_bool", False)
    use_img_bool = st.sidebar.checkbox('Use image guess', value=st.session_state.use_img_bool,key = "use_img_bool")

    initial_state_value("contour_bool", False)
    contour_bool = st.sidebar.checkbox('contour filter (necessary for Area)', value=st.session_state.contour_bool,key = "contour_bool")

    initial_state_value("fill_bool", False)
    fill_bool = st.sidebar.checkbox('fill circle', value=st.session_state.fill_bool,key = "fill_bool")

    initial_state_value("r_guess", '500')
    # Make sure initial value is stored as string
    if "r_guess" not in st.session_state:
        st.session_state.r_guess = "500"  # store as string, not int

    # Use text_input with string default
    r_guess_str = st.sidebar.text_input(
        "r_guess:", st.session_state.r_guess, key = "r_guess"
    )

    # Convert back to int safely
    try:
        r_guess = int(r_guess_str)
    except ValueError:
        r_guess = int(st.session_state.r_guess)  # fallback if invalid input

    initial_state_value("n_dots", 1)
    n_dots_sel = list(range(1, 10))
    n_dots = st.sidebar.selectbox("n_dots:", n_dots_sel, n_dots_sel.index(st.session_state.n_dots),key = "n_dots")

    pxl_range_list = list(range(5, 30, 5))
    initial_state_value("pxl_range", pxl_range_list[3])
    pxl_range = st.sidebar.selectbox("pxl_range:", pxl_range_list, pxl_range_list.index(st.session_state.pxl_range),key = "pxl_range")

    pxl_accuracy_list = list(range(1, 9))
    initial_state_value("pxl_accuracy", pxl_accuracy_list[0])
    pxl_accuracy = st.sidebar.selectbox("pxl_accuracy:", pxl_accuracy_list, pxl_accuracy_list.index(st.session_state.pxl_accuracy),key = "pxl_accuracy")
    time.sleep(0.1)
    # --- Paths for selected images ---
    path_glue = image_path(image_options, num_option, selected_num)
    path_ref = image_path(image_options, num_option, selected_num_ref)

    # --- Main UI layout ---
    left, right = st.columns(2, vertical_alignment="center")
    with left:
        if "crop" not in st.session_state:
            st.session_state.crop = [600, 2610, 1370, 3520]  # default crop

        # --- Canvas widget ---


        canvas_main_image = st_canvas(
            fill_color = "rgba(255, 0, 0, 0.1)",
            stroke_width = 3,
            stroke_color = "rgba(255, 0, 0, 1)",
            background_color = "#eee",
            background_image = Image.open(path_glue),
            update_streamlit = True,
            width = int(w * factor_main_image),
            height = int(h * factor_main_image),
            drawing_mode = "transform",
            point_display_radius = 0,
            key = "main_image",
            initial_drawing = json_data
        )

        # --- Update crop from canvas if available ---
        if canvas_main_image.json_data is not None:
            with right:
                st.image(path_ref, caption = "Ref", width = 300)

            rect_crop = canvas_main_image.json_data["objects"]
            if rect_crop:
                rect_crop = rect_crop[0]
                st.session_state.crop = [
                    int(rect_crop["top"] / factor_main_image),
                    int((rect_crop["top"] + rect_crop["height"]) / factor_main_image),  # height not width!
                    int(rect_crop["left"] / factor_main_image),
                    int((rect_crop["left"] + rect_crop["width"]) / factor_main_image),
                ]

        # Always use session_state crop
        crop = st.session_state.crop

    # --- Run analysis if we have crop ---
    if crop is not None:
        results = run_full_analysis(
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

        im_diff, edge, df, objects, contours, im_fit = results
        left, middle, right = st.columns(3, vertical_alignment="center")
        with left:
            st.image(im_diff, width=200)

        with middle:
            drawing_mode = st.radio("Mode:", ["Draw", "Move"], horizontal=True, label_visibility="hidden")
            canvas_mode = "circle" if drawing_mode == "Draw" else "transform"
            canvas_result = st_canvas(
                fill_color="rgba(255, 0, 0, 0.1)",
                stroke_width=3,
                stroke_color="rgba(255, 0, 0, 1)",
                background_color="#eee",
                background_image=Image.fromarray((edge * 255).astype(np.uint8)),
                update_streamlit=False,
                width=200,
                height=200,
                drawing_mode=canvas_mode,
                point_display_radius=0,
                key="circle_draw"
            )

        if fit_bool and im_fit is not None:
            with right:
                st.image(im_fit, width=200)

        # --- DataFrames ---
        left, right = st.columns(2, vertical_alignment="center")
        with right:
            "Analysis results :"
            st.dataframe(df, hide_index=True)
        with left:
            "Image Guess :"
            if len(objects) > 0:
                objects = get_dot_pos(objects).sort_values("dot_pos")
                objects = objects.rename(columns={"center_x": "x", "center_y": "y"})
                st.dataframe(objects.loc[:, ["center_x", "center_y", "radius_guess", "dot_pos"]], hide_index=True)
            else:
                st.dataframe({"x": [], "y": [], "radius_guess": [], "dot_pos": []}, hide_index=True)

        # --- Save session ---
        if st.button("Save Session State"):
            dic_stat = st.session_state.to_dict()
            dic_stat.pop('circle_draw', None)
            dic_stat.pop('main_image', None)
            df_info = pd.json_normalize(dic_stat).astype({"selected_date": str})
            print(df_info)
            df["selected_date"] = [df_info["selected_date"].array[0]] * len(df)
            df["selected_num"] = [df_info["selected_num"].array[0]] * len(df)
            df_info.set_index(["selected_date", "selected_num"], inplace=True)
            df.set_index(["selected_date", "selected_num", "dot_pos"], inplace=True)
            save_session_state(df_info)
page1()