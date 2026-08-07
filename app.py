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

# --- Embedded Reference Documentation ---
EMBEDDED_GRAPH_REFERENCE = """# Scientific Graph Keys and Syntax Reference

This reference guide lists all the configuration keys, data structures, and syntax rules used by the `render_yaml_graph_to_image` function in your Physics Question Generator application.

## 1. Top-Level Graph Keys

Every scientific graph object defined under the top-level `graph` key in a question YAML file supports the following properties:

| Key | Type | Description |
| --- | --- | --- |
| `type` | String | Defines the chart type. Options: `'bar'`, `'scatter'`, `'line'`, or `'mixed'`. |
| `title` | String | The title displayed at the top of the rendered graph figure. |
| `xlabel` | String | The label displayed along the horizontal ($X$) axis. |
| `ylabel` | String | The label displayed along the vertical ($Y$) axis. |
| `axes` | Dictionary | Configuration block for axis limits, major/minor gridlines, and tick spacings. |
| `data` | Dictionary | Primary data block (used for simple bar charts or single-series data). |
| `datasets` | List of Dictionaries | Multi-series data block (used for scatter plots with separate data points and lines of best fit). |

## 2. Axes Configuration (`axes`)

The `axes` dictionary fine-tunes the plotting area, tick mark intervals, and gridline behaviors:

| Key | Type | Description |
| --- | --- | --- |
| `ymin` | Float / Int | Minimum value for the vertical ($Y$) axis. |
| `ymax` | Float / Int | Maximum value for the vertical ($Y$) axis. |
| `xmin` | Float / Int | Minimum value for the horizontal ($X$) axis. |
| `xmax` | Float / Int | Maximum value for the horizontal ($X$) axis. |
| `ytick_distance` | Float / Int | Step size interval for major tick marks on the $Y$ axis. |
| `xtick_distance` | Float / Int | Step size interval for major tick marks on the $X$ axis. |
| `x_major_grid` | Dictionary | Configuration for $X$-axis major grid lines. |
| `y_major_grid` | Dictionary | Configuration for $Y$-axis major grid lines. |
"""

EMBEDDED_DEFAULT_PROMPTS = [
    "Act as an expert GCSE Physics examiner. Generate a calculation question involving force, mass, and acceleration.",
    "Act as an expert GCSE Physics examiner. Generate a graph analysis question involving Hooke's law and extension.",
    "Act as an expert GCSE Physics examiner. Generate a energy calculation question involving specific heat capacity.",
    "Act as an expert GCSE Physics examiner. Generate a wave equation calculation question involving frequency and wavelength."
]

# --- Configuration ---
st.set_page_config(page_title="Physics Question Generator", layout="wide")

client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", ""))

def clean_latex(text):
    return text.replace('\\\\', '\\')

def load_prompt_library():
    # Load prompts from embedded list instead of prompts.csv
    return {f"{i+1}: {p[:40]}...": p for i, p in enumerate(EMBEDDED_DEFAULT_PROMPTS)}

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
    Parses scientific graph YAML schema and renders it as a matplotlib figure,
    returning bytes of the PNG image restricted to 800x600 pixels.
    """
    if not isinstance(graph_data, dict):
        raise ValueError(f"Invalid graph YAML content: expected dictionary schema, got {type(graph_data).__name__}.")
        
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    
    g_type = graph_data.get('type', 'bar')
    title = graph_data.get('title', '')
    xlabel = graph_data.get('xlabel', '')
    ylabel = graph_data.get('ylabel', '')
    
    axes_cfg = graph_data.get('axes', {})
    ymin = axes_cfg.get('ymin')
    ymax = axes_cfg.get('ymax')
    xmin = axes_cfg.get('xmin')
    xmax = axes_cfg.get('xmax')
    
    x_major_grid = axes_cfg.get('x_major_grid', {'present': True, 'color': '#000000', 'opacity': 1.0})
    y_major_grid = axes_cfg.get('y_major_grid', {'present': True, 'color': '#000000', 'opacity': 1.0})
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, fontweight='semibold')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, fontweight='semibold')
        
    if g_type == 'bar':
        data_block = graph_data.get('data', {})
        labels = data_block.get('labels', [])
        values = data_block.get('values', [])
        styling = data_block.get('styling', {})
        fill_color = styling.get('fill', '#374151')
        border_color = styling.get('border', '#111827')
        
        ax.bar(labels, values, color=fill_color, edgecolor=border_color, width=0.6)
        
    elif g_type in ['scatter', 'line', 'mixed']:
        datasets = graph_data.get('datasets', [])
        if not datasets and 'data' in graph_data:
            datasets = [{'name': 'Data', 'type': g_type, 'coordinates': graph_data.get('data', {}).get('coordinates', graph_data.get('data', {}).get('values', []))}]
            
        for ds in datasets:
            ds_name = ds.get('name', ds.get('label', ''))
            ds_type = ds.get('type', g_type)
            ds_color = ds.get('color', '#2563eb')
            
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
                    pt_radius = ds.get('point_radius', 6)
                    ax.scatter(xs, ys, label=ds_name, color=ds_color, s=pt_radius*10, zorder=3)
                else:
                    lw = ds.get('border_width', 2)
                    ls = '--' if ds.get('border_dash') else '-'
                    ax.plot(xs, ys, label=ds_name, color=ds_color, linewidth=lw, linestyle=ls, marker='o' if g_type=='line' else None, zorder=2)
                    
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
        
    if xtick_dist and xmin is not None and xmax is not None:
        ax.set_xticks(np.arange(xmin, xmax + xtick_dist * 0.1, xtick_dist))

    if x_major_grid.get('present', True):
        ax.xaxis.grid(True, which='major', color=x_major_grid.get('color', '#000000'), alpha=x_major_grid.get('opacity', 1.0), linestyle='-', linewidth=0.7)

    if y_major_grid.get('present', True):
        ax.yaxis.grid(True, which='major', color=y_major_grid.get('color', '#000000'), alpha=y_major_grid.get('opacity', 1.0), linestyle='-', linewidth=0.7)
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#9ca3af')
    ax.spines['bottom'].set_color('#9ca3af')
    
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()

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
        "graph": None,
        "tags": []
    }

def generate_question(prompt_text, force_image=False, force_graph=False, unit_conv=False, std_form=False, inc_eq=False):
    with st.spinner("Generating..."):
        extra_instr = " You MUST include a detailed descriptive text for a diagram in the 'diagram_url' field." if force_image else ""
        graph_instr = (
            " You MUST include a structured graph object under the top-level 'graph' key conforming to the Scientific Graph YAML Schema. "
            "It must include graph 'type' (e.g., 'bar' or 'scatter'), 'title', 'xlabel', 'ylabel', 'axes' configuration (ymin, ymax, ytick_distance, grid), "
            "and 'data' (labels and values) or 'datasets' (for scatter/lines)."
        ) if force_graph else ""
        
        latex_instr = " All mathematical expressions and scientific notation MUST be formatted in LaTeX (e.g., $E=mc^2$)."
        conv_instr = " include one unit that must be converted to its base unit in the question." if unit_conv else " do not use unit conversions."
        std_form_instr = " give one value as standard form." if std_form else ""
        eq_instr = " include the equations needed in the question text." if inc_eq else ""
        
        query = (f"Generate a physics question based on: {prompt_text}.{latex_instr} "
                 f"{conv_instr} {std_form_instr} {eq_instr} "
                 f"Output strictly in valid YAML matching this schema: {st.session_state.data}.{extra_instr}{graph_instr} "
                 "Return ONLY the YAML.")
        
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=query
            )
            raw_text = response.text.replace('```yaml', '').replace('```', '')
            st.session_state.data = yaml.safe_load(clean_latex(raw_text))
            st.session_state.image_prompt = None
            st.session_state.pushed_graph_id = None
            st.success("Generation complete!")
        except Exception as e:
            st.error(f"Generation failed: {e}")

if 'data' not in st.session_state:
    st.session_state.data = get_empty_schema()

st.sidebar.title("Data Management")
uploaded_file = st.sidebar.file_uploader("Load Schema YAML", type=["yaml"])
if uploaded_file:
    st.session_state.data = yaml.safe_load(uploaded_file)

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
            if 'axes' not in graph_data or not isinstance(graph_data['axes'], dict):
                graph_data['axes'] = {}
            
            graph_data['axes']['x_major_grid'] = {
                'present': True,
                'color': '#000000',
                'opacity': 1.0,
                'style': 'solid'
            }
            graph_data['axes']['y_major_grid'] = {
                'present': True,
                'color': '#000000',
                'opacity': 1.0,
                'style': 'solid'
            }
            
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
        parsed_graph = yaml.safe_load(yaml_content)
        
        if not isinstance(parsed_graph, dict):
            st.error(f"Error: `G/{pushed_id}.yaml` loaded from GitHub is not a valid graph dictionary schema...")
        else:
            st.info(f"Loaded `G/{pushed_id}.yaml` successfully from GitHub.")
            
            col_img, col_controls = st.columns([2, 1])
            
            with col_img:
                image_bytes = render_yaml_graph_to_image(parsed_graph)
                st.image(image_bytes, caption=f"Rendered Graph for {pushed_id}", use_container_width=True)
                
                if st.button("Push image to GitHub"):
                    push_to_github(f"{pushed_id}.png", None, subdir="I", is_image=True, image_data=image_bytes)
                    st.success(f"Graph image successfully pushed to `I/{pushed_id}.png`!")

            with col_controls:
                st.markdown("### Graph YAML Content")
                updated_graph_yaml = yaml.dump(parsed_graph, sort_keys=False)
                st.text_area("YAML Code", value=updated_graph_yaml, height=300, key=f"yaml_view_{pushed_id}")
            
            st.divider()
            st.markdown("### Scientific Graph Keys & Syntax Reference")
            # Render embedded reference documentation directly
            st.markdown(EMBEDDED_GRAPH_REFERENCE)
            
    except Exception as e:
        st.warning(f"Could not load `G/{pushed_id}.yaml` from GitHub yet: {e}")
