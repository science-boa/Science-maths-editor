import streamlit as st
import yaml
import os
import pandas as pd
import time
import io
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from github import Github
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional, Union

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", ""))

# --- Pydantic Schemas for Strict JSON Structured Outputs ---
class MetadataSchema(BaseModel):
    topic: str
    marks: int
    difficulty_level: float

class QuestionSchema(BaseModel):
    text: str
    variables: List[str] = []

class SolutionStepSchema(BaseModel):
    step_number: int
    text: str
    marks_assigned: int
    check_type: str
    milestone_value: float
    tolerance: float

class SolutionSchema(BaseModel):
    final_answer: float
    marks_available: int
    steps: List[SolutionStepSchema]

class MediaSchema(BaseModel):
    diagram_url: Optional[str] = None
    video_explainer_url: Optional[str] = None

class BarDataSchema(BaseModel):
    labels: List[str] = Field(description="List of category labels for the X-axis")
    values: List[float] = Field(description="Numeric values corresponding to each category")

class GraphDatasetPoint(BaseModel):
    x: Union[float, str]
    y: float

class GraphDatasetSchema(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    color: Optional[str] = None
    point_size: Optional[int] = 5
    coordinates: Optional[List[GraphDatasetPoint]] = None
    points: Optional[List[GraphDatasetPoint]] = None

class AxesGridConfig(BaseModel):
    present: bool = True
    color: str = "#000000"
    opacity: float = 1.0
    style: Optional[str] = "solid"
    divisions: Optional[int] = 5

class AxesConfig(BaseModel):
    xmin: Optional[float] = 0
    xmax: Optional[float] = 100
    xtick_distance: Optional[float] = 20
    ymin: Optional[float] = None
    ymax: Optional[float] = None
    ytick_distance: Optional[float] = None
    x_major_grid: Optional[AxesGridConfig] = None
    y_major_grid: Optional[AxesGridConfig] = None
    x_minor_grid: Optional[AxesGridConfig] = None
    y_minor_grid: Optional[AxesGridConfig] = None

class GraphSchema(BaseModel):
    type: str = Field(description="Must be 'bar', 'scatter', or 'line'")
    title: str
    xlabel: str
    ylabel: str
    axes: Optional[AxesConfig] = None
    data: Optional[BarDataSchema] = None
    datasets: Optional[List[GraphDatasetSchema]] = None

class PhysicsQuestionSchema(BaseModel):
    id: str
    metadata: MetadataSchema
    question: QuestionSchema
    solution: SolutionSchema
    media: Optional[MediaSchema] = None
    graph: Optional[GraphSchema] = None
    tags: List[str] = []


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

def push_to_github(filename, content, subdir="Q", is_image=False, image_data=None):
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

def render_yaml_graph_to_image(graph_data):
    """
    Parses scientific graph dictionary and renders it as a matplotlib figure,
    returning bytes of the PNG image restricted to 800x600 pixels.
    """
    if not isinstance(graph_data, dict):
        raise ValueError(f"Invalid graph content: expected dictionary schema, got {type(graph_data).__name__}.")
        
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    
    g_type = graph_data.get('type', 'bar')
    title = graph_data.get('title', '')
    xlabel = graph_data.get('xlabel', '')
    ylabel = graph_data.get('ylabel', '')
    
    axes_cfg = graph_data.get('axes', {}) or {}
    ymin = axes_cfg.get('ymin')
    ymax = axes_cfg.get('ymax')
    xmin = axes_cfg.get('xmin')
    xmax = axes_cfg.get('xmax')
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, fontweight='semibold')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, fontweight='semibold')
        
    if g_type == 'bar':
        labels, values = [], []
        fill_color, border_color = '#000000', '#000000'
        
        if graph_data.get('data'):
            data_block = graph_data.get('data', {})
            labels = data_block.get('labels', [])
            values = data_block.get('values', [])
        elif graph_data.get('datasets'):
            ds = graph_data['datasets'][0]
            raw_vals = ds.get('values', ds.get('coordinates', ds.get('points', [])))
            if raw_vals:
                if isinstance(raw_vals[0], (list, tuple)):
                    labels = [str(item[0]) for item in raw_vals]
                    values = [item[1] for item in raw_vals]
                elif isinstance(raw_vals[0], dict):
                    labels = [str(item.get('x', item.get('label', ''))) for item in raw_vals]
                    values = [item.get('y', item.get('value', 0)) for item in raw_vals]
            fill_color = ds.get('color', '#000000')
            
        x_indexes = np.arange(len(labels)) + 0.5
        ax.bar(x_indexes, values, color=fill_color, edgecolor=border_color, width=0.6)
        
        ax.set_xticks(x_indexes)
        ax.set_xticklabels(labels)
        ax.set_xlim(0, len(labels) + 1.0)
        
    elif g_type in ['scatter', 'line', 'mixed']:
        datasets = graph_data.get('datasets', [])
        if not datasets and graph_data.get('data'):
            datasets = [{'name': 'Data', 'type': g_type, 'coordinates': graph_data.get('data', {}).get('coordinates', graph_data.get('data', {}).get('values', []))}]
            
        for ds in datasets:
            ds_name = ds.get('name', ds.get('label', ''))
            ds_type = ds.get('type', g_type)
            ds_color = ds.get('color', '#000000')
            pt_size = ds.get('point_size', 5)
            
            coords = ds.get('coordinates', ds.get('points', ds.get('values', [])))
            
            xs, ys = [], []
            if coords:
                if isinstance(coords[0], dict) and 'x' in coords[0] and 'y' in coords[0]:
                    xs = [pt['x'] for pt in coords]
                    ys = [pt['y'] for pt in coords]
                else:
                    xs = [pt[0] for pt in coords]
                    ys = [pt[1] for pt in coords]
            elif 'x' in ds and 'y' in ds:
                xs = ds['x']
                ys = ds['y']
                
            if xs and ys:
                if ds_type == 'scatter':
                    ax.scatter(xs, ys, label=ds_name, color=ds_color, s=pt_size*10, zorder=3)
                else:
                    ax.plot(xs, ys, label=ds_name, color=ds_color, linewidth=2, linestyle='-', marker='o' if g_type=='line' else None, markersize=(pt_size**0.5)*1.5, zorder=2)
                    
        if len(datasets) > 1 or (datasets and (datasets[0].get('name') or datasets[0].get('label'))):
            ax.legend(frameon=True, facecolor='white', edgecolor='#e5e7eb', fontsize=9)

    if ymin is not None or ymax is not None:
        ax.set_ylim(bottom=ymin, top=ymax)
    if xmin is not None or xmax is not None:
        ax.set_xlim(left=xmin, right=xmax)
        
    ytick_dist = axes_cfg.get('ytick_distance')
    if ytick_dist is None and ymin is not None and ymax is not None:
        ytick_dist = (ymax - ymin) / 5.0
    if ytick_dist and ymin is not None and ymax is not None:
        ax.set_yticks(np.arange(ymin, ymax + ytick_dist * 0.1, ytick_dist))
        
    xtick_dist = axes_cfg.get('xtick_distance')
    if xtick_dist is None and xmin is not None and xmax is not None:
        xtick_dist = (xmax - xmin) / 5.0
    if g_type == 'bar' and xtick_dist is None:
        xtick_dist = 1.0
        
    if g_type != 'bar' and xtick_dist and xmin is not None and xmax is not None:
        ax.set_xticks(np.arange(xmin, xmax + xtick_dist * 0.1, xtick_dist))

    # Gridlines configuration
    ax.xaxis.grid(True, which='major', color='#000000', alpha=1.0, linestyle='solid', linewidth=0.7)
    ax.yaxis.grid(True, which='major', color='#000000', alpha=1.0, linestyle='solid', linewidth=0.7)
    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.xaxis.grid(True, which='minor', color='#000000', alpha=1.0, linestyle='dashed', linewidth=0.5)
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.grid(True, which='minor', color='#000000', alpha=1.0, linestyle='dashed', linewidth=0.5)
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#000000')
    ax.spines['bottom'].set_color('#000000')
    
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()

def get_empty_schema_dict():
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
        "graph": None,
        "tags": []
    }

# Safely initialize session state data
if 'data' not in st.session_state or not isinstance(st.session_state.data, dict):
    st.session_state.data = get_empty_schema_dict()

# Ensure nested keys are never None if loaded from an incomplete YAML file
if st.session_state.data.get('media') is None:
    st.session_state.data['media'] = {"diagram_url": None, "video_explainer_url": None}
if st.session_state.data.get('metadata') is None:
    st.session_state.data['metadata'] = {"topic": "", "marks": 4, "difficulty_level": 0.5}
if st.session_state.data.get('question') is None:
    st.session_state.data['question'] = {"text": "", "variables": []}
if st.session_state.data.get('solution') is None:
    st.session_state.data['solution'] = {"final_answer": 0.0, "marks_available": 4, "steps": []}

def generate_question(prompt_text, force_image=False, force_graph=False, unit_conv=False, std_form=False, inc_eq=False):
    with st.spinner("Generating structured output..."):
        extra_instr = " You MUST include a detailed descriptive text for a diagram in the 'diagram_url' field." if force_image else ""
        graph_instr = " You MUST include a structured graph object under the top-level 'graph' key following the schema requirements." if force_graph else ""
        
        latex_instr = " All mathematical expressions and scientific notation MUST be formatted in LaTeX (e.g., $E=mc^2$)."
        conv_instr = " include one unit that must be converted to its base unit in the question." if unit_conv else " do not use unit conversions."
        std_form_instr = " give one value as standard form." if std_form else ""
        eq_instr = " include the equations needed in the question text." if inc_eq else ""
        
        query = (f"Generate a physics question based on: {prompt_text}.{latex_instr} "
                 f"{conv_instr} {std_form_instr} {eq_instr}{extra_instr}{graph_instr}")
        
        try:
            # Enforce structured output constraint via Pydantic model and JSON mime type
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=query,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': PhysicsQuestionSchema,
                }
            )
            
            # response.parsed gives back a validated Pydantic object, which we convert to dict
            parsed_obj = response.parsed
            if isinstance(parsed_obj, PhysicsQuestionSchema):
                parsed_data = parsed_obj.model_dump()
            else:
                import json
                parsed_data = json.loads(response.text)
                
            st.session_state.data = parsed_data
            st.session_state.image_prompt = None
            st.session_state.pushed_graph_id = None
            st.success("Generation complete!")
        except Exception as e:
            st.error(f"Generation failed: {e}")

st.sidebar.title("Data Management")
uploaded_file = st.sidebar.file_uploader("Load Schema YAML", type=["yaml"])
if uploaded_file:
    loaded_data = yaml.safe_load(uploaded_file)
    if isinstance(loaded_data, dict):
        st.session_state.data = loaded_data
        if st.session_state.data.get('media') is None:
            st.session_state.data['media'] = {"diagram_url": None, "video_explainer_url": None}
        if st.session_state.data.get('metadata') is None:
            st.session_state.data['metadata'] = {"topic": "", "marks": 4, "difficulty_level": 0.5}
        if st.session_state.data.get('question') is None:
            st.session_state.data['question'] = {"text": "", "variables": []}
        if st.session_state.data.get('solution') is None:
            st.session_state.data['solution'] = {"final_answer": 0.0, "marks_available": 4, "steps": []}

st.sidebar.title("Prompt Library")
PROMPT_LIBRARY = load_prompt_library()
selected_key = st.sidebar.selectbox("Select a Prompt Type", list(PROMPT_LIBRARY.keys()))

st.title("Physics Question Generator")
prompt = st.text_area("Question Prompt", value=PROMPT_LIBRARY[selected_key])

col_t1, col_t2, col_t3 = st.columns(3)
with col_t1:
    unit_conv = st.toggle("Unit Conversions")
with col_t2:
    std_form = st.toggle("Standard Form")
with col_t3:
    inc_eq = st.toggle("Include Equation")

col_gen1, col_gen2, col_gen3 = st.columns(3)
with col_gen1:
    if st.button("Generate Question"):
        generate_question(prompt, force_image=False, force_graph=False, unit_conv=unit_conv, std_form=std_form, inc_eq=inc_eq)
with col_gen2:
    if st.button("Generate Question with Image"):
        generate_question(prompt, force_image=True, force_graph=False, unit_conv=unit_conv, std_form=std_form, inc_eq=inc_eq)
with col_gen3:
    if st.button("Generate with Graph"):
        generate_question(prompt, force_image=False, force_graph=True, unit_conv=unit_conv, std_form=std_form, inc_eq=inc_eq)

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
        
        if 'media' not in st.session_state.data or st.session_state.data['media'] is None:
            st.session_state.data['media'] = {}
        
        st.session_state.data['media']['diagram_url'] = f"I/{q_id}.png"
        
        if uploaded_image:
            ext = uploaded_image.name.split('.')[-1]
            push_to_github(f"{q_id}.{ext}", None, subdir="I", is_image=True, image_data=uploaded_image.getvalue())
            time.sleep(1)
        
        payload_to_push = dict(st.session_state.data)
        graph_data = payload_to_push.pop('graph', None)
        
        has_graph = graph_data is not None
        if has_graph:
            if not isinstance(graph_data, dict):
                graph_data = {}
            
            graph_yaml_str = yaml.dump(graph_data, sort_keys=False)
            push_to_github(f"{q_id}.yaml", graph_yaml_str, subdir="G")
            st.session_state.pushed_graph_id = q_id
            time.sleep(1)
        else:
            st.session_state.pushed_graph_id = None
        
        question_yaml_str = yaml.dump(payload_to_push, sort_keys=False)
        push_to_github(f"{q_id}.yaml", question_yaml_str, subdir="Q")
        st.success("Successfully pushed question and graph to GitHub!")

if st.session_state.get('pushed_graph_id'):
    pushed_id = st.session_state.pushed_graph_id
    st.divider()
    st.subheader(f"Graph Rendering & Image Export for {pushed_id}")
    
    try:
        g_client = Github(st.secrets["GITHUB_TOKEN"])
        g_repo = g_client.get_repo(st.secrets["GITHUB_REPO"])
        file_contents = g_repo.get_contents(f"G/{pushed_id}.yaml")
        yaml_content = file_contents.decoded_content.decode("utf-8")
        
        col_img, col_controls = st.columns([2, 1])
        
        with col_controls:
            st.markdown("### Graph YAML Content")
            updated_graph_yaml = st.text_area("YAML Code", value=yaml_content, height=300, key=f"yaml_view_{pushed_id}")
        
        try:
            parsed_graph = yaml.safe_load(updated_graph_yaml)
        except Exception as parse_err:
            parsed_graph = None
            st.error(f"YAML Syntax Error: {parse_err}")

        with col_img:
            if isinstance(parsed_graph, dict):
                image_bytes = render_yaml_graph_to_image(parsed_graph)
                st.image(image_bytes, caption=f"Rendered Graph for {pushed_id}", use_container_width=True)
                
                if st.button("Push updated image & YAML to GitHub"):
                    push_to_github(f"{pushed_id}.yaml", updated_graph_yaml, subdir="G")
                    push_to_github(f"{pushed_id}.png", None, subdir="I", is_image=True, image_data=image_bytes)
                    st.success(f"Updated graph successfully pushed to GitHub!")
            else:
                st.warning("Please enter a valid graph dictionary YAML schema to render the preview.")
            
        st.divider()
        st.markdown("### Scientific Graph Keys & Syntax Reference")
        if os.path.exists("graph_keys_reference.md"):
            with open("graph_keys_reference.md", "r") as ref_file:
                st.markdown(ref_file.read())
        else:
            st.warning("Reference guide file `graph_keys_reference.md` not found.")
            
    except Exception as e:
        st.warning(f"Could not load `G/{pushed_id}.yaml` from GitHub yet: {e}")
