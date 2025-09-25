"""
Session state management utilities for glue analysis app.
"""
import streamlit as st
from datetime import date
from config.settings import BASEDIR
import os
import pandas as pd
import time
import json
import numpy as np
def initial_state_value(key,default_val):
    if key not in st.session_state:
        st.session_state[key] = default_val

def save_session_state(df):

    save_dir = os.path.join(BASEDIR, "analysis")
    os.makedirs(save_dir, exist_ok = True)
    selected_date = df["selected_date"].values[0]
    filename = os.path.join(save_dir, f"{selected_date}_session_state.csv")

    # --- Relevant dtypes and columns ---
    dtypes = {
        "selected_date": str,
        "selected_num": int,
        "downsample_factor": int,
        "pxl_range": int,
        "n_dots": int,
        "selected_num_ref": int,
        "fit_bool": bool,
        "fill_bool": bool,
        "use_img_bool": bool,
        "high_threshold": int,
        "pxl_accuracy": int,
        "r_guess": int,
        "contour_bool": bool,
        "crop": str,
    }

    # --- Keep only relevant columns ---
    df_to_save = pd.DataFrame({col: df.get(col, pd.Series([None])) for col in dtypes.keys()})
    df_to_save = df_to_save.astype(dtypes)

    # --- Set multi-index for merging/updating ---
    df_to_save.set_index(["selected_date", "selected_num"], inplace=True)
    if os.path.exists(filename):
        # --- Load existing ---
        existing_df = pd.read_csv(filename).set_index(["selected_date", "selected_num"])

        # --- Combine existing + new, overwrite duplicates ---
        combined_df = pd.concat([existing_df, df_to_save])
        combined_df = combined_df[~combined_df.index.duplicated(keep="last")]

        # --- Save back ---
        combined_df.to_csv(filename)
        st.write("Session state saved/updated.")
    else:
        # --- No existing file, just save ---
        df_to_save.to_csv(filename)
        st.write("Session state saved.")

def load_session_state():
    if "selected_num" not in st.session_state:
        return None
    save_dir = os.path.join(BASEDIR, "analysis")
    os.makedirs(save_dir, exist_ok = True)
    selected_date, selected_num = st.session_state.selected_date, st.session_state.selected_num
    filename = os.path.join(save_dir, f"{selected_date}_session_state.csv")

    if os.path.exists(filename):
        dtypes = {
            "selected_date": str, "selected_num": int, "downsample_factor": int,
            "pxl_range": int, "n_dots": int, "selected_num_ref": int,
            "fit_bool": bool, "fill_bool": bool, "use_img_bool": bool,
            "high_threshold": int, "pxl_accuracy": int, "r_guess": str,
            "contour_bool": bool, "crop": str,  # crop stays as string in CSV
        }
        df = pd.read_csv(filename, dtype = {k: v for k, v in dtypes.items() if k != "crop"})
        df = df.set_index(["selected_date", "selected_num"])

        try:
            row = df.loc[(str(selected_date), int(selected_num))]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            for key, value in row.items():
                # if key == "crop":
                #     try:
                #         st.session_state["crop"] = json.loads(value) if isinstance(value, str) else value
                #     except Exception:
                #         st.session_state["crop"] = [600, 2610, 1370, 3520]  # fallback default
                #
                # else:
                st.session_state[key] = value.item() if isinstance(value, np.generic) else value
        except KeyError:
            print(f"No entry for ({selected_date}, {selected_num}) in {filename}")