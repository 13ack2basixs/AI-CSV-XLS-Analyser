import streamlit as st
import pandas as pd
from pandasai import SmartDataframe 
from pandasai.llm.openai import OpenAI
from datetime import datetime, timedelta

openai_api_key = st.secrets["OPENAI_API_KEY"]
llm = OpenAI(api_token=openai_api_key.strip()) 

def sanitise_input(user_input):
    allowed_chars = {
        'abcdefghijklmnopqrstuvwxyz',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        '0123456789',
        ' ', ',', '.', '?', '-', '_', "'", '"', '@', '\n', '\r', '\t'
    }
    MAX_INPUT_LENGTH = 1000
    sanitised = []
    char_count = 0
    
    for char in user_input:
        if char in allowed_chars:
            sanitised.append(char)
            char_count += 1
            if char_count >= MAX_INPUT_LENGTH:
                break
    return ''.join(sanitised)

def check_rate_limit():
    rl = st.session_state.rate_limit

    # Reset counter if past 1 min
    if datetime.now() > rl["last_reset"] + timedelta(seconds=rl["window_seconds"]):
        rl["count"] = 0
        rl["last_reset"] = datetime.now()
    
    rl["count"] += 1
    return rl["count"] > rl["max_requests"]

st.title("AI CSV/XLS Analyser")

# Upload files
uploaded_files = st.file_uploader("Upload one or more CSV/Excel files", accept_multiple_files=True, type=["csv", "xls", "xlsx"])
options = [uploaded_file.name for uploaded_file in uploaded_files]

# User input 
n = st.text_input("How many rows would you like to view?", "")
file = st.selectbox("Select which file you would like to view the rows of:", options, index=0)

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

    # Initialise session state
    if "missing_prompt" not in st.session_state:
        st.session_state.missing_prompt = False
    if "generate_prompt" not in st.session_state:
        st.session_state.generate_prompt = False
    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
    if "prompt_input" not in st.session_state: 
        st.session_state.prompt_input = ""
    if "feedback_history" not in st.session_state:
        st.session_state.feedback_history = []
    if "feedback_message" not in st.session_state:
        st.session_state.feedback_message = ""
    if "rate_limit" not in st.session_state:
        st.session_state.rate_limit = {
            "count": 0,
            "last_reset": datetime.now(),
            "window_seconds": 60,
            "max_requests": 5,
        }

    st.session_state.prompt_input = st.text_area("What do you want to know about the selected file?",
                              value=st.session_state.prompt_input)
    
    # Sanitise prompt input
    prompt_input = sanitise_input(st.session_state.prompt_input)

    # On click event for sending prompt
    def handle_send():
        if st.session_state.prompt_input.strip():
            st.session_state.generate_prompt = True
            st.session_state.missing_prompt = False
        else:
            st.session_state.generate_prompt = False
            st.session_state.missing_prompt = True
    
    # Display warning for empty prompt
    if st.session_state.missing_prompt:
        st.warning("Please enter a prompt!")

    # Display dropdown of prompt history
    if st.session_state.prompt_history:
        old_prompt = st.selectbox("Select which prompt you would like to re-use:",
                    options=st.session_state.prompt_history[::-1], index=None)
        if old_prompt:
            st.session_state.prompt_input = old_prompt

    st.button("Send", on_click=handle_send)

    prompt_input = st.session_state.prompt_input.lower()
    if st.session_state.generate_prompt:
        if check_rate_limit():
            st.error("Too many requests. Please try again after a minute.")
            st.stop()
            
        with st.spinner("Generating..."):
            # Extract dataset user wants to know about
            dataset = None
            for f in uploaded_files:
                if f.name.lower() in prompt_input:
                    dataset = f.name
                    break
            
            # Filter out the exact dataset
            if dataset:
                prompted_file = None
                for f in uploaded_files:
                    if f.name.lower() == dataset.lower():
                        prompted_file = f
                        break
                # Check if csv/excel then read it
                if prompted_file: 
                    prompted_file.seek(0) # Reset pointer to start of file (allow re-parsing)
                    if prompted_file.name.endswith(".csv"):
                        df = pd.read_csv(f)
                    else:
                        df = pd.read_excel(f)

                    sdf = SmartDataframe(df, config={"llm": llm})
                    response = sdf.chat(prompt_input, output_type="string")
            
                    # Append prompt to history
                    prompt = st.session_state.prompt_input.strip()
                    if prompt and prompt not in st.session_state.prompt_history:
                        st.session_state.prompt_history.append(prompt_input.strip())
                        # Keep only recent 5 prompts
                        st.session_state.prompt_history = st.session_state.prompt_history[-5:]
                    
                    st.write(response)

                    def handle_like():
                        st.session_state.feedback_history.append({
                            "prompt": prompt_input,
                            "response": response,
                            "feedback": "Like"
                        })
                        st.session_state.feedback_message = "You found this useful!"
                    
                    def handle_dislike():
                        st.session_state.feedback_history.append({
                            "prompt": prompt_input,
                            "response": response,
                            "feedback": "Dislike"
                        })
                        st.session_state.feedback_message = "You did not find this useful!"

                    # Show feedback buttons
                    st.button("Like", on_click=handle_like, icon=":material/thumb_up:")            
                    st.button("Dislike", on_click=handle_dislike, icon=":material/thumb_down:")
                    
                    if st.session_state.feedback_message:
                        st.info(st.session_state.feedback_message)
                else:
                    st.warning("Dataset not found. Have you uploaded it?")
            else:
                st.warning("Could not find valid dataset in your prompt.")
        
        st.session_state.generate_prompt = False
