import streamlit as st
import pandas as pd

openai_api_key = st.secrets["OPENAI_API_KEY"]

st.title("AI CSV/XLS Analyser")

# Upload files
uploaded_files = st.file_uploader("Upload one or more CSV/Excel files", accept_multiple_files=True, type=["csv", "xls", "xlsx"])
options = [uploaded_file.name for uploaded_file in uploaded_files]

# User input 
n = st.text_input("How many rows would you like to view?", "")
file = st.selectbox("Select which file you would like to view the rows of", options, index=0)

if file and n.isdigit():
    for f in uploaded_files:
        if f.name == file:
            selected_file = f
    
    if selected_file:
        if selected_file.name.endswith(".csv"):
            df = pd.read_csv(selected_file)
        else:
            df = pd.read_excel(selected_file)
        st.write(df.head(int(n)))

