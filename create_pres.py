import pandas as pd
from pptx import Presentation
from pptx.util import Inches

def create_table(n_col,n_line,slide):
    x, y, cx, cy = Inches(1), Inches(2), Inches(4), Inches(1.5)
    shape = slide.shapes.add_table(n_col,n_line, x, y, cx, cy)
    tbl = shape._element.graphic.graphicData.tbl
    style_id = '{5940675A-B579-460E-94D1-54222C63F5DA}'
    tbl[0][-1].text = style_id
    table = shape.table
    col_w = []
    cols = table.columns
    for colno in range(n_line):
        cols[colno].width =  Inches(1.5) if colno!=0 else Inches(2.5)
    return table
prs = Presentation()
df = pd.read_csv("/local/home/mp274748/Documents/data/Glue/240716_heaters/all_infos.csv")
df = df.sort_values("filename")
for filename in df["filename"].unique():
    df_b = df.loc[df["filename"] == filename].sort_values("position")
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    for shape in slide.shapes:
        if shape.has_text_frame:
            text_frame = shape.text_frame
            p = text_frame.paragraphs[0]
            crys = df_b["Crystal"].unique()
            crys = crys[0] if type( crys[0])==str else crys[1]
            chip = df_b["Chip"].unique()
            chip = chip[0] if type(chip[0]) == str else chip[1]
            p.text = crys + " / " + chip
    table = create_table(6,5,slide)
    table.cell(0,0).text = "Filename"
    table.cell(0, 1).text = "Crystal"
    table.cell(0, 2).text = "Chip"
    table.cell(0,3).text = "Position"
    table.cell(0,4).text = "Radius"
    cell = table.cell(1,0)
    other_cell = table.cell(5,0)
    cell.merge(other_cell)
    cell.text = filename
    for i,col in enumerate(["Crystal", "Chip","position","corrected_diameter_in_um"]):
        for j, index in enumerate(df_b.index):
            cell = table.cell(j+1,i+1)
            try:
                cell.text = df.loc[index,col]  if type(df.loc[index,col]) == str else "" if pd.isna(df_b.loc[index,col]) else "{:.2f}".format(df.loc[index,col])
            except:
                cell.text = ""
    cell = table.cell(1, 1)
    other_cell = table.cell(5, 1)
    cell.merge(other_cell)
    cell = table.cell(1, 2)
    other_cell = table.cell(5, 2)
    cell.merge(other_cell)
    #pic = slide.shapes.add_picture("/local/home/mp274748/Documents/data/Glue/240716_heaters/"+filename, Inches(1), Inches(4.5),Inches(3))
    #pic.crop_top,pic.crop_bottom,pic.crop_left,pic.crop_right= 0.1,0.2,0.15,0.2

prs.save('/local/home/mp274748/Documents/data/Glue/test.pptx')