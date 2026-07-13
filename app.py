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

def push_to_github(filename, content, is_image=False, image_data=None):
    subdir = "I" if is_image else "Q"
    path = f"{subdir}/{filename}"
    
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        push_content = image_data if is_image else content
        
        try:
            contents = repo.get_contents(path)
            repo.update_file(contents.path, f"Update {path}", push_content, contents.sha)
            st.success(f"Updated {path} on GitHub!")
        except:
            repo.create_file(path, f"Add {path}", push_content)
            st.success(f"Created {path} on GitHub!")
    except Exception as e:
        st.error(f"GitHub push failed for {path}: {e}")

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

def generate_question(prompt_text, force_image=False):
    with st.spinner("Generating..."):
        extra_instr = " You MUST include a detailed descriptive text for a diagram in the 'diagram_url' field." if force_image else ""
        query = (f"Generate a physics question based on: {prompt_text}. "
                 f"Output strictly in valid YAML matching this schema: {st.session_state.data}.{extra_instr} "
                 "Return ONLY the YAML.")
        
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=query
        )
        
        st.session_state.data = yaml.safe_load(clean_latex(response.text.replace('```yaml', '').replace('```', '')))
        st.session_state.image_prompt = None
        st.success("Generation complete!")

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

col_gen1, col_gen2 = st.columns(2)
with col_gen1:
    if st.button("Generate Question"):
        generate_question(prompt, force_image=False)
with col_gen2:
    if st.button("Generate Question with Image"):
        generate_question(prompt, force_image=True)

st.subheader("Edit Question Data")
st.session_state.data['id'] = st.text_input("Question ID", st.session_state.data['id'])

# --- Image Generation Flow ---
if st.session_state.data.get('media', {}).get('diagram_url'):
    if st.button("Generate Image Prompt"):
        desc = st.session_state.data['media']['diagram_url']
        st.session_state.image_prompt = f"Generate a physics textbook style image, black and white line drawing of {desc}"

if st.session_state.get('image_prompt'):
    st.info("Image prompt generated. Use the copy button on the code block below:")
    st.code(st.session_state.image_prompt, language='text')
    st.link_button("Open Gemini Chat", "https://gemini.google.com")

st.divider()
st.subheader("Upload Diagram")
uploaded_image = st.file_uploader("Upload generated diagram", type=["png", "jpg", "jpeg"])

# Display the YAML *after* the logic so it picks up state changes
st.code(yaml.dump(st.session_state.data, sort_keys=False), language='yaml')

col1, col2 = st.columns(2)
with col1:
    st.download_button("Download YAML", yaml.dump(st.session_state.data, sort_keys=False), file_name=f"{st.session_state.data['id']}.yaml", mime="text/yaml")
with col2:
    if st.button("Push to GitHub"):
        q_id = st.session_state.data['id']
        
        # 1. Update the state first so it persists in the UI
        if uploaded_image:
            ext = uploaded_image.name.split('.')[-1]
            st.session_state.data['media']['diagram_url'] = f"I/{q_id}.{ext}"
            # 2. Push Image
            push_to_github(f"{q_id}.{ext}", None, is_image=True, image_data=uploaded_image.getvalue())
        
        # 3. Push updated YAML (which now contains the URL)
        push_to_github(f"{q_id}.yaml", yaml.dump(st.session_state.data, sort_keys=False))
        # 4. Rerun to update the UI display
        st.rerun()
