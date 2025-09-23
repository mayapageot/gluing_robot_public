"""
IO utilities for glue analysis app.
"""
import os

def list_image_files(basedir, date_str, cam="CAM1"):
    list_dirs = [d for d in os.listdir(basedir) if date_str == d[:6]]
    if not list_dirs:
        return []
    dir_path = os.path.join(basedir, list_dirs[0], cam)
    image_options = [os.path.join(dir_path, file) for file in os.listdir(dir_path) if file.endswith("bmp")]
    return image_options
