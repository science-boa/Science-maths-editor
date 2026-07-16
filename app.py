import streamlit as st
import yaml
import os
import pandas as pd
import time
from github import Github
from google import genai

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

# Initialize the Interactions API client
client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", ""))

# --- Utilities ---
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
            st.toast(f"Updated {path} on GitHub!", icon="✅")
        except:
            repo.create_file(path, f"Add {path}", push_content)
            st.toast(f"Created {path} on GitHub!", icon="✅")
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

def generate_question(prompt_text, force_image=False, unit_conv=False, std_form=False, inc_eq=False):
    with st.spinner("Generating..."):
        extra_instr = " You MUST include a detailed descriptive text for a diagram in the 'diagram_url' field." if force_image else ""
        latex_instr = " All mathematical expressions and scientific notation MUST be formatted in LaTeX (e.g., $E=mc^2$)."
        
        conv_instr = " include one unit that must be converted to its base unit in the question." if unit_conv else " do not use unit conversions."
        std_form_instr = " give one value as standard form." if std_form else ""
        eq_instr = " include the equations needed in the question text." if inc_eq else ""
        
        query = (f"Generate a physics question based on: {prompt_text}.{latex_instr} "
                 f"{conv_instr} {std_form_instr} {eq_instr} "
                 f"Output strictly in valid YAML matching this schema: {st.session_state.data}.{extra_instr} "
                 "Return ONLY the YAML.")
        
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=query
            )
            raw_text = response.text.replace('```yaml', '').replace('```', '')
            st.session_state.data = yaml.safe_load(clean_latex(raw_text))
            st.session_state.image_prompt = None
            st.success("Generation complete!")
        except Exception as e:
            st.error(f"Generation failed: {e}")

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

# Toggle Switches
col_t1, col_t2, col_t3 = st.columns(3)
with col_t1:
    unit_conv = st.toggle("Unit Conversions")
with col_t2:
    std_form = st.toggle("Standard Form")
with col_t3:
    inc_eq = st.toggle("Include Equation")

col_gen1, col_gen2 = st.columns(2)
with col_gen1:
    if st.button("Generate Question"):
        generate_question(prompt, force_image=False, unit_conv=unit_conv, std_form=std_form, inc_eq=inc_eq)
with col_gen2:
    if st.button("Generate Question with Image"):
        generate_question(prompt, force_image=True, unit_conv=unit_conv, std_form=std_form, inc_eq=inc_eq)

st.subheader("Edit Question Data")
st.session_state.data['id'] = st.text_input("Question ID", st.session_state.data['id'])

if st.session_state.data.get('media', {}).get('diagram_url'):
    if st.button("Generate Image Prompt"):
        desc = st.session_state.data['media']['diagram_url']
        st.session_state.image_prompt = f"Generate a physics textbook style image, black and white line drawing of {desc}"

if st.session_state.get('image_prompt'):
    st.info("Image prompt generated. Use the copy button below:")
    st.code(st.session_state.image_prompt, language='text')
    st.link_button("Open Gemini Chat", "https://gemini.google.com")

st.divider()
st.subheader("Upload Diagram")
uploaded_image = st.file_uploader("Upload generated diagram", type=["png", "jpg", "jpeg"])

st.code(yaml.dump(st.session_state.data, sort_keys=False), language='yaml')

col1, col2 = st.columns(2)
with col1:
    st.download_button("Download YAML", yaml.dump(st.session_state.data, sort_keys=False), file_name=f"{st.session_state.data['id']}.yaml", mime="text/yaml")
with col2:
    if st.button("Push to GitHub"):
        q_id = st.session_state.data['id']
        if uploaded_image:
            ext = uploaded_image.name.split('.')[-1]
            st.session_state.data['media']['diagram_url'] = f"I/{q_id}.{ext}"
            push_to_github(f"{q_id}.{ext}", None, is_image=True, image_data=uploaded_image.getvalue())
            time.sleep(1)
        
        push_to_github(f"{q_id}.yaml", yaml.dump(st.session_state.data, sort_keys=False))
        st.rerun()
