import os, json, sys, time, re, shutil
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
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
    rename_project_group,
    _connect,
)
from datetime import datetime
import hashlib

from core import (
    DEFAULT_PROFILE_NAME,
    normalize_profile_name,
    resolve_project_dir,
    trigger_rerun,
    replace_bibtex_key,
    extract_title_from_bibtex,
)
from ui import (
    render_papers_tab,
    render_extraction_tab,
    render_analytics_tab,
    render_settings_tab,
    render_project_creation_form,
)



def reset_workspace() -> None:
    """Remove all user data (database, outputs, per-project assets)."""
    targets = [Path("data/app.db"), Path("data/master.csv")]
    directories = [Path("data/projects"), Path("data/config")]

    for target in targets:
        try:
            target.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass

    for directory in directories:
        if directory.exists():
            try:
                shutil.rmtree(directory)
            except Exception:
                pass

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

GLOBAL_CONFIG_DIR = Path("data/config")
GLOBAL_MODEL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "global_models.json"
GLOBAL_MODEL_TEMPLATE_PATH = Path("config/default_global_models.json")


def load_global_model_configs() -> Dict[str, Any]:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not GLOBAL_MODEL_CONFIG_PATH.exists() and GLOBAL_MODEL_TEMPLATE_PATH.exists():
        try:
            GLOBAL_MODEL_CONFIG_PATH.write_text(
                GLOBAL_MODEL_TEMPLATE_PATH.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        except Exception:
            pass
    if GLOBAL_MODEL_CONFIG_PATH.exists():
        try:
            with open(GLOBAL_MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault('models', [])
                    data.setdefault('default_model', 'gpt-5')
                    return data
        except Exception:
            pass
    return {'models': [], 'default_model': 'gpt-5'}


def save_global_model_configs(data: Dict[str, Any]) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_MODEL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_model_config(config: Dict[str, Any], name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    for model in config.get('models', []):
        if model.get('name') == name:
            return model
    return None


def sync_api_settings_from_global() -> None:
    global_conf = st.session_state.get('global_model_configs', {'models': [], 'default_model': 'gpt-5'})
    api_state = st.session_state.setdefault('api_settings', {})
    default_model = global_conf.get('default_model') or api_state.get('default_model') or 'gpt-5'
    api_state['default_model'] = default_model
    model_conf = find_model_config(global_conf, default_model)

    api_key = model_conf.get('api_key') if model_conf else api_state.get('api_key', '')
    base_url = model_conf.get('base_url') if model_conf else api_state.get('base_url', '')
    organization = model_conf.get('organization') if model_conf else api_state.get('organization', '')

    api_state['api_key'] = api_key or api_state.get('api_key', '')
    api_state['base_url'] = base_url or api_state.get('base_url', '')
    api_state['organization'] = organization or api_state.get('organization', '')

    if api_state['api_key']:
        os.environ['OPENAI_API_KEY'] = api_state['api_key']
    if api_state['base_url']:
        os.environ['OPENAI_BASE_URL'] = api_state['base_url']
    else:
        os.environ.pop('OPENAI_BASE_URL', None)
    if api_state['organization']:
        os.environ['OPENAI_ORG'] = api_state['organization']
        os.environ['OPENAI_ORGANIZATION'] = api_state['organization']
    else:
        os.environ.pop('OPENAI_ORG', None)
        os.environ.pop('OPENAI_ORGANIZATION', None)


def render_global_model_settings() -> None:
    st.title("⚙️ Model & API Global Settings")
    st.caption("Manage global model credentials used across every project.")

    global_conf = st.session_state.setdefault('global_model_configs', load_global_model_configs())
    models = global_conf.get('models', [])
    default_model_name = global_conf.get('default_model') or ''

    cols = st.columns([0.2, 0.8])
    with cols[0]:
        if st.button("⬅️ Back to Projects", key="back_to_projects"):
            st.session_state.show_api_settings = False
            trigger_rerun()

    st.markdown("### ➕ Add Model")
    with st.form("add_global_model_form"):
        new_name = st.text_input("Model Name", key="global_add_model_name")
        new_base_url = st.text_input("API Base URL", value="https://api.openai.com/v1", key="global_add_model_base")
        new_api_key = st.text_input("API Key", type="password", key="global_add_model_key")
        new_org = st.text_input("Organization ID", key="global_add_model_org")
        new_desc = st.text_area("Notes", key="global_add_model_desc")
        add_submit = st.form_submit_button("Add Model")

    if add_submit:
        name_clean = new_name.strip()
        errors = []
        if not name_clean:
            errors.append("Model name cannot be empty")
        elif any(m.get('name') == name_clean for m in models):
            errors.append("A model with this name already exists. Choose another name.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            models.append({
                'name': name_clean,
                'base_url': new_base_url.strip(),
                'api_key': new_api_key.strip(),
                'organization': new_org.strip(),
                'description': new_desc.strip(),
            })
            global_conf['models'] = models
            if not global_conf.get('default_model'):
                global_conf['default_model'] = name_clean
            save_global_model_configs(global_conf)
            st.session_state['global_model_configs'] = global_conf
            sync_api_settings_from_global()
            st.success("Model added")
            trigger_rerun()

    st.markdown("### 📚 Configured Models")
    if not models:
        st.info("No models configured yet. Add one first.")
    else:
        for idx, model in enumerate(models):
            header = model.get('name', f'Model {idx + 1}')
            if header == default_model_name:
                header = f"{header} · Default"
            with st.expander(header, expanded=False):
                with st.form(f"edit_global_model_{idx}"):
                    updated_name = st.text_input("Model Name", value=model.get('name', ''), key=f"global_edit_name_{idx}")
                    updated_base = st.text_input("API Base URL", value=model.get('base_url', ''), key=f"global_edit_base_{idx}")
                    updated_key = st.text_input("API Key", value=model.get('api_key', ''), type="password", key=f"global_edit_key_{idx}")
                    updated_org = st.text_input("Organization ID", value=model.get('organization', ''), key=f"global_edit_org_{idx}")
                    updated_desc = st.text_area("Notes", value=model.get('description', ''), key=f"global_edit_desc_{idx}")
                    update_submit = st.form_submit_button("Save Changes")

                if update_submit:
                    name_clean = updated_name.strip()
                    if not name_clean:
                        st.error("Model name cannot be empty")
                    elif any(m.get('name') == name_clean for j, m in enumerate(models) if j != idx):
                        st.error("Another model already uses this name. Please choose a different one.")
                    else:
                        models[idx] = {
                            'name': name_clean,
                            'base_url': updated_base.strip(),
                            'api_key': updated_key.strip(),
                            'organization': updated_org.strip(),
                            'description': updated_desc.strip(),
                        }
                        if default_model_name == model.get('name'):
                            global_conf['default_model'] = name_clean
                        global_conf['models'] = models
                        save_global_model_configs(global_conf)
                        st.session_state['global_model_configs'] = global_conf
                        sync_api_settings_from_global()
                        st.success("Model updated")
                        trigger_rerun()

                cols = st.columns([0.4, 0.3, 0.3])
                with cols[0]:
                    if st.button("Set as Default", key=f"set_default_model_{idx}"):
                        global_conf['default_model'] = model.get('name')
                        save_global_model_configs(global_conf)
                        st.session_state['global_model_configs'] = global_conf
                        sync_api_settings_from_global()
                        st.success("Default model updated")
                        trigger_rerun()
                with cols[2]:
                    if st.button("Delete Model", key=f"delete_model_{idx}"):
                        removed = models.pop(idx)
                        global_conf['models'] = models
                        if removed.get('name') == global_conf.get('default_model'):
                            global_conf['default_model'] = models[0]['name'] if models else 'gpt-5'
                        save_global_model_configs(global_conf)
                        st.session_state['global_model_configs'] = global_conf
                        sync_api_settings_from_global()
                        st.success("Model deleted")
                        trigger_rerun()

    st.markdown("---")
    st.caption("Heads-up: model credentials live in the local `data/config/global_models.json`. Please keep them backed up and secure.")

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

# Connectivity test (results shown in sidebar)
connection_ok = False
connection_error_msg = ""
try:
    import httpx

    httpx.get("https://httpbin.org/status/200", timeout=2)
    connection_ok = True
except Exception as exc:
    connection_error_msg = "Check `.env`/network/BASE_URL and consider Python 3.11." if not str(exc) else str(exc)

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

if 'global_model_configs' not in st.session_state:
    st.session_state['global_model_configs'] = load_global_model_configs()

if 'api_settings' not in st.session_state:
    st.session_state['api_settings'] = {
        'api_key': os.getenv("OPENAI_API_KEY", ""),
        'base_url': os.getenv("OPENAI_BASE_URL", ""),
        'organization': os.getenv("OPENAI_ORG", os.getenv("OPENAI_ORGANIZATION", "")),
        'default_model': os.getenv("OPENAI_MODEL", "gpt-5"),
        'default_model_custom': "",
    }

sync_api_settings_from_global()

# Guard: require key for extraction/repository actions only
has_api_key = bool(st.session_state['api_settings'].get('api_key'))

st.sidebar.header("Settings")
st.sidebar.caption(f"Python: {sys.version.split()[0]} (3.11 recommended)")

# Database status - simplified check
try:
    # Check database file exists
    if os.path.exists(db_path):
        if connection_ok:
            st.sidebar.success("✅ Database ready · 🌐 Connected")
        else:
            st.sidebar.warning("✅ Database ready · ❌ No connection")
            if connection_error_msg:
                st.sidebar.info(connection_error_msg)
    else:
        st.sidebar.warning("Database not found")
        st.sidebar.info("Will be created automatically")
        if connection_ok:
            st.sidebar.info("🌐 Connected")
        elif connection_error_msg:
            st.sidebar.info(connection_error_msg)
except Exception as e:
    st.sidebar.error(f"Database issue: {str(e)[:20]}...")
    st.sidebar.info("Try refreshing the page")

# App sections in sidebar
st.sidebar.markdown("### ⚙️ System")
if st.session_state.get('show_api_settings', False):
    if st.sidebar.button("⬅️ Back to Projects", key="sidebar_back_to_projects"):
        st.session_state.show_api_settings = False
        trigger_rerun()
else:
    if st.sidebar.button("Model & API Settings", key="sidebar_open_global_settings"):
        st.session_state.show_api_settings = True
        trigger_rerun()

if st.session_state.get('show_api_settings'):
    render_global_model_settings()
    st.stop()

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

st.sidebar.markdown("---")
reset_state_key = "confirm_reset_workspace"
if st.sidebar.button(
    "🧹 Reset Workspace",
    help="Delete all user data (projects, database, outputs).",
    key="reset_workspace_button",
):
    st.session_state[reset_state_key] = True

if st.session_state.get(reset_state_key):
    st.sidebar.error("This will remove all projects, papers, extractions, and configuration files. This action cannot be undone.")
    confirm_col, cancel_col = st.sidebar.columns(2)
    with confirm_col:
        if st.button("Confirm", key="reset_workspace_confirm"):
            reset_workspace()
            st.session_state.pop(reset_state_key, None)
            st.sidebar.success("Workspace reset. Reloading...")
            trigger_rerun()
    with cancel_col:
        if st.button("Cancel", key="reset_workspace_cancel"):
            st.session_state.pop(reset_state_key, None)

# defaults to avoid NameError when switching sections
run_btn = False
citation = ""
pdf_file = None
paper_id = ""

# Load field profiles
def load_field_list(codebook_path: str, profile_name: str) -> List[str]:
    cfg = read_yaml(codebook_path)
    if normalize_profile_name(profile_name) == DEFAULT_PROFILE_NAME:
        return [f["name"] for f in cfg["fields"]]
    profiles = cfg.get("profiles", {})
    normalized_name = normalize_profile_name(profile_name)
    if normalized_name not in profiles:
        return [f["name"] for f in cfg["fields"]]
    subset = profiles[normalized_name]
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
    DEFAULT_PROFILE_NAME: [],
    "Only Classification": [],
    "Only RQ1": [],
    "Only RQ2": [],
    "Only RQ3": [],
    "Only RQ4": [],
    "Only RQ5": [],
    "Only RQ6": [],
}

# Include `venue.trust_rating` in the general profile (optional for classification/RQ subsets).
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

    with _connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT e.*, p.title, p.citation
            FROM extractions e
            LEFT JOIN papers p ON e.paper_id = p.paper_id
            WHERE e.project_id = ?
            ORDER BY e.created_at DESC
            """,
            (selected_project['project_id'],),
        )
        project_extractions = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]

    with _connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT e.*, p.title, p.citation
            FROM extractions e
            LEFT JOIN papers p ON e.paper_id = p.paper_id
            WHERE e.project_id = ?
            ORDER BY e.created_at DESC
            """,
            (selected_project['project_id'],),
        )
        project_extractions = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]

    # Project tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Papers", "🔍 Extraction", "📊 Analytics", "⚙️ Settings"])

    with tab1:
        render_papers_tab(selected_project, db_path)

    with tab2:
        render_extraction_tab(
            selected_project=selected_project,
            db_path=db_path,
            project_extractions=project_extractions,
            has_api_key=has_api_key,
            global_conf=global_conf,
        )

    with tab3:
        render_analytics_tab(selected_project, db_path, project_extractions)

    with tab4:
        render_settings_tab(selected_project, db_path, global_conf)

# Show create project form if requested
if st.session_state.get('show_create_project', False):
    global_conf = st.session_state.get('global_model_configs', load_global_model_configs())
    render_project_creation_form(db_path, global_conf)

# Show analytics if requested
if st.session_state.get('show_analytics', False):
    st.markdown("---")
    st.subheader("📊 Global Analytics")
    st.info("Global analytics functionality will be implemented here.")
    
    if st.button("Close Analytics"):
        st.session_state.show_analytics = False
        trigger_rerun()

st.markdown("---")
st.caption("Config priority: secrets.toml > .env. Per-project defaults live under data/projects/<id>/feature_groups/default/, with optional fallbacks in config/codebook.yaml and prompts/extract.j2.")
