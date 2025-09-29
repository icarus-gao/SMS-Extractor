import os, json, sys, time
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from typing import List
import streamlit as st
from utils.extractor import run_extraction, append_outputs
from utils.extractor import read_yaml
from utils.extractor import guess_title_from_citation
from utils.db import (
    init_db,
    insert_or_update_paper,
    add_extraction,
    list_papers,
    list_extractions,
    get_paper,
    get_paper_by_sha,
    delete_extraction,
    delete_paper,
    rename_paper_id,
    upsert_project,
    list_projects,
    get_project,
    delete_project,
    upsert_project_group,
    list_project_groups,
    delete_project_group,
    _connect,
)
from datetime import datetime
import hashlib

# Auto-load .env
load_dotenv(find_dotenv())

st.set_page_config(
    page_title="Data Extractor with LLM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📊 Data Extractor with LLM")
st.caption("AI-powered literature data extraction with project management")

# Top-right connection test
hdr_l, hdr_r = st.columns([6,1])
with hdr_r:
    try:
        import httpx
        r = httpx.get("https://httpbin.org/status/200", timeout=2)
        st.success("🌐 Connected")
    except Exception:
        st.error("❌ No connection")
        st.write("Check `.env`/network/BASE_URL and consider Python 3.11.")

# Init DB
db_path = init_db()

# Optional: override from Streamlit secrets
try:
    if "openai" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["openai"].get("api_key", os.getenv("OPENAI_API_KEY",""))
    for key in ["OPENAI_MODEL","OPENAI_BASE_URL"]:
        if key in st.secrets:
            os.environ[key] = st.secrets.get(key, os.getenv(key,""))
except Exception:
    pass

# Guard: require key for extraction/repository actions only
has_api_key = bool(os.getenv("OPENAI_API_KEY"))

st.sidebar.header("Settings")
st.sidebar.caption(f"Python: {sys.version.split()[0]} (3.11 recommended)")

# Database status - simplified check
try:
    # Check database file exists
    if os.path.exists(db_path):
        st.sidebar.success("✅ Database ready")
    else:
        st.sidebar.warning("Database not found")
        st.sidebar.info("Will be created automatically")
except Exception as e:
    st.sidebar.error(f"Database issue: {str(e)[:20]}...")
    st.sidebar.info("Try refreshing the page")

# App sections in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Project Management")

# Project selector
projects = list_projects(db_path)
if projects:
    # Only show project name if it's different from project_id, otherwise just show the name
    project_options = []
    for p in projects:
        if p['name'] != p['project_id']:
            project_options.append(f"{p['name']} ({p['project_id']})")
        else:
            project_options.append(p['name'])
    
    selected_project_idx = st.sidebar.selectbox("Select Project", range(len(project_options)), format_func=lambda x: project_options[x])
    selected_project = projects[selected_project_idx] if selected_project_idx is not None else None
else:
    selected_project = None
    st.sidebar.info("No projects yet. Create your first project below.")

# Project actions
st.sidebar.markdown("#### Project Actions")
if st.sidebar.button("🆕 Create New Project"):
    st.session_state.show_create_project = True
if st.sidebar.button("📊 Project Analytics"):
    st.session_state.show_analytics = True

# Help section
st.sidebar.markdown("---")
with st.sidebar.expander("💡 Help"):
    st.markdown("""
    **Complete Workflow in Projects:**
    1. **Create Project** - Set up extraction strategy
    2. **Upload Papers** - Add PDFs to your project
    3. **Run Extraction** - Extract data from papers
    4. **View Analytics** - Analyze results and statistics
    
    **Tips:**
    - Each project is self-contained
    - Projects define extraction strategy
    - Attribute groups reduce token costs
    - Batch extraction for efficiency
    """)

# defaults to avoid NameError when switching sections
run_btn = False
citation = ""
pdf_file = None
paper_id = ""

# Load field profiles
def load_field_list(codebook_path: str, profile_name: str) -> List[str]:
    cfg = read_yaml(codebook_path)
    if profile_name == "Full Schema":
        return [f["name"] for f in cfg["fields"]]
    profiles = cfg.get("profiles", {})
    if profile_name not in profiles:
        return [f["name"] for f in cfg["fields"]]
    subset = profiles[profile_name]
    names = [f["name"] for f in cfg["fields"]]
    if subset:
        names = [n for n in names if n in subset]
    return names

codebook_path = str(Path("config/codebook.yaml").resolve())
template_path = str(Path("prompts/extract.j2").resolve())
master_csv   = str(Path("data/master.csv").resolve())
evidence_csv = str(Path("data/evidence_log.csv").resolve())

# Load profiles
profiles = {
    "Full Schema": [],
    "Only Classification": [],
    "Only RQ1": [],
    "Only RQ2": [],
    "Only RQ3": [],
    "Only RQ4": [],
    "Only RQ5": [],
    "Only RQ6": [],
}

# 将 venue.trust_rating 纳入通用 Profile（Only Classification / RQ3等不强制）
profiles["Only Classification"].append("venue.trust_rating")

# Main interface based on selected project
if selected_project is None:
    # No project selected - show welcome/create project
    st.subheader("📋 Welcome to Data Extractor")
    st.caption("Create and manage your extraction projects. Each project defines a specific extraction strategy.")
    
    if not projects:
        st.info("🎯 **Welcome!** Let's create your first project to get started.")
        st.markdown("""
        **What is a project?**
        - A project defines your extraction strategy (what fields to extract)
        - You can have multiple projects for different research questions
        - Each project can have multiple attribute groups (field subsets)
        - Papers can be reused across different projects
        """)
    else:
        st.info("👆 **Please select a project from the sidebar to get started.**")
        st.markdown("### Available Projects:")
        for project in projects:
            with st.expander(f"📁 {project['name']} ({project['project_id']})"):
                st.write(f"**Description:** {project['notes'] or 'No description'}")
                st.write(f"**Model:** {project['model']}")
                st.write(f"**Created:** {datetime.fromtimestamp(project['created_at']).strftime('%Y-%m-%d %H:%M')}")
else:
    # Project selected - show project interface
    st.subheader(f"📁 {selected_project['name']}")
    st.caption(f"Project ID: {selected_project['project_id']}")
    
    # Project tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Papers", "🔍 Extraction", "📊 Analytics", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### 📄 Papers Management")
        st.caption("Upload and manage papers for this project")
        
        # Zotero import section
                # Zotero import removed by user request
        with st.expander("📤 Upload Papers", expanded=True):
            uploaded_files = st.file_uploader(
                f"Upload PDF files for {selected_project['name']}", 
                type=["pdf"], 
                accept_multiple_files=True, 
                key=f"upload_{selected_project['project_id']}"
            )
            if uploaded_files:
                for pdf_file in uploaded_files:
                    # Generate paper_id if not provided
                    paper_id = f"{selected_project['project_id']}-{int(time.time())}"
                    citation = f"Uploaded: {pdf_file.name}"
                    
                    # Save PDF to project's papers directory
                    project_dir = Path(selected_project['codebook_path']).parent.parent
                    papers_dir = project_dir / "papers"
                    papers_dir.mkdir(parents=True, exist_ok=True)
                    tmp_path = papers_dir / pdf_file.name
                    with open(tmp_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    
                    pdf_sha = hashlib.sha256(pdf_file.getbuffer()).hexdigest()
                    
                    # Check for duplicates
                    existing = get_paper_by_sha(db_path, pdf_sha)
                    if existing:
                        st.warning(f"PDF already exists as paper_id: {existing['paper_id']}")
                        continue
                    
                    # Insert paper
                    insert_or_update_paper(db_path, paper_id, citation, str(tmp_path), title=None, pdf_sha256=pdf_sha)
                    st.success(f"Uploaded: {pdf_file.name} as {paper_id}")
        
        # Display papers for this project
        project_papers = []
        all_papers = list_papers(db_path)
        for paper in all_papers:
            # Check if this paper belongs to this project (by paper_id prefix or by extraction records)
            if paper['paper_id'].startswith(selected_project['project_id'] + '-'):
                project_papers.append(paper)
            else:
                # Check if there are extractions for this paper in this project
                with _connect(db_path) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM extractions WHERE paper_id = ? AND project_id = ?", 
                             (paper['paper_id'], selected_project['project_id']))
                    if c.fetchone()[0] > 0:
                        project_papers.append(paper)
        
        if project_papers:
            st.write(f"**Papers in {selected_project['name']}:**")
            for paper in project_papers:
                with st.expander(f"{paper['paper_id']}: {paper['title'] or '(no title)'}", expanded=False):
                    st.write(f"**Citation:** {paper['citation']}")
                    st.write(f"**PDF:** {paper['pdf_path']}")
                    st.write(f"**Created:** {datetime.fromtimestamp(paper['created_at']).strftime('%Y-%m-%d %H:%M')}")
                    
                    # Management buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Rename {paper['paper_id']}", key=f"rename_{paper['paper_id']}"):
                            new_id = st.text_input("New paper_id", value=paper['paper_id'], key=f"new_id_{paper['paper_id']}")
                            if st.button("Confirm", key=f"confirm_rename_{paper['paper_id']}"):
                                # Update paper_id in papers table
                                with _connect(db_path) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE papers SET paper_id = ? WHERE paper_id = ?", (new_id, paper['paper_id']))
                                    c.execute("UPDATE extractions SET paper_id = ? WHERE paper_id = ?", (new_id, paper['paper_id']))
                                    conn.commit()
                                st.success(f"Renamed to {new_id}")
                                st.rerun()
                    
                    with col2:
                        if st.button(f"Delete {paper['paper_id']}", key=f"delete_{paper['paper_id']}"):
                            delete_paper = st.checkbox("Also delete PDF file", key=f"delete_pdf_{paper['paper_id']}")
                            if st.button("Confirm Delete", key=f"confirm_delete_{paper['paper_id']}"):
                                # Delete from database
                                with _connect(db_path) as conn:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM extractions WHERE paper_id = ?", (paper['paper_id'],))
                                    c.execute("DELETE FROM papers WHERE paper_id = ?", (paper['paper_id'],))
                                    conn.commit()
                                
                                # Delete PDF file if requested
                                if delete_paper and paper['pdf_path'] and Path(paper['pdf_path']).exists():
                                    Path(paper['pdf_path']).unlink()
                                
                                st.success(f"Deleted {paper['paper_id']}")
                                st.rerun()
        else:
            st.info(f"No papers uploaded for {selected_project['name']} yet.")
    
    with tab2:
        st.markdown("### 🔍 Data Extraction")
        st.caption("Extract data from papers using AI")
        
        # Get papers for this project
        project_papers = []
        all_papers = list_papers(db_path)
        for paper in all_papers:
            if paper['paper_id'].startswith(selected_project['project_id'] + '-'):
                project_papers.append(paper)
            else:
                with _connect(db_path) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM extractions WHERE paper_id = ? AND project_id = ?", 
                             (paper['paper_id'], selected_project['project_id']))
                    if c.fetchone()[0] > 0:
                        project_papers.append(paper)
        
        if project_papers:
            st.info("Single paper extraction functionality will be implemented here.")
        else:
            st.info("Upload some papers first to run extraction.")
    
    with tab3:
        st.markdown("### 📊 Project Analytics")
        st.caption("View extraction statistics and results")
        
        # Get project-specific analytics
        with _connect(db_path) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT e.*, p.title, p.citation
                FROM extractions e
                LEFT JOIN papers p ON e.paper_id = p.paper_id
                WHERE e.project_id = ?
                ORDER BY e.created_at DESC
            """, (selected_project['project_id'],))
            project_extractions = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
        
        # Get project papers count
        project_papers = []
        all_papers = list_papers(db_path)
        for paper in all_papers:
            if paper['paper_id'].startswith(selected_project['project_id'] + '-'):
                project_papers.append(paper)
            else:
                with _connect(db_path) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM extractions WHERE paper_id = ? AND project_id = ?", 
                             (paper['paper_id'], selected_project['project_id']))
                    if c.fetchone()[0] > 0:
                        project_papers.append(paper)
        
        if project_extractions:
            # Summary statistics
            total_extractions = len(project_extractions)
            successful_extractions = len([e for e in project_extractions if e['status'] == 'success'])
            error_extractions = len([e for e in project_extractions if e['status'] == 'error'])
            success_rate = (successful_extractions / total_extractions * 100) if total_extractions > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Extractions", total_extractions)
            with col2:
                st.metric("Successful", successful_extractions, delta=f"{success_rate:.1f}%")
            with col3:
                st.metric("Errors", error_extractions)
            with col4:
                st.metric("Papers", len(project_papers))
            
            # Recent extractions
            st.markdown("**Recent Extractions:**")
            for ext in project_extractions[:5]:  # Show last 5
                with st.expander(f"{ext['paper_id']} - {ext.get('title', 'No title')} ({ext['status']})"):
                    st.write(f"**Date:** {datetime.fromtimestamp(ext['created_at']).strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Model:** {ext.get('model', 'Unknown')}")
                    st.write(f"**Profile:** {ext.get('profile', 'Unknown')}")
                    if ext['status'] == 'error' and ext.get('error_msg'):
                        st.error(f"Error: {ext['error_msg']}")
                    elif ext['status'] == 'success' and ext.get('result_json'):
                        try:
                            result = json.loads(ext['result_json'])
                            st.write("**Extracted Fields:**")
                            st.json({k: v for k, v in list(result.items())[:3]})  # Show first 3 fields
                            if len(result) > 3:
                                st.write(f"... and {len(result) - 3} more fields")
                        except:
                            st.text("Could not parse result JSON")
        else:
            st.info("No extractions for this project yet.")
            st.metric("Papers", len(project_papers))
    
    with tab4:
        st.markdown("### ⚙️ Project Settings")
        st.caption("Configure project settings and manage files")
        st.info("Settings functionality will be implemented here.")

# Show create project form if requested
if st.session_state.get('show_create_project', False):
    st.markdown("---")
    st.subheader("🆕 Create New Project")
    
    # Quick templates for common use cases
    if not projects:
        st.markdown("**Quick Start Templates:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Literature Review", help="For systematic literature review"):
                st.session_state.quick_template = "literature_review"
        with col2:
            if st.button("🔬 Algorithm Analysis", help="For BFT algorithm analysis"):
                st.session_state.quick_template = "algorithm_analysis"
        with col3:
            if st.button("📊 Custom Project", help="Create from scratch"):
                st.session_state.quick_template = "custom"
    
    with st.form("create_project"):
        # Auto-fill based on template
        if hasattr(st.session_state, 'quick_template'):
            if st.session_state.quick_template == "literature_review":
                project_name = "Literature Review"
                notes = "Systematic literature review project"
            elif st.session_state.quick_template == "algorithm_analysis":
                project_name = "Algorithm Analysis"
                notes = "BFT algorithm analysis project"
            else:
                project_name = ""
                notes = ""
        else:
            project_name = ""
            notes = ""
        
        project_name = st.text_input("Project Name", value=project_name)
        
        # File uploads for codebook and prompt
        st.markdown("**Upload Configuration Files:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Codebook (YAML)**")
            codebook_file = st.file_uploader("Upload Codebook", type=["yaml", "yml"], key="codebook_upload")
        
        with col2:
            st.markdown("**Prompt Template (Jinja2)**")
            prompt_file = st.file_uploader("Upload Prompt Template", type=["j2", "txt"], key="prompt_upload")
        
        model = st.text_input("Default Model", value="gpt-5")
        notes = st.text_area("Notes", value=notes)
        
        if st.form_submit_button("Create Project"):
            if project_name:
                # Generate project_id from project_name
                import re
                project_id = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name.lower()).strip('-')
                if not project_id:
                    project_id = f"project-{int(time.time())}"
                
                # Create project directory structure
                project_dir = Path(f"data/projects/{project_id}")
                project_dir.mkdir(parents=True, exist_ok=True)
                
                # Create subdirectories
                (project_dir / "config").mkdir(exist_ok=True)
                (project_dir / "data").mkdir(exist_ok=True)
                (project_dir / "prompts").mkdir(exist_ok=True)
                (project_dir / "papers").mkdir(exist_ok=True)
                
                # Handle file uploads
                project_codebook = str(project_dir / "config" / "codebook.yaml")
                project_prompt = str(project_dir / "prompts" / "extract.j2")
                
                # Save uploaded files or use defaults
                if codebook_file:
                    with open(project_codebook, "wb") as f:
                        f.write(codebook_file.getbuffer())
                    st.success("✅ Codebook uploaded")
                else:
                    # Use default codebook
                    import shutil
                    if os.path.exists("config/codebook.yaml"):
                        shutil.copy("config/codebook.yaml", project_codebook)
                    else:
                        st.warning("⚠️ No codebook uploaded and no default found")
                
                if prompt_file:
                    with open(project_prompt, "wb") as f:
                        f.write(prompt_file.getbuffer())
                    st.success("✅ Prompt template uploaded")
                else:
                    # Use default prompt
                    import shutil
                    if os.path.exists("prompts/extract.j2"):
                        shutil.copy("prompts/extract.j2", project_prompt)
                    else:
                        st.warning("⚠️ No prompt uploaded and no default found")
                
                # Create project in database
                upsert_project(db_path, project_id, project_name, project_codebook, project_prompt, model, notes)
                st.success(f"Created project: {project_name}")
                st.info(f"Project directory: {project_dir}")
                # Clear template selection
                if hasattr(st.session_state, 'quick_template'):
                    del st.session_state.quick_template
                st.rerun()
            else:
                st.error("Project name is required")
    
    # Clear the create project flag
    if st.button("Cancel"):
        st.session_state.show_create_project = False
        st.rerun()

# Show analytics if requested
if st.session_state.get('show_analytics', False):
    st.markdown("---")
    st.subheader("📊 Global Analytics")
    st.info("Global analytics functionality will be implemented here.")
    
    if st.button("Close Analytics"):
        st.session_state.show_analytics = False
        st.rerun()

st.markdown("---")
st.caption("Config priority: secrets.toml > .env. Customize fields in config/codebook.yaml and prompt in prompts/extract.j2.")
