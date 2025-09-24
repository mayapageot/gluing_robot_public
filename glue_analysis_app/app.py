import streamlit as st
from datetime import date
from utils.session_utils import init_global_session_state
init_global_session_state()
st.set_page_config(page_title="Glue Analysis App", layout="wide")

st.title("Glue Analysis App")

st.sidebar.success("Select a page above.")

# Streamlit will auto-discover files inside `pages/`
