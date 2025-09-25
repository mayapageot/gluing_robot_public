import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw
from datetime import date
from utils import image_utils
import numpy as np
from config.settings import BASEDIR

def image_path(image_options,num_option,num):
    return image_options[num_option.index(num)]
def synch_selected_date():
    st.session_state.selected_date2 = st.session_state.selected_date
def page3():
    st.set_page_config(layout="centered")
    st.title("Visualize Analysed Images by Date")

    # --- Select date ---
    if "selected_date2" not in st.session_state:
        st.session_state.selected_date2 = date.today()
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = st.session_state.selected_date2
    selected_date = st.date_input(
        "Select a date",  # use backup for default
        key = "selected_date",  # Sync on change
        on_change = synch_selected_date
    )
    list_dirs = [dir for dir in os.listdir(BASEDIR) if selected_date.strftime("%y%m%d") == dir[:6]]

    if len(list_dirs) == 0:
        st.warning("No images found for the selected date.")
        return

    dir = os.path.join(BASEDIR, list_dirs[0], "CAM1")
    date_str = selected_date.strftime("%Y-%m-%d")
    image_options = [
        os.path.join(dir, file) for file in os.listdir(dir) if file.endswith("bmp")
    ]
    num_option = [int(img[-14:-4]) for img in image_options]
    image_options = [img for _, img in sorted(zip(num_option, image_options))]
    num_option = sorted(num_option)
    # --- Find analysis CSV for that date ---
    csv_filename = f"{date_str}.csv"
    save_dir = os.path.join(BASEDIR, "analysis")
    csv_path = os.path.join(save_dir, csv_filename)

    if not os.path.exists(csv_path):
        st.warning(f"No analysis CSV found for {date_str}.")
        return

    # --- Load analysis CSV ---
    df = pd.read_csv(csv_path)
    images = df["image_file"].unique()
    st.write(f"Found {len(images)} analyzed images for {date_str}.")

    # --- User selects images ---
    st.write("### Select images to analyze")
    image_numbers = [int(f[-14:-4]) for f in images]

    if "selected_numbers" not in st.session_state:
        st.session_state.selected_numbers = []

    selected_numbers = []

    # Rolling window / scrollable container
    with st.expander("Select images (scrollable)"):
        n_cols_chk = 10
        cols_chk = st.columns(n_cols_chk)
        for idx, (num, f) in enumerate(zip(image_numbers, images)):
            col = cols_chk[idx % n_cols_chk]
            checked = num in st.session_state.selected_numbers
            if col.checkbox(f"{num}", value=checked, key=f"chk_{num}"):
                selected_numbers.append(num)

    st.session_state.selected_numbers = selected_numbers
    selected_images = [f for f, num in zip(images, image_numbers) if num in selected_numbers]

    if not selected_images:
        st.warning("No images selected.")
        return

    # --- Option to use diff image ---
    use_diff = st.checkbox("Display diff image instead of original", value=False)

    # --- Display images in rows of 4 ---
    n_cols_disp = 4
    for i in range(0, len(selected_images), n_cols_disp):
        cols = st.columns(n_cols_disp)
        for j, img_file in enumerate(selected_images[i:i+n_cols_disp]):
            img_path = os.path.join(dir, img_file)
            img_df = df[df["image_file"] == img_file]
            crop = [df["crop_top"].values[0] ,df["crop_bottom"].values[0] , df["crop_left"].values[0] ,df["crop_right"].values[0] ]
            if not os.path.exists(img_path):
                st.warning(f"Image {img_file} not found!")
                continue

            # Determine which image to load
            if use_diff:
                path_ref = image_path(image_options, num_option, selected_numbers[i]-1)
                im_diff = image_utils.get_im_diff(img_path, path_ref, crop)
                img = Image.fromarray(im_diff.astype(np.uint8)).convert("RGB")

            else:
                img = Image.open(img_path).convert("RGB")
                img = img.crop((crop[2], crop[0], crop[3], crop[1]))
            draw = ImageDraw.Draw(img)

            # Overlay detected circles

            for _, row in img_df.iterrows():
                x, y, r = int(row["x"]), int(row["y"]), int(row["radius"])
                draw.ellipse([x - r, y - r, x + r, y + r], outline=(255, 0, 0), width=25)

            with cols[j]:
                st.image(img, caption=f"{img_file[-14:-4]}", use_container_width=True)
                st.dataframe(img_df[["x", "y", "radius","accum"]].reset_index(drop=True), hide_index=True)

page3()
