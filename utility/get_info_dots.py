import numpy as np
import pandas as pd
df = pd.read_csv("/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T212046Z-001/analysis_2.csv")
#df = pd.read_csv("/local/home/mp274748/Documents/glue_analysis/data/BDPT_v2/drive-download-20240407T215728Z-001/analysis_2.csv")
def get_pic_number(df):
    return df["filename"].apply(lambda x : int(x[-14:-4]))

pos_pic = {"m": 0, "tl": 1, "tr": 2, "br": 3, "bl": 4}
def sel_pos_pic(df,pos = "m"):
    df_1 = df.groupby("module").apply(
        lambda x: x.groupby('position').apply(lambda x: x.iloc[pos_pic[pos]], include_groups = False), include_groups = False)
    return df_1
def sel_pos_dot(df,pos="m"):
    df_1 = df.iloc[df.index.get_level_values('position') == pos]
    return df_1

def get_dif_btw_dots(df):
    dif_to_center = df.groupby("module").apply(lambda x:x.groupby('position')
                                               .apply(lambda x : x["diameter"]-x["diameter"].iloc[0],include_groups=False),
                                               include_groups=False)
    for pos in df["position"].unique():
        j =pos_pic[pos]
        A = dif_to_center.loc[:,pos].to_numpy().reshape(-1,5)
        A[np.abs(A)>20] = np.nan
        B = np.nanstd(A,axis=0)
        C = np.nanmean(A,axis=0)
        print(pos,C[j],"+-",B[j])


def glue_dots_analysis(df):
   data = df["diameter"].to_numpy()
   time = df["filename"].apply(lambda x : hhmmss_to_seconds(os.path.split(x)[1][7:13])/60-689-40).to_numpy()
   plt.scatter(time, data, s = 20)
   plt.xlabel("time in minutes")
   plt.ylabel("radius size in pixel")
   plt.show()