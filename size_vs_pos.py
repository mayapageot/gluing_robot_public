import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import griddata

df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/240607_104955/CAM1/analysis_2.csv")
df = df[df["diameter"] < 400]
# df_b = df[(df["num"]<218)&(df["num"]>119)]

# df_b = df[(df["num"]<319)&(df["num"]>218)]
# df_b = df[(df["num"]<422)&(df["num"]>321)]
for df_b in [df[(df["num"] < 218) & (df["num"] > 119)], df[(df["num"] < 319) & (df["num"] > 218)],
             df[(df["num"] < 422) & (df["num"] > 321)]]:
    #print(df_b["diameter"].mean())
    #print(df_b["diameter"].std())
    maz_z = df_b["diameter"].max()
    x, y, z = df_b["center_x"], df_b["center_y"], df_b["diameter"]/maz_z
    grid_x, grid_y = np.mgrid[x.min():x.max():100j, y.min():y.max():100j]
    print(grid_x.max(), grid_y.max(),grid_x.min(), grid_y.min())
    # Interpolate data
    grid_z = griddata((x, y), z, (grid_x, grid_y), method = 'cubic')
    fig, ax = plt.subplots(figsize = (8, 6))
    im = ax.imshow(grid_z.T, extent = (0, 1, 0, 1), origin = 'lower', cmap = 'viridis')
    fig.colorbar(im, label = 'Intensity')
    # plt.scatter(x, y, c = 'red', s = 10)  # Optional: to plot original points
    #print(df_b["diameter"]/df_b["diameter"].max())
    print(griddata(df_b.loc[:, ["center_x","center_y"]], df_b["diameter"]/df_b["diameter"].max(),([3000.],[2000.])))
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_title('2D Interpolated Heatmap' + str(df_b["num"].min()))
    """plt.figure(figsize=(8, 6))
    plt.scatter(df_b["center_x"],df_b["center_y"], c=df_b["diameter"], cmap='viridis')

    plt.colorbar(label='Intensity')
    plt.xlabel('X axis')
    plt.ylabel('Y axis')
    plt.title('2D Heatmap')
    plt.show()"""
plt.show()
