import streamlit as st
import os
import pandas as pd
from datetime import date
from analysis.image_analysis import run_full_analysis
from utils.session_utils import initial_state_value

BASEDIR = "/media/mp274748/Transcend/data/Glue_Files/"

def page2():
    st.set_page_config(layout="centered")
    st.title("Automatic Analysis")

    # --- Select date ---
    selected_date = st.date_input(
        "Select a date",
        date.fromisoformat("2025-02-06"),
        key="selected_date_auto"
    )

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
        initial_state_value("high_threshold", 30)
        high_threshold = st.slider('Edge high_threshold', 10, 100, step=1, value=st.session_state.high_threshold)

        initial_state_value("downsample_factor", 7)
        downsample_factor = st.slider('Downsample factor', 1, 20, step=1, value=int(st.session_state.downsample_factor))

        initial_state_value("fit_bool", False)
        fit_bool = st.checkbox('Fit circles', value=st.session_state.fit_bool)

        initial_state_value("use_img_bool", False)
        use_img_bool = st.checkbox('Use image guess', value=st.session_state.use_img_bool)

        initial_state_value("contour_bool", False)
        contour_bool = st.checkbox('Contour filter (for Area)', value = st.session_state.contour_bool)

        initial_state_value("fill_bool", False)
        fill_bool = st.checkbox('Fill circles', value = st.session_state.fill_bool)

    with col2:
        initial_state_value("crop_values", "600, 2610, 1370, 3520")
        crop_val_str = st.text_input("Crop [top, bottom, left, right]:", st.session_state.crop_values)

        initial_state_value("r_guess", 500)
        r_guess = int(st.text_input("Radius guess:", st.session_state.r_guess))

        initial_state_value("n_dots", 1)
        n_dots_sel = [i for i in range(1, 10)]
        n_dots = st.selectbox("Number of dots:", n_dots_sel, n_dots_sel.index(st.session_state.n_dots))

        pxl_range_list = [i for i in range(5, 30, 5)]
        initial_state_value("pxl_range", pxl_range_list[3])
        pxl_range = st.selectbox("Pixel range:", pxl_range_list, pxl_range_list.index(st.session_state.pxl_range))

        pxl_accuracy_list = [i for i in range(1, 9)]
        initial_state_value("pxl_accuracy", pxl_accuracy_list[0])
        pxl_accuracy = st.selectbox("Pixel accuracy:", pxl_accuracy_list, pxl_accuracy_list.index(st.session_state.pxl_accuracy))

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
            crop = [600, 2610, 1370, 3520]  # full image; adjust if needed

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
                use_img_bool=use_img_bool,
                contour_bool=contour_bool,
                fill_bool=fill_bool,
                pxl_range=pxl_range,
                pxl_accuracy=pxl_accuracy
            )

            im_diff, edge, df, objects, contours, im_fit = analysis_result
            print(df)
            if df is not None:
                df["image_file"] = img_file
                results_list.append(df)

            # Update progress bar
            my_bar.progress((i + 1) / len(selected_files), text=f"Processing {img_file}")

        # --- Combine results ---
        if results_list:
            final_df = pd.concat(results_list, ignore_index=True)
            st.success("Analysis completed!")
            st.dataframe(final_df)
            save_path = os.path.join(BASEDIR, f"automatic_analysis_{selected_date}.csv")
            final_df.to_csv(save_path, index=False)
            st.info(f"Results saved to: {save_path}")
        else:
            st.warning("No circles detected in selected images.")
page2()