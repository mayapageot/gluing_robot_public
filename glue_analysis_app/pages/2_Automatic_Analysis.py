import streamlit as st
import os
import pandas as pd
from datetime import date
from analysis.image_analysis import run_full_analysis
from utils.session_utils import initial_state_value
from config.settings import BASEDIR, DEFAULT_PARAMS

def page2():
    st.set_page_config(layout="centered")
    st.title("Automatic Analysis")

    # --- Select date ---
    if "selected_date" not in st.session_state:
        try:
            st.session_state.selected_date = st.session_state.selected_date2
        except:
            st.session_state.selected_date = date.today()

    # The widget controls the value
    selected_date = st.date_input(
        "Select a date",
        st.session_state.selected_date,
        key = "selected_date"
    )
    st.session_state.selected_date2 = st.session_state.selected_date
    list_dirs = [dir for dir in os.listdir(BASEDIR) if selected_date.strftime("%y%m%d") == dir[:6]]

    if len(list_dirs) == 0:
        st.warning("No images found for the selected date.")
        return

    dir = os.path.join(BASEDIR, list_dirs[0], "CAM1")
    image_files = [f for f in os.listdir(dir) if f.lower().endswith(".bmp")]
    image_files.sort()
    num_option = [int(img[-14:-4]) for img in image_files]
    # --- User selects images (main window) ---
    st.write("### Select images to analyze")

    # Extract image numbers
    image_numbers = [int(f[-14:-4]) for f in image_files]

    # Initialize session state for persistence
    if "selected_numbers" not in st.session_state:
        st.session_state.selected_numbers = []

    selected_numbers = []

    # Rolling window / scrollable container
    with st.expander("Select images (scrollable)"):
        n_cols = 10
        cols = st.columns(n_cols)

        for idx, (num, f) in enumerate(zip(image_numbers, image_files)):
            col = cols[idx % n_cols]
            checked = num in st.session_state.selected_numbers
            if col.checkbox(f"{num}", value = checked, key = f"chk_{num}"):
                selected_numbers.append(num)

    # Update session_state for persistence
    st.session_state.selected_numbers = selected_numbers

    # Map selected numbers back to filenames
    selected_files = [f for f, num in zip(image_files, image_numbers) if num in selected_numbers]

    if not selected_files:
        st.warning("No images selected.")
        return

    # --- Analysis parameters ---
    col1, col2 = st.columns(2)

    with col1:
        # --- Delta reference ---
        initial_state_value("delta_ref", 1)
        delta_ref = st.number_input(
            "Reference image delta",
            min_value = 1,
            max_value = 5,
            step = 1,
            value = st.session_state.delta_ref
        )
        initial_state_value("high_threshold", DEFAULT_PARAMS["high_threshold"])
        high_threshold = st.slider('Edge high_threshold', 10, 100, step=1, value=st.session_state.high_threshold,key = "high_threshold")

        initial_state_value("downsample_factor", DEFAULT_PARAMS["downsample_factor"])
        downsample_factor = st.slider('Downsample factor', 1, 20, step=1, value=int(st.session_state.downsample_factor),key = "downsample_factor")

        initial_state_value("fit_bool", DEFAULT_PARAMS["fit_bool"])
        fit_bool = st.checkbox('Fit circles', value=st.session_state.fit_bool,key = "fit_bool")

        initial_state_value("contour_bool", DEFAULT_PARAMS["contour_bool"])
        contour_bool = st.checkbox('Contour filter (for Area)', value = st.session_state.contour_bool,key = "contour_bool")

        initial_state_value("fill_bool", DEFAULT_PARAMS["fill_bool"])
        fill_bool = st.checkbox('Fill circles', value = st.session_state.fill_bool, key = "fill_bool")

    with col2:
        initial_state_value("crop",DEFAULT_PARAMS["crop"])
        crop_val_str = st.text_input("Crop [top, bottom, left, right]:", st.session_state.crop, key="crop")
        try:
            crop = [int(x.strip()) for x in crop_val_str.split(",")]
        except ValueError:
            st.error("Invalid crop values! Please enter 4 integers separated by commas.")
            st.session_state.crop = DEFAULT_PARAMS["crop"]
            crop_val_str = DEFAULT_PARAMS["crop"]
            crop = [int(x.strip()) for x in crop_val_str.split(",")]  # fallback default
        initial_state_value("r_guess", DEFAULT_PARAMS["r_guess"])
        r_guess = int(st.text_input("Radius guess:", st.session_state.r_guess))

        initial_state_value("n_dots", DEFAULT_PARAMS["n_dots"])
        n_dots_sel = list(range(DEFAULT_PARAMS["n_dots_min"], DEFAULT_PARAMS["n_dots_max"]))
        n_dots = st.sidebar.selectbox("n_dots:", n_dots_sel, n_dots_sel.index(st.session_state.n_dots), key = "n_dots")

        pxl_range_list = list(range(DEFAULT_PARAMS["pxl_range_min"], DEFAULT_PARAMS["pxl_range_max"],
                                    DEFAULT_PARAMS["pxl_range_interval"]))
        initial_state_value("pxl_range", DEFAULT_PARAMS["pxl_range"])
        pxl_range = st.sidebar.selectbox("pxl_range:", pxl_range_list, pxl_range_list.index(st.session_state.pxl_range),
                                         key = "pxl_range")

        pxl_accuracy_list = list(range(DEFAULT_PARAMS["pxl_accuracy_min"], DEFAULT_PARAMS["pxl_accuracy_max"]))
        initial_state_value("pxl_accuracy", DEFAULT_PARAMS["pxl_accuracy"])
        pxl_accuracy = st.sidebar.selectbox("pxl_accuracy:", pxl_accuracy_list,
                                            pxl_accuracy_list.index(st.session_state.pxl_accuracy),
                                            key = "pxl_accuracy")

        if "final_df" not in st.session_state:
            st.session_state["final_df"] = pd.DataFrame({})
    # --- Run analysis button ---
    if st.button("Run Automatic Analysis"):
        results_list = []
        progress_text = "Processing images..."
        my_bar = st.progress(0, text=progress_text)

        for i, img_file in enumerate(selected_files):
            path_glue = os.path.join(dir, img_file)
            im_num = int(img_file[-14:-4])
            ref_num = im_num - delta_ref
            path_ref = os.path.join(dir, image_files[num_option.index(ref_num)])


            # Run analysis
            analysis_result = run_full_analysis(
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

            im_diff, edge, df, objects, contours, im_fit = analysis_result
            if df is not None:
                results_list.append(df)

            # Update progress bar
            my_bar.progress((i + 1) / len(selected_files), text=f"Processing {img_file}")

        # --- Combine results ---

        if results_list:
            final_df = pd.concat(results_list, ignore_index = True)
            st.success("Analysis completed!")
            st.session_state["final_df"] = final_df
        else:
            st.warning("No circles detected in selected images.")
    st.dataframe(st.session_state["final_df"])
    if st.button("Save Analysis"):
        final_df = st.session_state["final_df"]
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
page2()