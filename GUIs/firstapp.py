import streamlit as st
from datetime import date
from PIL import Image
import cv2
import os
import pandas as pd
import numpy as np
from streamlit_drawable_canvas import st_canvas
from skimage.transform import hough_circle, hough_circle_peaks,hough_ellipse
from skimage.measure import block_reduce
from skimage.measure import find_contours
from skimage.feature import canny
from skimage.morphology import dilation, disk
from joblib import Parallel, delayed
import json
import time
basedir = "/media/mp274748/Transcend/data/Glue_Files/"

rect_obj = {
    "type": "rect",
    "version": "4.4.0",
    "originX": "left",
    "originY": "top",
    "left": 72,
    "top": 24,
    "width": 133,
    "height": 135,
    "fill": "rgba(255, 0, 0, 0.1)",
    "stroke": "rgba(255, 0, 0, 1)",
    "strokeWidth": 3,
    "strokeDashArray": None,
    "strokeLineCap": "butt",
    "strokeDashOffset": 0,
    "strokeLineJoin": "miter",
    "strokeUniform": True,
    "strokeMiterLimit": 4,
    "scaleX": 1,
    "scaleY": 1,
    "angle": 0,
    "flipX": False,
    "flipY": False,
    "opacity": 1,
    "shadow": None,
    "visible": True,
    "backgroundColor": "",
    "fillRule": "nonzero",
    "paintFirst": "fill",
    "globalCompositeOperation": "source-over",
    "skewX": 0,
    "skewY": 0,
    "rx": 0,
    "ry": 0
}

def image_path(image_options,num_option,num):
    return image_options[num_option.index(num)]

def concat_large_contours(edge_image, length_threshold):
    contours = find_contours(edge_image, 0.5)

    # Filter and concatenate all contours larger than the threshold
    large_contours = [contour for contour in contours if len(contour) > length_threshold]

    if len(large_contours) == 0:
        return np.empty((0, 2))  # No large contours, return empty array

    # Concatenate all selected contours into one big array
    concatenated_contour = np.concatenate(large_contours, axis=0)

    return concatenated_contour
def orientation_of_consecutive_vectors(x, y):
    # Calculate the cross product between consecutive vectors
    x_start = np.append(x[1:],x[0])
    y_start = np.append(y[1:],y[0])
    cross_products = x * y_start - y * x_start

    # Determine orientation based on the sign of the cross product
    orientation = cross_products > 0
    return orientation
def get_radius(x,y):
    return (x.max()-x.min()+y.max()-y.min())/2

def fill_gap(contour):
    x_contour, y_contour = contour[:, 1], contour[:, 0]
    orientation = orientation_of_consecutive_vectors(x_contour - x_contour.mean(), y_contour - y_contour.mean())
    np.min(x_contour[orientation])
    r1 = get_radius(x_contour[orientation], y_contour[orientation])
    r2 = get_radius(x_contour[~orientation], y_contour[~orientation])
    if r1<r2:
        orientation=~orientation
    x_contour = x_contour[orientation]
    y_contour = y_contour[orientation]
    center_x = np.mean(x_contour)
    center_y = np.mean(y_contour)
    angles = np.arctan2(y_contour - center_y, x_contour - center_x)
    sorted_indices = np.argsort(angles)
    existing_x_sorted = x_contour[sorted_indices]
    existing_y_sorted = y_contour[sorted_indices]
    angles_sorted = angles[sorted_indices]
    angle_diff = np.abs(np.append(angles_sorted[1:], angles_sorted[0]+2*np.pi) - angles_sorted)
    gap_length = 5/np.mean(1/angle_diff)
    gap_indices = np.where(angle_diff > gap_length)[0]
    for gap_indice in gap_indices:
        start_index = gap_indice
        try:
            radius = np.mean(np.sqrt((existing_x_sorted[start_index - 4] - center_x) ** 2 + (
                    existing_y_sorted[start_index - 4] - center_y) ** 2))
        except:
            radius = np.mean(np.sqrt(
                (existing_x_sorted[start_index] - center_x) ** 2 + (existing_y_sorted[start_index] - center_y) ** 2))
        if gap_indice + 1 < len(angles_sorted):
            end_index = gap_indice + 1
            angle_interp = np.linspace(angles_sorted[start_index], angles_sorted[end_index], 1000)
        else:
            end_index = 0
            angle_interp = np.linspace(angles_sorted[start_index], angles_sorted[end_index] + 2 * np.pi, 1000)
        interp_x = radius * np.cos(angle_interp) + center_x
        interp_y = radius * np.sin(angle_interp) + center_y
        existing_x_sorted = np.insert(existing_x_sorted, start_index, interp_x)
        existing_y_sorted = np.insert(existing_y_sorted, start_index, interp_y)
    c = np.empty((existing_x_sorted.shape[0], 1, 2), dtype = np.float32)
    c[:, 0, 0] = existing_x_sorted
    c[:, 0, 1] = existing_y_sorted
    return c
@st.cache_data
def get_im_diff(path, path_ref, crop = None):
    imag = cv2.imread(path)
    if crop is None:
        crop = [0, imag.shape[0], 0, imag.shape[1]]
    # crop, center_chip = get_chip(path_ref,crop)
    imag = imag[crop[0]: crop[1], crop[2]: crop[3]]
    im = np.array(cv2.cvtColor(imag, cv2.COLOR_BGR2GRAY), dtype = np.int32)
    im_ref = np.array(cv2.cvtColor(cv2.imread(path_ref), cv2.COLOR_BGR2GRAY), dtype = np.int32)
    im_ref = im_ref[crop[0]: crop[1], crop[2]: crop[3]]
    im_diff = np.abs(im_ref - im)
    return cv2.normalize(im_diff, None, 0, 255, cv2.NORM_MINMAX)
@st.cache_data
def get_edges(image,high_threshold,downsample_factor=10):
    edges = canny(image, sigma = 5, low_threshold = 5, high_threshold = high_threshold)
    downsampled_image = block_reduce(edges, (downsample_factor, downsample_factor), np.max)
    downsampled_image = dilation(downsampled_image, disk(1))
    return downsampled_image
@st.cache_data
def merge_circle(edges,n_dots,r_guess,fill_bool=False):
    contours = find_contours(edges)
    contours = sorted(contours, key = len, reverse = True)
    # [len(c) for c in contours]
    new_edges = np.zeros_like(edges,dtype=np.uint8)
    cxs = []
    cys = []
    sel_contour = []
    for contour in contours:
        _, tot_radius = cv2.minEnclosingCircle(contour.astype(int))
        if tot_radius < r_guess * 0.7:
            continue
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = np.mean(contour[:,1])#int(M['m10'] / M['m00'])
            cy = np.mean(contour[:,0])#int(M['m01'] / M['m00'])
            is_near = False
            for cx_prev,cy_prev in zip(cxs,cys):
                if (cx-cx_prev)**2+(cy-cy_prev)**2<r_guess/2:
                    is_near = True
                    continue
            if is_near:
                continue
            else:
                if fill_bool:
                    contour = fill_gap(contour)
                else:
                    contour = contour[:, ::-1]
                cv2.drawContours(new_edges, [contour.astype(int)], contourIdx = -1, color = 255, thickness = 2)
                cxs.append(cx)
                cys.append(cy)
                sel_contour.append(contour)
        if len(cxs)>=n_dots:
            break
    return new_edges.astype(bool), sel_contour
@st.cache_data
def get_circle(edges, r_guess=400, n_dots=1,pxl_range=10,pxl_accuracy=5):
    hough_radii = np.arange(r_guess - pxl_range, r_guess + pxl_range, pxl_accuracy)
    hough_results = np.concat(Parallel(n_jobs = -1)(delayed(hough_circle)(edges, r) for r in hough_radii))
    min_dist = r_guess
    accums, cx, cy, radii = hough_circle_peaks(hough_results, hough_radii, total_num_peaks = n_dots,
                                               min_xdistance = min_dist, min_ydistance = min_dist)
    return accums, cx, cy, radii

@st.cache_data
def get_elipse(edges, r_guess=400, n_dots=1,pxl_range=10,pxl_accuracy=5):
    contour = find_contours(edges)
    contour = max(contour, key = lambda c: len(c)).astype(int)
    area = [cv2.contourArea(contour)]
    hough_results = hough_ellipse(edges, accuracy=pxl_accuracy, threshold=1, min_size=r_guess-pxl_range, max_size=r_guess+pxl_range)
    hough_results.sort(order = 'accumulator')
    hough_results
    accums, cx, cy, a, b = hough_results[-n_dots:]
    return accums, cx, cy, a, b

def get_dot_pos(df):
    if len(df)==1:
        df["dot_pos"]="middle"
    if len(df)==5:
        idx = df.index
        df["dot_pos"] = ["m"]*5
        idx_tl = idx[np.argmax(-df["center_x"]**2-df["center_y"]**2)]
        idx_tr = idx[np.argmax(-df["center_x"]**2+df["center_y"]**2)]
        idx_bl = idx[np.argmax(df["center_x"]**2-df["center_y"]**2)]
        idx_br = idx[np.argmax(df["center_x"]**2+df["center_y"]**2)]
        df.loc[[idx_tl,idx_tr,idx_bl,idx_br],"dot_pos"] = ["top left","top right","bottom left","bottom right"]
    return df

# Function to save session state DataFrame with overwriting
def save_session_state(df, filename = "session_state.csv"):
    filename = os.path.join(basedir,filename)
    if os.path.exists(filename):
        # Load the existing DataFrame
        dtypes = {"selected_date":str,"selected_num":int,"downsample_factor":int,"pxl_range":int,"n_dots":int,"selected_num_ref":int,"fit_bool":bool,
                  "fill_bool":bool,"use_img_bool":bool,
                  "high_threshold":int,"pxl_accuracy":int,"r_guess":int,"countour_bool":bool}
        existing_df = pd.read_csv(filename,dtype=dtypes)
        existing_df = existing_df.set_index(["selected_date", "selected_num"])
        existing_df.loc[df.index[0], :] = df.iloc[0]
        dtypes.pop("selected_date")
        dtypes.pop("selected_num")
        existing_df = existing_df.astype(dtypes)
        existing_df.to_csv(filename)

        st.write("Session state saved/updated.")
    else:
        df.to_csv(filename)
        st.write("Session state saved.")


def load_session_state(filename = "session_state.csv"):
    if "selected_num" in st.session_state:
        selected_date, selected_num = st.session_state.selected_date,st.session_state.selected_num
    else :
        return None
    filename = os.path.join(basedir, filename)
    if os.path.exists(filename):
        dtypes = {"selected_date": str, "selected_num": int, "downsample_factor": int, "pxl_range": int, "n_dots": int,
                  "selected_num_ref": int, "fit_bool": bool,
                  "fill_bool": bool, "use_img_bool": bool,
                  "high_threshold": int, "pxl_accuracy": int, "r_guess": int, "countour_bool": bool}
        df = pd.read_csv(filename, dtype = dtypes)
        df = df.set_index(["selected_date", "selected_num"])
        try :
            row = df.loc[(str(selected_date),int(selected_num)), :]
            for key, value in row.items():
                st.session_state[key] = value
                st.session_state[key]
            time.sleep(0.5)
        except KeyError:
            pass
def initial_state_value(key,default_val):
    if key not in st.session_state:
        st.session_state[key] = default_val
def save_analysis(df,filename = "analysis.csv"):
    pass
def page1():
    st.set_page_config(layout="centered")
    selected_date = st.sidebar.date_input("Select a date", date.fromisoformat('2025-02-06'),key="selected_date")

    list_dirs = [dir for dir in  os.listdir(basedir) if selected_date.strftime("%y%m%d")==dir[:6]]
    if len(list_dirs)>0:
        dir = os.path.join(basedir,list_dirs[0],"CAM1")
        image_options =[os.path.join(dir,file) for i,file in enumerate(os.listdir(dir)) if file[-3:]=="bmp"]
        num_option = [int(image_option[-14:-4]) for image_option in image_options]
        selected_num = st.sidebar.selectbox("Select a image number:", num_option,1,key = "selected_num")
        # load_button = st.sidebar.button("load_prev")
        # if load_button:
        #     load_session_state()
        st.session_state
        delta_ref = 1 #int(st.sidebar.text_input("Delta between Glue and Ref images", value="1",key="delta_ref"))
        initial_state_value("selected_num_ref", 1)
        st.session_state.selected_num_ref
        a = num_option.index(st.session_state.selected_num_ref)
        a
        selected_num_ref = st.sidebar.selectbox("Select a ref number:", num_option,num_option.index(st.session_state.selected_num_ref))
        initial_state_value("high_threshold", 30)
        high_threshold = st.sidebar.slider('Edge high_threshold', 10, 100, step=1,value=st.session_state.high_threshold)
        initial_state_value("downsample_factor", 7)
        downsample_factor = st.sidebar.slider('downsample factor', 1, 20, step=1, value=int(st.session_state.downsample_factor))
        initial_state_value("fit_bool", False)
        fit_bool = st.sidebar.checkbox('Fit circle', value=st.session_state.fit_bool)
        initial_state_value("use_img_bool", False)
        use_img_bool = st.sidebar.checkbox('Use image guess', value=st.session_state.use_img_bool)
        initial_state_value("countour_bool", False)
        countour_bool = st.sidebar.checkbox('contour filter (necessary for Area)', value=st.session_state.countour_bool)
        initial_state_value("fill_bool", False)
        fill_bool = st.sidebar.checkbox('fill circle', value=st.session_state.fill_bool)
        initial_state_value("r_guess", 500)
        r_guess = int(st.sidebar.text_input("r_guess:",st.session_state.r_guess))
        initial_state_value("n_dots", 1)
        n_dots_sel = [i for i in range(1,10)]
        n_dots = st.sidebar.selectbox("n_dots:", n_dots_sel, n_dots_sel.index(st.session_state.n_dots))
        pxl_range_list = [i for i in range(5,30,5)]
        initial_state_value("pxl_range", pxl_range_list[3])
        pxl_range = st.sidebar.selectbox("pxl_range:", pxl_range_list,pxl_range_list.index(st.session_state.pxl_range))
        pxl_accuracy_list = [i for i in range(1,9)]
        initial_state_value("pxl_accuracy", pxl_accuracy_list[0])
        pxl_accuracy = st.sidebar.selectbox("pxl_accuracy:", pxl_accuracy_list,pxl_accuracy_list.index(st.session_state.pxl_accuracy))

        left, right = st.columns(2, vertical_alignment="center")
        path_glue = image_path(image_options,num_option,selected_num)
        path_ref = image_path(image_options, num_option, selected_num_ref)
        w,h = 5104, 4092
        with left:
            with open(basedir+"test.json", 'r') as json_file:
                json_data = json.load(json_file)
            factor_main_image = 300/w
            canvas_main_image = st_canvas(
                fill_color = "rgba(255, 0, 0, 0.1)",  # Fixed fill color with some opacity
                stroke_width = 3,
                stroke_color = "rgba(255, 0, 0, 1)",
                background_color = "#eee",
                background_image = Image.open(path_glue),
                update_streamlit = True,
                width = int(w*factor_main_image),
                height = int(h * factor_main_image),
                drawing_mode = "transform",
                point_display_radius = 0,
                key="main_image",
                initial_drawing = json_data
            )
        if canvas_main_image.json_data is not None:
            with right:
                st.image(path_ref, caption = "im Diff", width = 300)
            rect_crop = canvas_main_image.json_data["objects"]
            if len(rect_crop)>0:
                rect_crop = rect_crop[0]
                crop = [rect_crop["top"],rect_crop["top"]+rect_crop["width"],rect_crop["left"],rect_crop["left"]+rect_crop["width"]]
                crop = [int(c / factor_main_image) for c in crop]
            else:
                crop = [600, 2610, 1370, 3520]
            im_diff = get_im_diff(path_glue, path_ref,crop)
            left, middle, right = st.columns(3, vertical_alignment="center")
            with left:
                ""
                ""
                ""
                im = st.image(im_diff, width = 200)
            edge = get_edges(im_diff,high_threshold,downsample_factor)
            if countour_bool:
                edge, contours = merge_circle(edge, n_dots, r_guess//downsample_factor,fill_bool)
            factor = 200/edge.shape[1]
            with middle:
                drawing_mode = st.radio(
                    "Mode:", ["Draw", "Move"], horizontal = True, label_visibility = "hidden"
                )
                canvas_mode = "circle" if drawing_mode == "Draw" else "transform"
                canvas_result = st_canvas(
                    fill_color = "rgba(255, 0, 0, 0.1)",  # Fixed fill color with some opacity
                    stroke_width = 3,
                    stroke_color = "rgba(255, 0, 0, 1)",
                    background_color = "#eee",
                    background_image = Image.fromarray((edge*255).astype(np.uint8)) ,
                    update_streamlit = False,
                    width = 200,
                    height = 200,
                    drawing_mode = canvas_mode,
                    point_display_radius = 0,
                    key = "circle_draw"
                )
            print(canvas_result.json_data["objects"])
            objects = pd.DataFrame({"center_x":[],"center_y":[],"radius_guess":[],"dot_pos":[]})
            if canvas_result.json_data["objects"] is not None :
                if len(canvas_result.json_data["objects"])>0:
                    objects = pd.json_normalize(st.session_state.canvas_result.json_data["objects"])  # need to convert obj to str because PyArrow
                    for col in objects.select_dtypes(include = ['object']).columns:
                        objects[col] = objects[col].astype("str")
                    objects["angle_rad"] = np.radians(objects["angle"])
                    cos = np.cos(objects["angle_rad"])
                    sin = np.sin(objects["angle_rad"])
                    objects["x"] = ((objects["left"] + cos * objects["radius"] )/factor).astype(int)
                    objects["y"] = ((objects["top"] +  sin * objects["radius"] )/factor).astype(int)
                    objects["radius"] = (objects["radius"]/factor).astype(int)
                    objects["center_x"] =  objects["x"] *downsample_factor
                    objects["center_y"] = objects["y"] *downsample_factor
                    objects["radius_guess"] = objects["radius"]*downsample_factor
            dic = dict(center_x = [], center_y = [], radius = [], accum = [],dot_pos=[])
            df = pd.DataFrame(dic)
            if fit_bool:
                im_diff = np.clip(im_diff, 0, 255).astype(np.uint8)
                im = cv2.cvtColor(im_diff,cv2.COLOR_GRAY2RGB)
                if use_img_bool and len(canvas_result.json_data["objects"])>0:
                    accums, cx, cy, radii = np.array([]),np.array([],dtype=int),np.array([],dtype=int),np.array([],dtype=int)
                    for index, row in objects.iterrows():
                        centerx ,centery, r = row["x"], row["y"], row["radius"]
                        min_y, max_y = np.max([centery-r-pxl_range,0]),np.min([centery+r+pxl_range,edge.shape[0]])
                        min_x, max_x = np.max([centerx - r - pxl_range, 0]), np.min([centerx + r + pxl_range, edge.shape[1]])
                        im_dot = edge[min_y:max_y,min_x: max_x]
                        accum, x, y, radius = get_circle(im_dot, r_guess = int(row["radius"]), n_dots = 1, pxl_range = pxl_range,
                                                           pxl_accuracy = pxl_accuracy)

                        accums, cx, cy, radii = np.concat((accums,accum)), np.concat((cx,x+min_x)), np.concat((cy,y+min_y)), np.concat((radii,radius))
                    cx, cy, radii = cx * downsample_factor, cy * downsample_factor, radii * downsample_factor
                else:
                    accums, cx, cy, radii = get_circle(edge, r_guess=r_guess//downsample_factor, n_dots=n_dots,pxl_range=pxl_range,pxl_accuracy=pxl_accuracy)
                    cx, cy, radii = cx*downsample_factor, cy*downsample_factor, radii*downsample_factor
                if countour_bool:
                    radii = radii-downsample_factor
                for center_y, center_x, radius in zip(cy, cx, radii):
                    cv2.circle(im, (center_x, center_y), int(radius), (255, 0, 0), 20)
                with right:
                    ""
                    ""
                    ""
                    st.image(im, width = 200)
                dic = dict(center_x=cy, center_y=cx, radius=radii, accum=accums)
                df = pd.DataFrame(dic)
                df = get_dot_pos(df)
                if countour_bool:
                    df_area = pd.DataFrame(
                        {"center_x": [], "center_y": [], "Area": []})
                    for i,cnt in enumerate(contours):

                        M = cv2.moments(cnt)
                        df_area.loc[i,["center_x","center_y","Area"]] = [M['m10'] / M['m00'],M['m01'] / M['m00'],M['m00']]
                        df_area = get_dot_pos(df_area)
                        df_area = df_area.drop(["center_x","center_y"],axis=1)
                        df = pd.merge(df, df_area, on="dot_pos")
                df = df.sort_values("dot_pos")
                df = df.rename(columns = {"center_x": "x", "center_y": "y"})
            left, right = st.columns(2, vertical_alignment = "center")
            with right:
                "Analysis results :"
                st.dataframe(df,hide_index=True)
            with left:
                "Image Guess :"
                if len(canvas_result.json_data["objects"])>0:
                    objects = get_dot_pos(objects).sort_values("dot_pos")
                    objects=objects.rename(columns = {"center_x": "x", "center_y": "y"})
                    st.dataframe(objects.loc[:,["center_x","center_y","radius_guess","dot_pos"]],hide_index=True)
                else:
                    st.dataframe({"x":[], "y":[], "radius_guess":[], "dot_pos":[]}, hide_index = True)

            if st.button("Save Session State"):
                st.session_state.downsample_factor
                dic_stat = st.session_state.to_dict()
                dic_stat.pop('circle_draw', None)
                dic_stat.pop('main_image', None)
                df_info = pd.json_normalize(dic_stat)
                # df_info["selected_date"]=df_info["selected_date"].astype(str)
                df_info = df_info.astype({"selected_date":str})
                df["selected_date"] = [df_info["selected_date"].array[0]]*len(df)
                df["selected_num"] = [df_info["selected_num"].array[0]]*len(df)
                df_info.set_index(["selected_date", "selected_num"], inplace = True)
                df.set_index(["selected_date", "selected_num","dot_pos"], inplace = True)

                save_session_state(df_info)

def page2():
    st.title("Second page")
pg = st.navigation([
    st.Page(page1, title="Visual Anlysis", icon="👀"),
    st.Page(page2, title="Automatic analysis", icon="💻"),
])
pg.run()