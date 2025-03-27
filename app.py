import streamlit as st
import pandas as pd
from pandasai import SmartDataframe 
from pandasai.llm.openai import OpenAI

openai_api_key = st.secrets["OPENAI_API_KEY"]
llm = OpenAI(api_token=openai_api_key.strip()) 

st.title("AI CSV/XLS Analyser")

# Upload files
uploaded_files = st.file_uploader("Upload one or more CSV/Excel files", accept_multiple_files=True, type=["csv", "xls", "xlsx"])
options = [uploaded_file.name for uploaded_file in uploaded_files]

# User input 
n = st.text_input("How many rows would you like to view?", "")
file = st.selectbox("Select which file you would like to view the rows of", options, index=0)

if file and n.isdigit():
    # Find selected file by user
    for f in uploaded_files:
        if f.name == file:
            selected_file = f
    
    # Read and display n rows by user
    if selected_file:
        if selected_file.name.endswith(".csv"):
            df = pd.read_csv(selected_file)
        else:
            df = pd.read_excel(selected_file)
        st.write(df.head(int(n)))

    prompt = st.text_area("What do you want to know about the selected file?")

    # Initialise session state
    if "missing_prompt" not in st.session_state:
        st.session_state.missing_prompt = False
    if "generate_prompt" not in st.session_state:
        st.session_state.generate_prompt = False

    # On click event for sending prompt
    def handle_send():
        if prompt.strip() == "":
            st.session_state.generate_prompt = False
            st.session_state.missing_prompt = True
        else:
            st.session_state.generate_prompt = True
            st.session_state.missing_prompt = False
    
    if st.session_state.missing_prompt:
        st.warning("Please enter a prompt!")

    st.button("Send", on_click=handle_send)
    
    if st.session_state.generate_prompt:
        with st.spinner("Generating..."):
            sdf = SmartDataframe(df, config={"llm": llm})
            response = sdf.chat(prompt, output_type="string")
            st.write(response)