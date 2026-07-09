import streamlit as st
import yaml
import base64
import google.generativeai as genai
from github import Github

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.5-flash')

# --- Utilities ---
def format_superscripts(text):
    mapping = {"^0": "⁰", "^1": "¹", "^2": "²", "^3": "³", "^4": "⁴", "^5": "⁵", "^6": "⁶", "^7": "⁷", "^8": "⁸", "^9": "⁹"}
    for code, unicode_char in mapping.items():
        text = text.replace(code, unicode_char)
    return text

def clean_latex(text):
    return text.replace('\\\\', '\\')

def generate_image(prompt):
    """Generates an image using gemini-3.1-flash-image."""
    # Using the current supported model for image generation
    model_name = 'gemini-3.1-flash-image'
    imagen = genai.GenerativeModel(model_name) 
    
    # Configure the generation to explicitly request an image response
    result = imagen.generate_content(
        f"A clean, high-contrast, black and white physics textbook schematic diagram on a white background, no shading, minimal detail. {prompt}",
        generation_config={"response_modalities": ["IMAGE"]}
    )
    
    # Extract image data from the response parts
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
            # image_bytes is already base64 encoded data from the Gemini API
            repo.create_file(path, f"Add image {filename}", image_bytes.decode('utf-8'))
        else:
            repo.create_file(path, f"Add {filename}", content)
        st.success(f"Pushed {path} to GitHub!")
    except Exception as e:
        st.error(f"GitHub push failed: {e}")

# --- State ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "id": "PHYS-2026-001", "metadata": {"topic": "", "marks": 4},
        "question": {"text": ""}, "solution": {"steps": []},
        "media": {"diagram_url": None, "diagram_description": None}
    }
if 'image_bytes' not in st.session_state:
    st.session_state.image_bytes = None

# --- UI ---
st.title("Physics Question Generator")
prompt = st.text_area("Question Prompt")

if st.button("Generate Question"):
    with st.spinner("Generating content..."):
        system_instr = (
            "Use LaTeX (e.g., $\\frac{a}{b}$, $\\times$). "
            "Include steps with milestone_value/tolerance. "
            "If a diagram is needed, provide a detailed 'diagram_description' prompt in a 'textbook style'. "
            "If no diagram, set diagram_url and diagram_description to null."
        )
        query = f"Generate a physics question based on: {prompt}. {system_instr}"
        response = model.generate_content(query)
        
        yaml_content = yaml.safe_load(response.text.replace('```yaml', '').replace('```', ''))
        st.session_state.data = yaml_content
        
        # Trigger Image Gen
        desc = yaml_content['media'].get('diagram_description')
        if desc:
            st.session_state.image_bytes = generate_image(desc)
        else:
            st.session_state.image_bytes = None

# --- Display ---
st.subheader("Question Data & Preview")
col1, col2 = st.columns(2)
with col1:
    st.code(yaml.dump(st.session_state.data), language='yaml')
if st.session_state.image_bytes:
    with col2:
        # Decode base64 bytes for display in streamlit
        st.image(base64.b64decode(st.session_state.image_bytes), caption="Generated Diagram")

# --- Export ---
if st.button("Push to GitHub"):
    qid = st.session_state.data['id']
    if st.session_state.image_bytes:
        img_filename = f"{qid}.png"
        push_to_github(img_filename, None, is_image=True, image_bytes=st.session_state.image_bytes)
        st.session_state.data['media']['diagram_url'] = f"I/{img_filename}"
    
    push_to_github(f"{qid}.yaml", yaml.dump(st.session_state.data), is_image=False)
