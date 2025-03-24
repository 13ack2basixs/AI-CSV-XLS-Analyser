import streamlit as st

st.title("AI CSV/XLS Analyser")

# Upload files
uploaded_files = st.file_uploader("Upload one or more CSV/Excel files", accept_multiple_files=True, type=["csv", "xls", "xlsx"])


