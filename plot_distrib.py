import pandas as pd
from utility import plots

df = pd.read_csv(r"C:\GluingRobotData\Data_gluing\2024_02_19\192.168.200.2\SD2\cv-x\image\SD1_010\240716_093510\CAM1\analysis_2.csv")
print(df["filename"].apply(lambda x: int(x[-14:-4])))
sub_df = df.loc[(df["filename"].apply(lambda x: int(x[-14:-4]))>96)&(df["diameter"]>230)&(df["diameter"]<300)]

plots.slidded_bin_histogram(sub_df["diameter"])
print(sub_df["diameter"].mean(),sub_df["diameter"].std())
plots.show()