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

# Initialize session states if they don't exist
if 'yaml_text' not in st.session_state:
    st.session_state.yaml_text = ""
if 'qid' not in st.session_state:
    st.session_state.qid = ""
if 'image_bytes' not in st.session_state:
    st.session_state.image_bytes = None
if 'data' not in st.session_state:
    st.session_state.data = {}

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
        # We explicitly enforce the JSON schema expected by the frontend
        system_instr = (
            "Output your entire response as a single, valid JSON object. Do not include any conversational text or markdown. "
            "Use LaTeX formatting for equations. You MUST strictly follow this exact JSON structure: \n"
            "{\n"
            "  \"id\": \"string (e.g., Q005)\",\n"
            "  \"metadata\": {\"topic\": \"string\", \"marks\": integer, \"difficulty_level\": float (0.0 to 1.0)},\n"
            "  \"question\": {\n"
            "    \"text\": \"string (the full question text)\",\n"
            "    \"variables\": [{\"name\": \"string\", \"value\": float}]\n"
            "  },\n"
            "  \"solution\": {\n"
            "    \"final_answer\": \"string\",\n"
            "    \"marks_available\": integer,\n"
            "    \"steps\": [\n"
            "      {\"step_number\": integer, \"text\": \"string\", \"marks_assigned\": integer, \"check_type\": \"string (e.g. numeric, none)\", \"milestone_value\": float, \"tolerance\": float}\n"
            "    ]\n"
            "  },\n"
            "  \"media\": {\"diagram_url\": \"null\", \"diagram_description\": \"textbook style prompt for diagram or null\", \"video_explainer_url\": \"null\"},\n"
            "  \"tags\": [\"string\"]\n"
            "}"
        )
        query = f"Generate a physics question based on: {prompt}. {system_instr}"
        
        # Enforce application/json output mode for error-free parsing
        response = model.generate_content(
            query,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the JSON response directly (valid JSON is always valid YAML)
        yaml_content = yaml.safe_load(response.text)
        
        # Store initial structured values in Session State
        st.session_state.data = yaml_content
        st.session_state.yaml_text = yaml.dump(yaml_content, sort_keys=False)
        st.session_state.qid = yaml_content.get('id', 'new-question-01')
        
        desc = yaml_content.get('media', {}).get('diagram_description')
        st.session_state.image_bytes = generate_image(desc) if desc else None

# --- Display ---
st.subheader("Edit & Preview")

if st.session_state.yaml_text:
    # 1. Editable Question ID
    qid_input = st.text_input("Question ID (will be used for the filenames on GitHub)", value=st.session_state.qid)
    st.session_state.qid = qid_input
    
    # 2. Editable YAML block
    edited_yaml = st.text_area("Edit YAML Data Block", value=st.session_state.yaml_text, height=450)
    st.session_state.yaml_text = edited_yaml
    
    # Try parsing on-the-fly to validate syntax and sync parsed dict state
    try:
        parsed_data = yaml.safe_load(edited_yaml)
        if parsed_data is not None:
            st.session_state.data = parsed_data
            st.success("✅ YAML structure is valid!")
    except Exception as e:
        st.error(f"❌ Invalid YAML structure: {e}")
        
    # Render Generated Diagram Preview
    if st.session_state.image_bytes:
        st.image(base64.b64decode(st.session_state.image_bytes), caption="Generated Diagram")

# --- Push Button Execution ---
if st.button("Push to GitHub"):
    if not st.session_state.yaml_text:
        st.error("No question data generated yet!")
    elif not st.session_state.qid:
        st.error("Please enter a valid Question ID before pushing.")
    else:
        # Sync current editable parameters back into the final saved dictionary
        qid = st.session_state.qid
        st.session_state.data['id'] = qid
        
        if st.session_state.image_bytes:
            img_filename = f"{qid}.png"
            push_to_github(img_filename, None, is_image=True, image_bytes=st.session_state.image_bytes)
            
            # Safe setup for media key block
            if 'media' not in st.session_state.data or st.session_state.data['media'] is None:
                st.session_state.data['media'] = {}
            st.session_state.data['media']['diagram_url'] = f"I/{img_filename}"
            
        # Push completed configuration file
        push_to_github(f"{qid}.yaml", yaml.dump(st.session_state.data, sort_keys=False), is_image=False)
