import numpy as np
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Create a black background image (200x200)
bg_array = np.zeros((200, 200, 3), dtype=np.uint8)  # all black
bg_image = Image.fromarray(bg_array)

# Circle definition
json_circle = {
    "version": "4.4.0",
    "objects": [
        {
            "type": "circle",
            "left": 80,     # x-position
            "top": 80,      # y-position
            "radius": 40,   # circle radius
            "stroke": "rgba(255,0,0,1)",       # red border
            "fill": "rgba(255,0,0,0.3)",       # semi-transparent fill
            "strokeWidth": 3
        }
    ]
}

st.write("Circle with black background below:")

canvas = st_canvas(
    fill_color="rgba(255, 0, 0, 0.3)",  # default fill if drawing new
    stroke_width=3,
    stroke_color="rgba(255, 0, 0, 1)",
    background_color="#eee",
    background_image=bg_image,          # <- black background image
    update_streamlit=False,
    width=200,
    height=200,
    drawing_mode="transform",
    initial_drawing=json_circle,
    point_display_radius=0,
    key="circle_test"
)

# st.json(canvas.json_data)
