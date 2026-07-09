import streamlit as st
import yaml
import base64
import pandas as pd
import google.generativeai as genai
from github import Github
import os

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.5-flash')

# --- Utilities ---
def load_prompt_library():
    """Loads all prompts from prompts.csv if it exists."""
    if os.path.exists("prompts.csv"):
        try:
            # Load the CSV, handling potential quoting issues
            df = pd.read_csv("prompts.csv", header=None, quotechar='"')
            # Ensure we get all prompts regardless of column formatting
            prompts = df.iloc[:, 0].dropna().tolist()
            return {f"{i+1}: {p[:40]}...": p for i, p in enumerate(prompts)}
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
    
    return {"Default Prompt": "Act as an expert GCSE Physics examiner. Generate a calculation question..."}

def generate_image(prompt):
    model_name = 'gemini-3.1-flash-image'
    imagen = genai.GenerativeModel(model_name) 
    result = imagen.generate_content(
        f"A clean, high-contrast, black and white physics textbook schematic diagram on a white background, no shading, minimal detail. {prompt}",
        generation_config={"response_modalities": ["IMAGE"]}
    )
    for part in result.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data
    return None

def push_to_github(filename, content, is_image=False, image_bytes=None):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["GITHUB_REPO"])
    path = f"I/{filename}" if is_image else f"Q/{filename}"
    try:
        if is_image:
            repo.create_file(path, f"Add image {filename}", image_bytes.decode('utf-8'))
        else:
            repo.create_file(path, f"Add {filename}", content)
        st.success(f"Pushed {path} to GitHub!")
    except Exception as e:
        st.error(f"GitHub push failed: {e}")

# --- UI ---
st.title("Physics Question Generator")

# Load library
PROMPT_LIBRARY = load_prompt_library()

st.sidebar.header("Prompt Library")
# The selectbox natively supports scrolling for long lists
selected_key = st.sidebar.selectbox("Select a Prompt Type", list(PROMPT_LIBRARY.keys()))
prompt = st.text_area("Question Prompt", value=PROMPT_LIBRARY[selected_key], height=150)

if st.button("Generate Question"):
    with st.spinner("Generating..."):
        system_instr = (
            "Output your entire response as a single, valid JSON object. Do not include any conversational text, explanation or markdown formatting outside of the JSON. "
            "Use LaTeX. Ensure steps contain: step_number, text, marks_assigned, "
            "check_type, milestone_value, and tolerance. "
            "If a diagram is needed, provide a detailed 'diagram_description' prompt in a 'textbook style'. "
            "If no diagram, set diagram_url and diagram_description to null."
        )
        query = f"Generate a physics question based on: {prompt}. {system_instr}"
        
        # Enforce application/json output mode for error-free parsing
        response = model.generate_content(
            query,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the JSON response directly (valid JSON is always valid YAML)
        yaml_content = yaml.safe_load(response.text)
        st.session_state.data = yaml_content
        
        desc = yaml_content.get('media', {}).get('diagram_description')
        st.session_state.image_bytes = generate_image(desc) if desc else None

# --- Display ---
st.subheader("Output Preview")
if 'data' in st.session_state:
    st.code(yaml.dump(st.session_state.data), language='yaml')
    if st.session_state.image_bytes:
        st.image(base64.b64decode(st.session_state.image_bytes), caption="Generated Diagram")

if st.button("Push to GitHub"):
    qid = st.session_state.data['id']
    if st.session_state.image_bytes:
        img_filename = f"{qid}.png"
        push_to_github(img_filename, None, is_image=True, image_bytes=st.session_state.image_bytes)
        st.session_state.data['media']['diagram_url'] = f"I/{img_filename}"
    push_to_github(f"{qid}.yaml", yaml.dump(st.session_state.data), is_image=False)
