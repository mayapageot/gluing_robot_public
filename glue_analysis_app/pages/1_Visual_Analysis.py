import streamlit as st
from datetime import date
from PIL import Image
import os
import pandas as pd
import numpy as np
from streamlit_drawable_canvas import st_canvas
from utils import image_utils, session_utils, io_utils, plotting_utils
from config.settings import BASEDIR, DEFAULT_PARAMS
from utils.session_utils import initial_state_value,save_session_state,load_session_state
from analysis.image_analysis import  run_full_analysis

json_rect = {
    "version": "4.4.0",
    "objects": [
        {
            "type": "rect",
            "left": 74,
            "top": 29,
            "width": 129,
            "height": 129,
            "fill": "rgba(255, 0, 0, 0.1)",
            "stroke": "rgba(255, 0, 0, 1)",
            "strokeWidth": 3,
            "scaleX": 1,
            "scaleY": 1,
            "angle": 0,
            "visible": True
        }
    ]
}
json_circle = {
    "version": "4.4.0",
    "objects": [
        {
            "type": "circle",
            "left": 50,     # x-position
            "top": 50,      # y-position
            "radius": 40,   # circle radius
            "stroke": "rgba(255,0,0,1)",       # red border
            "fill": "rgba(255,0,0,0.3)",       # semi-transparent fill
            "strokeWidth": 3
        }
    ]
}
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


def page1():
    st.set_page_config(layout="centered")
    if "selected_date" not in st.session_state:
        try:
            st.session_state.selected_date = st.session_state.selected_date2
        except:
            st.session_state.selected_date = date.today()

    # The widget controls the value
    selected_date = st.sidebar.date_input(
        "Select a date",
        st.session_state.selected_date,
        key = "selected_date"
    )
    st.session_state.selected_date2 = st.session_state.selected_date
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
    if "json_data" not in st.session_state:
        st.session_state.json_data = json_rect
    # --- Session state loading ---
    if st.sidebar.button("Load previous session state"):
        print("Loading session state...")
        load_session_state()
        # Convert string to list of ints
        crop_list = [int(x) for x in st.session_state.crop.split(",")]

        st.session_state.json_data["objects"][0]["left"] = crop_list[2] * factor_main_image
        st.session_state.json_data["objects"][0]["top"] = crop_list[0] * factor_main_image
        st.session_state.json_data["objects"][0]["width"] = (crop_list[3] - crop_list[2]) * factor_main_image
        st.session_state.json_data["objects"][0]["height"] = (crop_list[1] - crop_list[0]) * factor_main_image
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
    initial_state_value("high_threshold", DEFAULT_PARAMS["high_threshold"])
    high_threshold = st.sidebar.slider('Edge high_threshold', 10, 100, step=1, value=st.session_state.high_threshold,key="high_threshold")

    initial_state_value("downsample_factor", DEFAULT_PARAMS["downsample_factor"])
    downsample_factor = st.sidebar.slider('downsample factor', 1, 20, step=1, value=int(st.session_state.downsample_factor),key = "downsample_factor")

    initial_state_value("fit_bool", DEFAULT_PARAMS["fit_bool"])
    fit_bool = st.sidebar.checkbox('Fit circle', value=st.session_state.fit_bool,key ="fit_bool")

    initial_state_value("use_img_bool", DEFAULT_PARAMS["use_img_bool"])
    use_img_bool = st.sidebar.checkbox('Use image guess', value=st.session_state.use_img_bool,key = "use_img_bool")

    initial_state_value("contour_bool", DEFAULT_PARAMS["contour_bool"])
    contour_bool = st.sidebar.checkbox('contour filter (necessary for Area)', value=st.session_state.contour_bool,key = "contour_bool")

    initial_state_value("fill_bool", DEFAULT_PARAMS["fill_bool"])
    fill_bool = st.sidebar.checkbox('fill circle', value=st.session_state.fill_bool,key = "fill_bool")

    # Ensure r_guess exists as string
    initial_state_value("r_guess", str(DEFAULT_PARAMS["r_guess"]))

    # If using image radius, show it in the widget but disable editing
    r_guess_default = st.session_state.r_guess
    if use_img_bool and "radius_orig" in st.session_state and st.session_state.radius_orig:
        r_guess_default = str(int(st.session_state.radius_orig))

    # Create text_input (disabled if use_img_bool)
    r_guess_str = st.sidebar.text_input(
        "r_guess:",
        value = r_guess_default,
        disabled = use_img_bool,
        key = "r_guess"
    )

    # Safely convert to int
    try:
        r_guess = int(r_guess_str)
    except ValueError:
        r_guess = int(DEFAULT_PARAMS["r_guess"])  # fallback

    initial_state_value("n_dots", DEFAULT_PARAMS["n_dots"])
    n_dots_sel = list(range(DEFAULT_PARAMS["n_dots_min"], DEFAULT_PARAMS["n_dots_max"]))
    n_dots = st.sidebar.selectbox("n_dots:", n_dots_sel, n_dots_sel.index(st.session_state.n_dots),key = "n_dots")

    pxl_range_list = list(range(DEFAULT_PARAMS["pxl_range_min"], DEFAULT_PARAMS["pxl_range_max"], DEFAULT_PARAMS["pxl_range_interval"]))
    initial_state_value("pxl_range", DEFAULT_PARAMS["pxl_range"])
    pxl_range = st.sidebar.selectbox("pxl_range:", pxl_range_list, pxl_range_list.index(st.session_state.pxl_range),key = "pxl_range")

    pxl_accuracy_list = list(range(DEFAULT_PARAMS["pxl_accuracy_min"], DEFAULT_PARAMS["pxl_accuracy_max"]))
    initial_state_value("pxl_accuracy", DEFAULT_PARAMS["pxl_accuracy"])
    pxl_accuracy = st.sidebar.selectbox("pxl_accuracy:", pxl_accuracy_list, pxl_accuracy_list.index(st.session_state.pxl_accuracy),key = "pxl_accuracy")

    # --- Paths for selected images ---
    path_glue = image_path(image_options, num_option, selected_num)
    path_ref = image_path(image_options, num_option, selected_num_ref)

    # --- Main UI layout ---
    left, right = st.columns(2, vertical_alignment="center")
    with right:
        st.image(path_ref, caption = "im Diff", width = 300)
    with left:
        # Ensure crop exists
        if "crop" not in st.session_state:
            st.session_state.crop = "600,2610,1370,3520"

        # --- Canvas ---
        canvas_main_image = st_canvas(
            fill_color = "rgba(255,0,0,0.1)",
            stroke_width = 3,
            stroke_color = "rgba(255,0,0,1)",
            background_color = "#eee",
            background_image = Image.open(path_glue),
            update_streamlit = True,
            width = int(w * factor_main_image),
            height = int(h * factor_main_image),
            drawing_mode = "transform",
            point_display_radius = 0,
            key = "main_image",
            initial_drawing = st.session_state.json_data
        )

        # --- Update session_state.crop from user only ---
        if canvas_main_image.json_data is not None:
            rects = canvas_main_image.json_data.get("objects", [])
            if rects:
                rect = rects[0]
                new_crop = ",".join([
                    str(round(rect["top"] / factor_main_image)),
                    str(round((rect["top"] + rect["height"]) / factor_main_image)),
                    str(round(rect["left"] / factor_main_image)),
                    str(round((rect["left"] + rect["width"]) / factor_main_image))
                ])
                if new_crop != st.session_state.crop:
                    st.session_state.crop = new_crop

        # Always use session_state crop
        crop = [int(x.strip()) for x in st.session_state.crop.split(",")]
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
            contour_bool=contour_bool,
            fill_bool=fill_bool,
            pxl_range=pxl_range,
            pxl_accuracy=pxl_accuracy
        )

        im_diff, edge, df, objects, contours, im_fit = results
        edge = image_utils.get_edges(im_diff, high_threshold, downsample_factor)
        if contour_bool:
            edge, contours = image_utils.merge_circle(edge, n_dots, r_guess // downsample_factor, fill_bool)
        factor = 200 / edge.shape[1]
        left,_, middle,mid_bis, right = st.columns([5,1,5,1,5], vertical_alignment = "center")
        with left:
            st.image(im_diff, width = 200)

        with middle:
            circle_draw = st_canvas(
                fill_color = "rgba(255,0,0,0.2)",  # only used for new shapes
                stroke_width = 3,
                stroke_color = "rgba(255,0,0,1)",  # only used for new shapes
                background_color = "#eee",
                background_image = Image.fromarray((edge * 255).astype(np.uint8)),
                update_streamlit = True,
                width = 200,
                height = 200,
                drawing_mode = "transform",
                initial_drawing = json_circle,
                point_display_radius = 0,
                key = "circle_draw"
            )
        # --- Process user circles ---
        objects = pd.DataFrame({"center_x": [], "center_y": [], "radius_guess": []})

        if circle_draw.json_data is not None:
            objs = circle_draw.json_data.get("objects", [])
            if objs:
                obj = objs[0]

                # Effective dimensions in canvas coords
                width = obj["width"] * obj.get("scaleX", 1)
                height = obj["height"] * obj.get("scaleY", 1)
                radius_canvas = (width + height) / 4  # average, safer than just width/2

                # Center in canvas coords
                cx_canvas = obj["left"] + width / 2
                cy_canvas = obj["top"] + height / 2

                # Convert back to downsampled coords
                cx_down = cx_canvas / factor
                cy_down = cy_canvas / factor
                radius_down = radius_canvas / factor

                # Convert back to original image coords
                cx_orig = cx_down * downsample_factor
                cy_orig = cy_down * downsample_factor
                radius_orig = radius_down * downsample_factor

                objects = pd.DataFrame({
                    "center_x": [cx_orig],
                    "center_y": [cy_orig],
                    "radius_guess": [radius_orig]
                })
                st.session_state.radius_orig = str(int(radius_orig))


        with right:
            if fit_bool and im_fit is not None:
                st.image(im_fit, width = 200, caption = "Fit")
        # --- DataFrames ---
        left, right = st.columns(2, vertical_alignment="center")
        with right:
            "Analysis results :"
            # List of columns to exclude
            exclude_cols = ["crop_top", "crop_bottom", "crop_left", "crop_right", "image_file"]

            # Filter columns
            display_df = df[[c for c in df.columns if c not in exclude_cols]]

            # Show in Streamlit
            st.dataframe(display_df, hide_index = True)
        with left:
            "Image Guess :"
            if len(objects) > 0:
                st.dataframe(objects.loc[:, ["center_x", "center_y", "radius_guess"]], hide_index=True)
            else:
                st.dataframe({"x": [], "y": [], "radius_guess": [], "dot_pos": []}, hide_index=True)

        # --- Save session ---
        if st.button("Save Session State"):
            dic_stat = st.session_state.to_dict()
            cols_to_save = [
                "selected_date", "selected_num", "downsample_factor", "pxl_range", "n_dots",
                "selected_num_ref", "fit_bool", "fill_bool", "use_img_bool", "high_threshold",
                "pxl_accuracy", "r_guess", "contour_bool", "crop"
            ]
            # make sure only those columns are included
            df_info = pd.DataFrame([{col: dic_stat.get(col) for col in cols_to_save}])

            save_session_state(df_info)
            final_df = df
            save_dir = os.path.join(BASEDIR, "analysis")
            os.makedirs(save_dir, exist_ok = True)
            save_path = os.path.join(save_dir, f"{selected_date}.csv")

            # --- Merge with existing file if present ---
            if os.path.exists(save_path):
                existing_df = pd.read_csv(save_path)

                # Drop duplicates on (image_file, dot_pos), keeping NEW results
                merged_df = pd.concat([existing_df, final_df], ignore_index = True)
                merged_df = merged_df.drop_duplicates(subset = ["image_file", "dot_pos"], keep = "last")
            else:
                merged_df = final_df

            # --- Extract numeric part for sorting ---
            merged_df["image_num"] = merged_df["image_file"].str.extract(r"(\d{10})(?=\.bmp)").astype(int)

            # Sort by image_num, then dot_pos
            merged_df = merged_df.sort_values(by = ["image_num", "dot_pos"]).reset_index(drop = True)

            # Drop helper column before saving
            merged_df = merged_df.drop(columns = ["image_num"])

            # Save merged result
            merged_df.to_csv(save_path, index = False)
            st.info(f"Results saved to: {save_path}")
page1()