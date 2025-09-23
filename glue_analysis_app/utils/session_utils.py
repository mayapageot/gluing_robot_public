"""
Session state management utilities for glue analysis app.
"""
import os
import pandas as pd
import streamlit as st
from config.settings import BASEDIR
import time
import json
import numpy as np
def initial_state_value(key,default_val):
    if key not in st.session_state:
        st.session_state[key] = default_val


def save_session_state(df, filename = "session_state.csv"):
    filename = os.path.join(BASEDIR, filename)

    # Always add crop as JSON string
    if "crop" in st.session_state:
        df["crop"] = [json.dumps(st.session_state.crop)]
    else:
        df["crop"] = [json.dumps([600, 2610, 1370, 3520])]  # fallback default

    if os.path.exists(filename):
        # Load the existing DataFrame
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
            "countour_bool": bool,
            "crop": str,  # stored as JSON string
        }
        existing_df = pd.read_csv(filename, dtype = dtypes)
        existing_df = existing_df.set_index(["selected_date", "selected_num"])

        # Update or insert row
        existing_df.loc[df.index[0], :] = df.iloc[0]

        # Cast types back (except crop stays str)
        dtypes.pop("selected_date")
        dtypes.pop("selected_num")
        existing_df = existing_df.astype(dtypes)

        existing_df.to_csv(filename)
        st.write("Session state saved/updated.")
    else:
        df.to_csv(filename)
        st.write("Session state saved.")


def load_session_state(filename = "session_state.csv"):
    if "selected_num" not in st.session_state:
        return None

    selected_date, selected_num = st.session_state.selected_date, st.session_state.selected_num
    filename = os.path.join(BASEDIR, filename)

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
                if key == "crop":
                    try:
                        st.session_state["crop"] = json.loads(value) if isinstance(value, str) else value
                    except Exception:
                        st.session_state["crop"] = [600, 2610, 1370, 3520]  # fallback default

                else:
                    st.session_state[key] = value.item() if isinstance(value, np.generic) else value
        except KeyError:
            print(f"No entry for ({selected_date}, {selected_num}) in {filename}")