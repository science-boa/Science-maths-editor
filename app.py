import streamlit as st
import yaml
import google.generativeai as genai

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

# Configure Google Generative AI
# Ensure you have GEMINI_API_KEY set in Streamlit Cloud Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Utilities ---
def format_superscripts(text):
    """Replaces caret notation (e.g., ^2) with Unicode (e.g., ²)."""
    mapping = {
        "^0": "⁰", "^1": "¹", "^2": "²", "^3": "³", "^4": "⁴",
        "^5": "⁵", "^6": "⁶", "^7": "⁷", "^8": "⁸", "^9": "⁹"
    }
    for code, unicode_char in mapping.items():
        text = text.replace(code, unicode_char)
    return text

def get_empty_schema():
    return {
        "id": "PHYS-2026-001",
        "metadata": {"topic": "", "marks": 4, "difficulty_level": 0.5},
        "question": {"text": "", "variables": []},
        "solution": {"step_by_step": [], "final_answer": ""},
        "media": {"diagram_url": None, "video_explainer_url": None},
        "tags": []
    }

# --- State Initialization ---
if 'data' not in st.session_state:
    st.session_state.data = get_empty_schema()

# --- UI: Sidebar ---
st.sidebar.title("Data Management")
uploaded_file = st.sidebar.file_uploader("Load Schema YAML", type=["yaml"])
if uploaded_file:
    st.session_state.data = yaml.safe_load(uploaded_file)

# --- UI: Main Generation ---
st.title("Physics Question Generator")
prompt = st.text_area("Question Prompt", height=100, 
                     help="Ask for a question, e.g., 'Calculate the kinetic energy of a 5kg mass moving at 10m/s.'")

if st.button("Generate Question"):
    with st.spinner("Generating with Gemini..."):
        # Contextual prompt
        query = (f"Generate a physics question based on: {prompt}. "
                 "Output strictly in valid YAML matching this exact schema: "
                 f"{st.session_state.data}. Return ONLY the YAML.")
        
        response = model.generate_content(query)
        
        # Clean response and format superscripts
        raw_yaml = response.text.replace('```yaml', '').replace('```', '')
        formatted_yaml = format_superscripts(raw_yaml)
        
        st.session_state.data = yaml.safe_load(formatted_yaml)
        st.success("Generation complete!")

# --- UI: Editor ---
st.subheader("Edit Question Data")
with st.expander("Editor Fields", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.data['id'] = st.text_input("ID", st.session_state.data['id'])
        st.session_state.data['metadata']['topic'] = st.text_input("Topic", st.session_state.data['metadata']['topic'])
    with col2:
        st.session_state.data['metadata']['marks'] = st.number_input("Marks", st.session_state.data['metadata']['marks'])
    
    st.session_state.data['question']['text'] = st.text_area("Question Text", st.session_state.data['question']['text'])
    st.session_state.data['solution']['final_answer'] = st.text_input("Final Answer", st.session_state.data['solution']['final_answer'])

# --- UI: Export ---
st.subheader("YAML Output")
yaml_output = yaml.dump(st.session_state.data, sort_keys=False)
st.code(yaml_output, language='yaml')

st.download_button(
    label="Download YAML",
    data=yaml_output,
    file_name=f"{st.session_state.data['id']}.yaml",
    mime="text/yaml"
)
