import streamlit as st
from PIL import Image

#img = Image.open('svtech-logo.jpg')
#st.sidebar.image(img, width=300)
st.set_page_config(
    page_title="Welcome",
    page_icon="✨",
    layout="wide",
 )

st.write("# Welcome 👋")
#st.sidebar.success("Select one above.")
st.markdown(
    """
    This page made by Linh Nguyen Tuan\n
    linh.nguyentuan@svtech.com.vn\n
    Base Treamlit- open source app framework.
    
    **👈 Select a page from the sidebar**
"""
)
