import streamlit as st
import yaml
import json
# Import your GenAI client here (e.g., google.generativeai or openai)

st.set_page_config(layout="wide")
st.title("Physics Question Editor")

# --- Sidebar: File Handling ---
st.sidebar.header("Data Management")
uploaded_file = st.sidebar.file_uploader("Load existing YAML", type=["yaml", "yml"])

# Initialize session state for the question structure
if 'data' not in st.session_state:
    st.session_state.data = {
        "id": "PHYS-2026-001", "metadata": {"topic": "", "marks": 0},
        "question": {"text": ""}, "solution": {"final_answer": ""}
    }

# Load YAML if uploaded
if uploaded_file:
    st.session_state.data = yaml.safe_load(uploaded_file)

# --- Screen 1: Generation ---
st.subheader("1. Generate Question")
prompt = st.text_area("Enter your prompt:", placeholder="E.g., Create a 4-mark physics question about kinematics...")
if st.button("Generate with AI"):
    # CALL YOUR AI HERE AND UPDATE st.session_state.data
    # st.session_state.data = call_gemini(prompt)
    st.success("Generation complete!")

# --- Screen 2: Editor ---
st.subheader("2. Edit Fields")
col1, col2 = st.columns(2)
with col1:
    st.session_state.data['id'] = st.text_input("ID", st.session_state.data['id'])
    st.session_state.data['metadata']['topic'] = st.text_input("Topic", st.session_state.data['metadata']['topic'])
    st.session_state.data['metadata']['marks'] = st.number_input("Marks", st.session_state.data['metadata']['marks'])
with col2:
    st.session_state.data['question']['text'] = st.text_area("Question Text", st.session_state.data['question']['text'])
    st.session_state.data['solution']['final_answer'] = st.text_input("Final Answer", st.session_state.data['solution']['final_answer'])

# --- Save Action ---
st.subheader("3. Save Result")
yaml_output = yaml.dump(st.session_state.data, sort_keys=False)
st.code(yaml_output, language='yaml')

st.download_button(
    label="Download YAML",
    data=yaml_output,
    file_name=f"{st.session_state.data['id']}.yaml",
    mime="text/yaml"
)
