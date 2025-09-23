import cv2
import numpy as np
import pandas as pd
import os
basedir = "/media/mp274748/Transcend/data/Glue_Files/"
filename = "session_state.csv"
filename = os.path.join(basedir,filename)
existing_df = pd.read_csv(filename)
for col in existing_df.columns:
    if "bool" in col:
        existing_df[col] = existing_df[col].astype(bool)
    elif "date" in col:
        existing_df[col] = existing_df[col].astype(str)
    elif "selected_num" in col:
        existing_df[col] = existing_df[col].astype(str)
    else:
        existing_df[col] = existing_df[col].astype(int)
df = existing_df.copy()
df["selected_num"]="5"
existing_df = existing_df.set_index(["selected_date", "selected_num"])
df = df.set_index(["selected_date", "selected_num"])
print(df.index[0])
print(existing_df)
existing_df.loc[df.index[0],:]=df.iloc[0]
print(existing_df)