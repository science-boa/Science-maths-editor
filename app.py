import streamlit as st
import yaml
import google.generativeai as genai

# Setup page
st.set_page_config(page_title="Physics Question Generator", layout="wide")

# Configure your latest authorized model
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.5-flash') 

# Define your exact schema
def get_empty_schema():
    return {
        "id": "PHYS-2026-001",
        "metadata": {"topic": "", "marks": 4, "difficulty_level": 0.5},
        "question": {"text": "", "variables": []},
        "solution": {"step_by_step": [], "final_answer": ""},
        "media": {"diagram_url": None, "video_explainer_url": None},
        "tags": []
    }

if 'data' not in st.session_state:
    st.session_state.data = get_empty_schema()

# Sidebar for file upload
uploaded_file = st.sidebar.file_uploader("Load Schema YAML", type=["yaml"])
if uploaded_file:
    st.session_state.data = yaml.safe_load(uploaded_file)

# Generation logic
prompt = st.text_area("Question Prompt")
if st.button("Generate"):
    # Instructing the model to adhere strictly to your schema
    query = f"Generate a physics question based on: {prompt}. Output strictly in YAML matching this schema: {st.session_state.data}"
    response = model.generate_content(query)
    st.session_state.data = yaml.safe_load(response.text.replace('```yaml', '').replace('```', ''))

# Editor fields (simplified view)
st.session_state.data['question']['text'] = st.text_area("Question", st.session_state.data['question']['text'])
st.session_state.data['solution']['final_answer'] = st.text_input("Answer", st.session_state.data['solution']['final_answer'])

# YAML preview and download
yaml_output = yaml.dump(st.session_state.data, sort_keys=False)
st.code(yaml_output, language='yaml')
st.download_button("Download YAML", yaml_output, f"{st.session_state.data['id']}.yaml")
