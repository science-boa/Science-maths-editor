import streamlit as st
import yaml
from google import genai
from github import Github
import os
import pandas as pd

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

# Initialize the Interactions API client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- Utilities ---
def format_superscripts(text):
    mapping = {
        "^0": "⁰", "^1": "¹", "^2": "²", "^3": "³", "^4": "⁴",
        "^5": "⁵", "^6": "⁶", "^7": "⁷", "^8": "⁸", "^9": "⁹"
    }
    for code, unicode_char in mapping.items():
        text = text.replace(code, unicode_char)
    return text

def clean_latex(text):
    return text.replace('\\\\', '\\')

def load_prompt_library():
    if os.path.exists("prompts.csv"):
        try:
            df = pd.read_csv("prompts.csv", header=None, quotechar='"')
            prompts = df.iloc[:, 0].dropna().tolist()
            return {f"{i+1}: {p[:40]}...": p for i, p in enumerate(prompts)}
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
    return {"Default Prompt": "Act as an expert GCSE Physics examiner. Generate a calculation question..."}

def push_to_github(filename, content):
    if not filename.startswith("Q/"):
        filename = f"Q/{filename}"
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        try:
            contents = repo.get_contents(filename)
            repo.update_file(contents.path, f"Update {filename}", content, contents.sha)
            st.success(f"Updated {filename} on GitHub!")
        except:
            repo.create_file(filename, f"Add {filename}", content)
            st.success(f"Created {filename} on GitHub!")
    except Exception as e:
        st.error(f"GitHub push failed: {e}")

def get_empty_schema():
    return {
        "id": "PHYS-2026-001",
        "metadata": {"topic": "", "marks": 4, "difficulty_level": 0.5},
        "question": {"text": "", "variables": []},
        "solution": {
            "final_answer": 0.0,
            "marks_available": 4,
            "steps": [{"step_number": 1, "text": "", "marks_assigned": 1, "check_type": "numeric", "milestone_value": 0.0, "tolerance": 0.001}]
        },
        "media": {"diagram_url": None, "video_explainer_url": None},
        "tags": []
    }

if 'data' not in st.session_state:
    st.session_state.data = get_empty_schema()

# --- UI ---
st.sidebar.title("Data Management")
uploaded_file = st.sidebar.file_uploader("Load Schema YAML", type=["yaml"])
if uploaded_file:
    st.session_state.data = yaml.safe_load(uploaded_file)

st.sidebar.title("Prompt Library")
PROMPT_LIBRARY = load_prompt_library()
selected_key = st.sidebar.selectbox("Select a Prompt Type", list(PROMPT_LIBRARY.keys()))

st.title("Physics Question Generator")
prompt = st.text_area("Question Prompt", value=PROMPT_LIBRARY[selected_key], height=100)

if st.button("Generate Question"):
    with st.spinner("Generating..."):
        query = (f"Generate a physics question based on: {prompt}. "
                 f"Output strictly in valid YAML matching this schema: {st.session_state.data}. "
                 "Return ONLY the YAML.")
        
        # Using the new Interactions API client
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=query
        )
        
        st.session_state.data = yaml.safe_load(clean_latex(response.text.replace('```yaml', '').replace('```', '')))
        st.session_state.image_prompt = None
        st.success("Generation complete!")

st.subheader("Edit Question Data")
st.session_state.data['id'] = st.text_input("Question ID", st.session_state.data['id'])
st.code(yaml.dump(st.session_state.data, sort_keys=False), language='yaml')

# --- Image Generation Flow ---
if st.session_state.data.get('media', {}).get('diagram_url'):
    if st.button("Generate Image Prompt"):
        desc = st.session_state.data['media']['diagram_url']
        st.session_state.image_prompt = f"Generate a physics textbook style image, black and white line drawing of {desc}"

if st.session_state.get('image_prompt'):
    st.info("Image prompt generated. Click below to copy and open Gemini.")
    st.text_area("Copy this prompt:", value=st.session_state.image_prompt, height=100)
    
    st.link_button("Open Gemini Chat", "https://gemini.google.com")

col1, col2 = st.columns(2)
with col1:
    st.download_button("Download YAML", yaml.dump(st.session_state.data, sort_keys=False), file_name=f"{st.session_state.data['id']}.yaml", mime="text/yaml")
with col2:
    if st.button("Push to GitHub"):
        push_to_github(f"{st.session_state.data['id']}.yaml", yaml.dump(st.session_state.data, sort_keys=False))
