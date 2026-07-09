import streamlit as st
import yaml
from google import genai
from google.genai import types
from github import Github
import os
import pandas as pd
import io
import base64
from PIL import Image

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

# Initialize the new Google GenAI client
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
st.title("Physics Question Generator")
PROMPT_LIBRARY = load_prompt_library()
prompt = st.text_area("Question Prompt", value=PROMPT_LIBRARY[list(PROMPT_LIBRARY.keys())[0]], height=100)

if st.button("Generate Question"):
    with st.spinner("Generating with Gemini 3.1..."):
        query = f"Generate physics question: {prompt}. Output strictly in YAML. Schema: {st.session_state.data}"
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=query
        )
        
        cleaned_yaml = clean_latex(response.text.replace('```yaml', '').replace('```', ''))
        st.session_state.data = yaml.safe_load(format_superscripts(cleaned_yaml))
        st.success("Generation complete!")

# Image Generation
if st.session_state.data.get('media', {}).get('diagram_url'):
    if st.button("Generate Image"):
        with st.spinner("Generating image..."):
            desc = st.session_state.data['media']['diagram_url']
            
            # Using the new SDK's image generation interface
            result = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=f"Physics textbook diagram: {desc}",
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            
            if result.generated_images:
                img_data = result.generated_images[0].image.image_bytes
                st.session_state.generated_image = Image.open(io.BytesIO(img_data)).resize((1024, 1024))

if st.session_state.get('generated_image'):
    st.image(st.session_state.generated_image, caption="Generated Diagram")
