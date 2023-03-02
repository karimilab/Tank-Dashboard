import streamlit as st
import os

st.set_page_config(
    page_title="Welcome page",
    page_icon="👋",
)

st.markdown(
    """
    # Welcome to Tank Dashboard app!
    This is a dashboard tool for simulating a cylindrical tank for cryogenic energy fluid storage
"""
)

os.system("conda install numpy")
# dependencies:
#   - numpy
#   - scipy
#   - pandas
#   - assimulo
#   - matplotlib
#   - xlsxwriter
#   - openpyxl