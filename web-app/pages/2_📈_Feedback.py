import streamlit as st
import time
import numpy as np

st.set_page_config(page_title="Feedback", page_icon="📈")

st.markdown("# Feedback")
st.write(
    """This memo when you want give me feedback about this page. Enjoy!"""
)
def clear_text():
    st.session_state.my_text = st.session_state.widget
    st.session_state.widget = ""

st.text_input('Enter feedback here:', key='widget', on_change=clear_text)
my_text = st.session_state.get('my_text', '')
if my_text:
    st.write('Thanks for your feedback')