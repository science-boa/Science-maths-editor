import streamlit as st
import yaml
import google.generativeai as genai
from github import Github
import os
import pandas as pd
import io
from PIL import Image

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.1-flash-lite')
image_model = genai.GenerativeModel('gemini-3.1-flash-lite-image')

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

def push_to_github(filename, content):
    """Pushes the YAML content to the /Q directory of the configured repository."""
    # Ensure filename starts with /Q/
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
            "steps": [
                {
                    "step_number": 1,
                    "text": "",
                    "marks_assigned": 1,
                    "check_type": "numeric",
                    "milestone_value": 0.0,
                    "tolerance": 0.001
                }
            ]
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
    with st.spinner("Generating with Gemini 3.5 Flash..."):
        system_instr = (
            "For physics questions, use LaTeX (e.g., $\\frac{a}{b}$, $\\times$). "
            "Ensure solution steps contain: step_number, text, marks_assigned, "
            "check_type (e.g., 'numeric'), milestone_value (as a float), and tolerance (as a float). "
            "For the 'diagram_url' field, instead of a URL, provide a detailed text description "
            "of the image/diagram that should accompany this question. "
            "If no diagram is needed, set 'diagram_url' to null. "
            "Ensure all backslashes are output as single backslashes."
        )
        
        query = (f"Generate a physics question based on: {prompt}. {system_instr} "
                 f"Output strictly in valid YAML matching this schema: {st.session_state.data}. "
                 "Return ONLY the YAML.")
        
        response = model.generate_content(query)
        
        raw_yaml = response.text.replace('```yaml', '').replace('```', '')
        cleaned_yaml = clean_latex(raw_yaml)
        formatted_yaml = format_superscripts(cleaned_yaml)
        
        st.session_state.data = yaml.safe_load(formatted_yaml)
        st.session_state.generated_image = None
        st.success("Generation complete!")

# --- UI: Editor ---
st.subheader("Edit Question Data")
st.session_state.data['id'] = st.text_input("Question ID", st.session_state.data['id'])

st.write("Current Data Loaded (Preview):")
st.code(yaml.dump(st.session_state.data, sort_keys=False), language='yaml')

# Image Generation Section
if st.session_state.data.get('media', {}).get('diagram_url'):
    if st.button("Generate Image"):
        with st.spinner("Generating image..."):
            desc = st.session_state.data['media']['diagram_url']
            img_prompt = f"Create a simple black and white physics textbook style diagram of {desc}"
            
            response = image_model.generate_content(
                img_prompt,
                generation_config={"response_modalities": ["IMAGE"]}
            )
            
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    st.session_state.generated_image = Image.open(io.BytesIO(image_bytes)).resize((480, 480))

if st.session_state.get('generated_image'):
    st.image(st.session_state.generated_image, caption="Generated Diagram")

col1, col2 = st.columns(2)
with col1:
    st.download_button("Download YAML", yaml.dump(st.session_state.data, sort_keys=False), 
                       file_name=f"{st.session_state.data['id']}.yaml", mime="text/yaml")
with col2:
    if st.button("Push to GitHub"):
        yaml_output = yaml.dump(st.session_state.data, sort_keys=False)
        push_to_github(f"{st.session_state.data['id']}.yaml", yaml_output)
