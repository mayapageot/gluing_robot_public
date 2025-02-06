import numpy as np
from pptx import Presentation
from pptx.util import Inches
import pandas as pd
from pptx import Presentation
from pptx.util import Inches
from PIL import Image
import io

def resize_image(input_path, new_width):
    with Image.open(input_path) as img:
        # Calculate the new height to maintain the aspect ratio
        width_percent = (new_width / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))
        # Resize image
        img = img.resize((new_width, new_height),  Image.Resampling.LANCZOS)

        # Save the resized image to a byte stream
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format = 'PNG')
        img_byte_arr.seek(0)  # Move to the start of the byte stream
        return img_byte_arr
# Create a presentation object
prs = Presentation()
prs.slide_width = Inches(16)
prs.slide_height = Inches(9)
# Add a title slide
slide_layout = prs.slide_layouts[0]  # Layout for title slide
slide = prs.slides.add_slide(slide_layout)
title = slide.shapes.title
subtitle = slide.placeholders[1]

title.text = "Ulysse test Gluing with UV620/UV645 and LUMI NTD"
subtitle.text = "06/02/2025"


path = "/media/mp274748/Transcend/data/Glue_Files/250129_143502/CAM1/data.csv"
df1 = pd.read_csv(path)
path = "/media/mp274748/Transcend/data/Glue_Files/250130_112657/CAM1/data.csv"
df2 = pd.read_csv(path)
path = "/media/mp274748/Transcend/data/Glue_Files/250204_112143/CAM1/data.csv"
df3 = pd.read_csv(path)
df = pd.concat((df1,df2,df3))
# path = "/media/mp274748/Transcend/data/Glue_Files/250206_110255/CAM1/data.csv"
# df = pd.read_csv(path)

df = df.set_index("file")
df = df.loc[pd.notnull(df["support_name"])]
for Chip_name in df["Chip_name"].unique():
    sub_df_1 = df[df["Chip_name"]==Chip_name]
    slide_layout = prs.slide_layouts[1]  # Layout for title and content
    slide = prs.slides.add_slide(slide_layout)
    for i,idx in enumerate(sub_df_1.index):
        sub_df = sub_df_1.loc[idx]
        if isinstance(sub_df, pd.Series):
            sub_df = sub_df.to_frame().T
        if "dot_nums" not in sub_df.columns:
            sub_df["dot_nums"] = np.zeros(len(sub_df))
        sub_df = sub_df.set_index(["dot_nums"])
        title = slide.shapes.title
        title.text =sub_df.loc[sub_df.index[0],"Chip"] +" "+ str(sub_df.loc[sub_df.index[0],"Chip_name"]) + " on " + sub_df.loc[sub_df.index[0],"support_name"]
        img_path = sub_df.loc[sub_df.index[0],"file_path"]
        resized_image_stream = resize_image(img_path, 800)
        slide.shapes.add_picture(resized_image_stream, Inches(0.5)+ i*Inches(5.5), Inches(1.3), Inches(5), Inches(4))
        table = slide.shapes.add_table(len(sub_df)+1, 2, Inches(0.5) + i*Inches(5.5), Inches(5.75), Inches(5), Inches(2)).table
        table.cell(0, 0).text = "Radius"
        table.cell(0, 1).text = "fit\nAccuracy"
        for j, dot_num in enumerate(sub_df.index):
            table.cell(int(j)+1, 0).text = "{:.0f}".format(sub_df.loc[dot_num,"radius"])
            table.cell(int(j)+1, 1).text = "{:.2f}".format(sub_df.loc[dot_num,"accum"])
        textbox = slide.shapes.add_textbox(Inches(0.5)+ i*Inches(5.5), Inches(5.25), Inches(5), Inches(1.5))
        text_frame = textbox.text_frame
        text_frame.text = idx
        break
# Save the presentation
prs.save('/media/mp274748/Transcend/data/Glue_Files/Ulysse_test_02-2025.pptx')
# prs.save('/media/mp274748/Transcend/data/Glue_Files/CROSS_gluing_06_02_2025.pptx')
print("Presentation created successfully!")
