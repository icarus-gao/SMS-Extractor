import os, json, sys, time, re, shutil
import html
import math
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from uuid import uuid4
import streamlit as st
import streamlit.components.v1 as components
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
import pandas as pd


DEFAULT_PROFILE_NAME = "Default"


def normalize_profile_name(name: Optional[str]) -> str:
    if not name:
        return DEFAULT_PROFILE_NAME
    if name.strip().lower() == "full schema":
        return DEFAULT_PROFILE_NAME
    return name


def sanitize_group_dir_name(name: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip('-')
    return slug or fallback


def ensure_unique_group_dir(base_dir: Path, desired_slug: str, current: Optional[Path] = None) -> Path:
    candidate = base_dir / desired_slug
    if current and candidate.resolve(strict=False) == current.resolve(strict=False):
        return candidate
    counter = 1
    while candidate.exists() and (not current or candidate.resolve(strict=False) != current.resolve(strict=False)):
        candidate = base_dir / f"{desired_slug}-{counter}"
        counter += 1
    return candidate


@contextmanager
def temporary_env(overrides: Dict[str, Optional[str]]):
    original: Dict[str, Optional[str]] = {}
    try:
        for key, value in overrides.items():
            original[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def filter_papers_by_query(papers: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    if not query:
        return papers
    needle = query.strip().lower()
    if not needle:
        return papers
    filtered: List[Dict[str, Any]] = []
    for paper in papers:
        pid = (paper.get('paper_id') or '').lower()
        title = (paper.get('title') or '').lower()
        if needle in pid or needle in title:
            filtered.append(paper)
    return filtered


def render_clipboard_button(text: str, label: str, *, help_text: Optional[str] = None, width: str = "100%") -> None:
    if not text:
        st.caption("No BibTeX reference stored for this entry.")
        return
    button_id = f"copy-btn-{uuid4().hex}"
    status_id = f"copy-status-{uuid4().hex}"
    safe_label = html.escape(label)
    tooltip = help_text or "Copy to clipboard"
    js_label = json.dumps(label)
    js_text = json.dumps(text)
    js_tooltip = json.dumps(tooltip)
    html_content = f"""
    <div style="width:{width}; display:flex; flex-direction:column; gap:0.25rem; align-items:flex-start;">
      <button id="{button_id}" title={js_tooltip}
              style="background:#f1f3f5;border:1px solid #ced4da;border-radius:0.5rem;padding:0.35rem 0.8rem;font-size:0.88rem;font-weight:600;color:#1f2933;cursor:pointer;">
        {safe_label}
      </button>
      <span id="{status_id}" style="font-size:0.72rem;color:#64748b;"></span>
    </div>
    <script>
    (function() {{
        const btn = document.getElementById('{button_id}');
        if (!btn || btn.dataset.bound === '1') return;
        btn.dataset.bound = '1';
        const initialLabel = {js_label};
        const successColor = '#1f5132';
        const successBackground = '#d1f7c4';
        const errorColor = '#7f1d1d';
        const errorBackground = '#ffe3e3';
        const defaultColor = '#1f2933';
        const defaultBackground = '#f1f3f5';
        const status = document.getElementById('{status_id}');
        btn.addEventListener('click', async () => {{
            try {{
                await navigator.clipboard.writeText({js_text});
                btn.textContent = 'Copied!';
                btn.style.background = successBackground;
                btn.style.color = successColor;
                if (status) {{
                    status.textContent = 'Copied to clipboard';
                    status.style.color = successColor;
                }}
            }} catch (err) {{
                console.error('Copy failed', err);
                btn.textContent = 'Copy failed';
                btn.style.background = errorBackground;
                btn.style.color = errorColor;
                if (status) {{
                    status.textContent = 'Copy failed, please try again';
                    status.style.color = errorColor;
                }}
            }}
            setTimeout(() => {{
                btn.textContent = initialLabel;
                btn.style.background = defaultBackground;
                btn.style.color = defaultColor;
                if (status) {{
                    status.textContent = '';
                }}
            }}, 1600);
        }});
    }})();
    </script>
    """
    components.html(html_content, height=60)


def trigger_rerun() -> None:
    """Safely force Streamlit to rerun, compatible with legacy APIs."""
    try:
        st.experimental_rerun()
    except AttributeError:
        try:
            st.rerun()
        except AttributeError:
            pass


def replace_bibtex_key(entry: str, new_key: str) -> str:
    """Replace the citation key in a BibTeX entry with the provided paper_id."""
    pattern = re.compile(r"(@[a-zA-Z]+\s*\{)\s*([^,\s]+)")

    def _sub(match: re.Match[str]) -> str:
        return f"{match.group(1)}{new_key}"

    return pattern.sub(_sub, entry, count=1)


def _cleanup_bibtex_value(value: str) -> str:
    text = value.strip()
    # Strip balanced outer wrappers like {}, "" repeatedly.
    changed = True
    while text and changed:
        changed = False
        if text.startswith('{') and text.endswith('}'):
            text = text[1:-1].strip()
            changed = True
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
            changed = True
    text = re.sub(r"\s+", " ", text)
    return text


def extract_title_from_bibtex(entry: str) -> Optional[str]:
    """Parse a BibTeX entry and return a cleaned title if present."""
    if not entry or not entry.strip():
        return None
    try:
        from bibtexparser import loads
        from bibtexparser.bparser import BibTexParser

        parser = BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = False
        bib_db = loads(entry, parser=parser)
        if bib_db.entries:
            title_raw = bib_db.entries[0].get('title')
            if title_raw:
                return _cleanup_bibtex_value(title_raw)
    except Exception:
        pass

    try:
        match = re.search(
            r"title\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\")",
            entry,
            flags=re.IGNORECASE,
        )
        if match:
            return _cleanup_bibtex_value(match.group(1))
    except Exception:
        pass
    return None


def resolve_project_dir(project: Dict[str, Any]) -> Path:
    """Infer the project root directory from a project's stored codebook path."""
    codebook_path = Path(project.get('codebook_path', '') or '')
    try:
        for parent in codebook_path.resolve(strict=False).parents:
            if parent.name == project.get('project_id'):
                return parent
    except Exception:
        pass
    if codebook_path.parent.name == project.get('project_id'):
        return codebook_path.parent
    if codebook_path.parent.parent.name == project.get('project_id'):
        return codebook_path.parent.parent
    return Path(f"data/projects/{project.get('project_id')}").resolve()


def build_feature_group_options(
    project: Dict[str, Any],
    groups: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Path]:
    project_dir = resolve_project_dir(project)
    options: List[Dict[str, Any]] = []

    for record in groups:
        outputs_dir = project_dir / "feature_groups" / record['group_name'] / "outputs"
        options.append(
            {
                "label": record['group_name'],
                "value": record['group_name'],
                "codebook": record.get('codebook_path') or project.get('codebook_path'),
                "prompt": record.get('prompt_path') or project.get('template_path'),
                "outputs_dir": outputs_dir,
                "profile": record['group_name'],
            }
        )
    return options, project_dir


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

    # Project tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Papers", "🔍 Extraction", "📊 Analytics", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### 📄 Papers Management")
        st.caption("Upload and manage papers for this project")
        
        # Zotero import section
                # Zotero import removed by user request
        with st.expander("📤 Upload Papers", expanded=True):
            uploader_key = f"upload_{selected_project['project_id']}"
            uploaded_files = st.file_uploader(
                f"Upload PDF files for {selected_project['name']}",
                type=["pdf"],
                accept_multiple_files=True,
                key=uploader_key,
            )

            if uploaded_files:
                st.info("Provide citation details for each paper (optional). If you choose BibTeX, the citation key becomes the paper ID.")
                per_file_inputs = []
                ts_base = int(time.time() * 1000)
                for idx, pdf_file in enumerate(uploaded_files):
                    section = st.container()
                    with section:
                        st.markdown(f"**{pdf_file.name}**")
                        format_key = f"{uploader_key}_format_{idx}"
                        citation_key = f"{uploader_key}_citation_{idx}"
                        paper_id_key = f"{uploader_key}_paper_id_{idx}"
                        suggested_id = f"{selected_project['project_id']}-{ts_base + idx}"
                        st.text_input(
                            "Paper ID",
                            value=suggested_id,
                            key=paper_id_key,
                            help="Leave as-is to auto-generate, or customize using letters, numbers, hyphen, underscore.",
                        )
                        format_choice = st.selectbox(
                            "Citation Format",
                            options=["BibTeX"],
                            key=format_key,
                            help="Currently only BibTeX is supported; additional formats may be added later.",
                        )
                        citation_value = st.text_area(
                            "Reference Content",
                            key=citation_key,
                            placeholder="Paste BibTeX or a standard reference entry",
                            height=120,
                        )
                        per_file_inputs.append(
                            {
                                "pdf": pdf_file,
                                "format": format_choice,
                                "citation_text": citation_value,
                                "format_key": format_key,
                                "citation_key": citation_key,
                                "paper_id_key": paper_id_key,
                                "paper_suffix": idx,
                                "default_id": suggested_id,
                            }
                        )

                if st.button("Save Uploads", key=f"{uploader_key}_commit"):
                    for entry in per_file_inputs:
                        pdf_file = entry["pdf"]
                        format_choice = st.session_state.get(entry["format_key"], "No Citation")
                        citation_text = st.session_state.get(entry["citation_key"], "").strip()
                        raw_paper_id = st.session_state.get(entry["paper_id_key"], "").strip()
                        default_id = entry["default_id"]
                        sanitized_id = re.sub(r'[^a-zA-Z0-9_-]', '-', raw_paper_id).strip('-')
                        paper_id = sanitized_id or default_id

                        if get_paper(db_path, paper_id):
                            st.warning(f"Paper ID '{paper_id}' already exists. Skipping {pdf_file.name}.")
                            continue

                        project_dir = resolve_project_dir(selected_project)
                        papers_dir = project_dir / "papers"
                        papers_dir.mkdir(parents=True, exist_ok=True)
                        file_path = papers_dir / pdf_file.name

                        pdf_buffer = pdf_file.getbuffer()
                        pdf_sha = hashlib.sha256(pdf_buffer).hexdigest()
                        existing = get_paper_by_sha(db_path, pdf_sha)
                        if existing:
                            st.warning(f"PDF already exists as paper_id: {existing['paper_id']}")
                            continue

                        with open(file_path, "wb") as f:
                            f.write(pdf_buffer)

                        citation_format: Optional[str] = None
                        citation_value = citation_text or f"Uploaded: {pdf_file.name}"

                        if citation_text:
                            citation_format = "bibtex"
                            citation_value = replace_bibtex_key(citation_text, paper_id)

                        title_guess = None
                        if citation_format == "bibtex":
                            title_guess = extract_title_from_bibtex(citation_value)
                            if not title_guess and citation_text:
                                title_guess = guess_title_from_citation(citation_text)
                        elif citation_text:
                            title_guess = guess_title_from_citation(citation_text)

                        insert_or_update_paper(
                            db_path,
                            paper_id,
                            selected_project['project_id'],
                            citation_value,
                            str(file_path),
                            title=title_guess,
                            citation_format=citation_format,
                            pdf_sha256=pdf_sha,
                        )
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

        search_query = st.text_input(
            "Search papers (ID or title)",
            value=st.session_state.get(f"paper_search_{selected_project['project_id']}", ""),
            key=f"paper_search_{selected_project['project_id']}",
        )
        filtered_papers = filter_papers_by_query(project_papers, search_query)

        if filtered_papers:
            st.write(f"**Papers in {selected_project['name']}:**")
            if search_query and len(filtered_papers) != len(project_papers):
                st.caption(f"Showing {len(filtered_papers)} of {len(project_papers)} results for '{search_query}'.")
            for paper in filtered_papers:
                with st.expander(f"{paper['paper_id']}: {paper['title'] or '(no title)'}", expanded=False):
                    st.write(f"**Citation:** {paper['citation']}")
                    if paper['citation_format']:
                        label = "BibTeX" if paper['citation_format'] == "bibtex" else paper['citation_format']
                        st.write(f"**Citation Format:** {label}")
                    st.write(f"**PDF:** {paper['pdf_path']}")
                    st.write(f"**Created:** {datetime.fromtimestamp(paper['created_at']).strftime('%Y-%m-%d %H:%M')}")
                    
                    # Management buttons with persistent state to survive reruns
                    rename_state_key = f"paper_rename_mode_{paper['paper_id']}"
                    rename_value_key = f"paper_rename_value_{paper['paper_id']}"
                    delete_state_key = f"paper_delete_mode_{paper['paper_id']}"
                    delete_checkbox_key = f"paper_delete_pdf_{paper['paper_id']}"

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Rename {paper['paper_id']}", key=f"rename_{paper['paper_id']}"):
                            st.session_state[rename_state_key] = True
                            st.session_state.setdefault(rename_value_key, paper['paper_id'])

                    with col2:
                        if st.button(f"Delete {paper['paper_id']}", key=f"delete_{paper['paper_id']}"):
                            st.session_state[delete_state_key] = True
                            st.session_state.setdefault(delete_checkbox_key, False)

                    if st.session_state.get(rename_state_key):
                        st.markdown("---")
                        st.info("Rename paper and keep extraction history linked to the new ID.")
                        st.session_state.setdefault(rename_value_key, paper['paper_id'])
                        new_id = st.text_input(
                            "New paper ID",
                            key=rename_value_key,
                            help="Letters, numbers, hyphen, underscore.",
                        ).strip()
                        rename_actions = st.columns([0.25, 0.25, 0.5])
                        with rename_actions[0]:
                            if st.button("Save", key=f"confirm_rename_{paper['paper_id']}"):
                                if not new_id:
                                    st.error("Paper ID cannot be empty.")
                                else:
                                    existing_paper = get_paper(db_path, paper['paper_id'])
                                    new_citation_text = None
                                    if existing_paper and existing_paper.get('citation_format') == 'bibtex' and existing_paper.get('citation'):
                                        try:
                                            new_citation_text = replace_bibtex_key(existing_paper['citation'], new_id)
                                        except Exception as exc:
                                            st.warning(f"BibTeX key update failed, keeping original citation: {exc}")
                                    new_title = existing_paper.get('title') if existing_paper else None
                                    if not new_title and new_citation_text:
                                        extracted_title = extract_title_from_bibtex(new_citation_text)
                                        if extracted_title:
                                            new_title = extracted_title
                                    try:
                                        rename_paper_id(db_path, paper['paper_id'], new_id)
                                    except ValueError as exc:
                                        st.error(str(exc))
                                    except Exception as exc:
                                        st.error(f"Rename failed: {exc}")
                                    else:
                                        if existing_paper:
                                            insert_or_update_paper(
                                                db_path,
                                                new_id,
                                                existing_paper.get('project_id'),
                                                new_citation_text or existing_paper.get('citation', ''),
                                                existing_paper.get('pdf_path', ''),
                                                title=new_title or existing_paper.get('title'),
                                                citation_format=existing_paper.get('citation_format'),
                                                pdf_sha256=existing_paper.get('pdf_sha256'),
                                            )
                                        st.success(f"Renamed to {new_id}")
                                        st.session_state.pop(rename_state_key, None)
                                        st.session_state.pop(rename_value_key, None)
                                        trigger_rerun()
                        with rename_actions[1]:
                            if st.button("Cancel", key=f"cancel_rename_{paper['paper_id']}"):
                                st.session_state.pop(rename_state_key, None)
                                st.session_state.pop(rename_value_key, None)
                                trigger_rerun()

                    if st.session_state.get(delete_state_key):
                        st.markdown("---")
                        st.error("Delete this paper and all related extractions? This cannot be undone.")
                        delete_pdf = st.checkbox(
                            "Also delete the stored PDF file",
                            key=delete_checkbox_key,
                        )
                        delete_actions = st.columns([0.25, 0.25, 0.5])
                        with delete_actions[0]:
                            if st.button("Delete", key=f"confirm_delete_{paper['paper_id']}"):
                                try:
                                    delete_paper(db_path, paper['paper_id'])
                                except Exception as exc:
                                    st.error(f"Delete failed: {exc}")
                                else:
                                    if delete_pdf and paper['pdf_path'] and Path(paper['pdf_path']).exists():
                                        try:
                                            Path(paper['pdf_path']).unlink()
                                        except Exception as exc:
                                            st.warning(f"PDF removal issue: {exc}")
                                    st.success(f"Deleted {paper['paper_id']}")
                                    st.session_state.pop(delete_state_key, None)
                                    st.session_state.pop(delete_checkbox_key, None)
                                    trigger_rerun()
                        with delete_actions[1]:
                            if st.button("Cancel", key=f"cancel_delete_{paper['paper_id']}"):
                                st.session_state.pop(delete_state_key, None)
                                st.session_state.pop(delete_checkbox_key, None)
                                trigger_rerun()
        else:
            if project_papers:
                st.info("No papers match your search.")
            else:
                st.info(f"No papers uploaded for {selected_project['name']} yet.")
    
    with tab2:
        st.markdown("### 🔍 Data Extraction")
        st.caption("Extract data from papers using AI")

        feedback_key = f"extraction_feedback_{selected_project['project_id']}"
        pending_feedback = st.session_state.get(feedback_key)
        if pending_feedback:
            if pending_feedback.get('status') == 'success':
                msg = f"Extraction complete for `{pending_feedback['paper_id']}`"
                if pending_feedback.get('profile'):
                    msg += f" · profile `{pending_feedback['profile']}`"
                if pending_feedback.get('mock'):
                    msg += " (mock run)"
                st.success(msg)
                if pending_feedback.get('meta') and pending_feedback['meta'].get('prompt_tokens'):
                    st.caption(f"Prompt tokens (approx.): {pending_feedback['meta']['prompt_tokens']}")
                if pending_feedback.get('preview'):
                    st.json(pending_feedback['preview'])
            else:
                st.error(pending_feedback.get('message', 'Extraction failed.'))
            st.session_state.pop(feedback_key, None)

        global_conf = st.session_state.get('global_model_configs', {'models': [], 'default_model': 'gpt-5'})
        model_options = [m.get('name') for m in global_conf.get('models', []) if m.get('name')]
        default_model_name = st.session_state['api_settings'].get('default_model') or (model_options[0] if model_options else 'gpt-5')

        if model_options:
            selected_model = st.selectbox(
                "Model Selection",
                options=model_options,
                index=model_options.index(default_model_name) if default_model_name in model_options else 0,
                key="extraction_model_select",
            )
            model_conf = find_model_config(global_conf, selected_model)
            if model_conf:
                st.session_state['api_settings']['default_model'] = selected_model
                st.session_state['api_settings']['api_key'] = model_conf.get('api_key', '')
                st.session_state['api_settings']['base_url'] = model_conf.get('base_url', '')
                st.session_state['api_settings']['organization'] = model_conf.get('organization', '')
                st.info("Credentials for the selected model have been loaded. Manage them from System Settings.")
        else:
            st.warning('No models configured yet. Go to "Model & API Settings" to add one.')
            selected_model = st.session_state['api_settings'].get('default_model', 'gpt-5')

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
        
        groups = list_project_groups(db_path, selected_project['project_id'])
        group_options, project_dir = build_feature_group_options(selected_project, groups)

        if not group_options:
            st.info("Create a feature group in Project Settings before running extractions.")
        else:
            search_query_extract = st.text_input(
                "Search papers (ID or title)",
                value=st.session_state.get(f"extraction_search_{selected_project['project_id']}", ""),
                key=f"extraction_search_{selected_project['project_id']}",
            )
            filtered_project_papers = filter_papers_by_query(project_papers, search_query_extract)

            if not project_papers:
                st.info("Upload some papers first to run extraction.")
            elif not filtered_project_papers:
                st.info("No papers match your search.")
            else:
                page_size = st.selectbox(
                    "Papers per page",
                    options=[5, 10, 25, 50],
                    index=0,
                    key=f"extraction_page_size_{selected_project['project_id']}",
                )
                total = len(filtered_project_papers)
                total_pages = max(1, math.ceil(total / page_size))
                page_key = f"extraction_page_{selected_project['project_id']}"
                current_default = st.session_state.get(page_key, 1)
                current_default = max(1, min(current_default, total_pages))
                if total_pages == 1:
                    current_page = 1
                    st.caption("Showing all results on a single page.")
                    st.session_state[page_key] = 1
                else:
                    current_page = st.slider(
                        "Page",
                        min_value=1,
                        max_value=total_pages,
                        value=current_default,
                        key=page_key,
                    )
                start = (current_page - 1) * page_size
                end = start + page_size
                page_papers = filtered_project_papers[start:end]

                if not page_papers:
                    st.info("This page has no papers. Adjust your filters or page number.")
                else:
                    table_rows = []
                    for paper in page_papers:
                        created = datetime.fromtimestamp(paper.get('created_at', 0)).strftime('%Y-%m-%d %H:%M') if paper.get('created_at') else ''
                        updated = datetime.fromtimestamp(paper.get('updated_at', 0)).strftime('%Y-%m-%d %H:%M') if paper.get('updated_at') else ''
                        table_rows.append(
                            {
                                "Paper ID": paper['paper_id'],
                                "Title": paper.get('title') or '',
                                "Created": created,
                                "Updated": updated,
                            }
                        )
                    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                    selection_options = [f"{paper['paper_id']} · {paper.get('title') or '(no title)'}" for paper in page_papers]
                    selected_paper_label = st.selectbox(
                        "Select paper to work on",
                        options=selection_options,
                        key=f"extraction_paper_{selected_project['project_id']}",
                    )
                    target_paper = page_papers[selection_options.index(selected_paper_label)]

                    latest_run = list_extractions(db_path, target_paper['paper_id'])
                    st.markdown(f"**Selected Paper:** `{target_paper['paper_id']}` — {target_paper.get('title') or '—'}")
                    if latest_run:
                        last = latest_run[0]
                        status = last.get('status', 'unknown').title()
                        ts = datetime.fromtimestamp(last.get('created_at', int(time.time()))).strftime('%Y-%m-%d %H:%M')
                        st.caption(f"Last extraction: {status} @ {ts}")

                    group_labels = [opt['label'] for opt in group_options]
                    ai_tab, manual_tab = st.tabs(["🤖 AI Extraction", "✍️ Manual Entry"])

                    with ai_tab:
                        if not group_labels:
                            st.info("No feature groups available. Create one in Project Settings.")
                        else:
                            ai_group_label = st.selectbox(
                                "Feature group",
                                options=group_labels,
                                key=f"ai_group_{selected_project['project_id']}",
                            )
                            ai_group = next(opt for opt in group_options if opt['label'] == ai_group_label)

                            ai_codebook_path = Path(ai_group['codebook']) if ai_group.get('codebook') else None
                            ai_prompt_path = Path(ai_group['prompt']) if ai_group.get('prompt') else None
                            outputs_dir: Path = ai_group['outputs_dir']
                            outputs_dir.mkdir(parents=True, exist_ok=True)
                            raw_dir = outputs_dir / "raw"
                            raw_dir.mkdir(parents=True, exist_ok=True)

                            warn_col, control_col = st.columns([2, 1])
                            with warn_col:
                                st.caption(f"Codebook: {ai_codebook_path}")
                                st.caption(f"Prompt: {ai_prompt_path}")
                                if not ai_codebook_path or not ai_codebook_path.exists():
                                    st.warning("Codebook path is missing or invalid.")
                                if not ai_prompt_path or not ai_prompt_path.exists():
                                    st.warning("Prompt path is missing or invalid.")
                            with control_col:
                                mock_run = st.checkbox(
                                    "Mock run",
                                    value=not has_api_key,
                                    key=f"extraction_mock_{selected_project['project_id']}",
                                    help="Run without calling the API (fills placeholders).",
                                )

                            run_button = st.button(
                                "Run Extraction",
                                type="primary",
                                key=f"run_extraction_{selected_project['project_id']}",
                            )

                            if run_button:
                                pdf_path = Path(target_paper.get('pdf_path') or '')
                                errors: List[str] = []
                                if not mock_run and not has_api_key:
                                    errors.append("API key required. Add one in Model & API Settings or enable mock mode.")
                                if not pdf_path.exists():
                                    errors.append(f"PDF file not found: {pdf_path}")
                                if not ai_codebook_path or not ai_codebook_path.exists():
                                    errors.append(f"Codebook not found: {ai_codebook_path}")
                                if not ai_prompt_path or not ai_prompt_path.exists():
                                    errors.append(f"Prompt template not found: {ai_prompt_path}")

                                if errors:
                                    for err in errors:
                                        st.error(err)
                                else:
                                    api_state = st.session_state.get('api_settings', {})
                                    env_overrides = {
                                        'OPENAI_MODEL': selected_model if selected_model else os.getenv('OPENAI_MODEL', 'gpt-5'),
                                        'OPENAI_API_KEY': api_state.get('api_key') or None,
                                        'OPENAI_BASE_URL': api_state.get('base_url') or None,
                                        'OPENAI_ORG': api_state.get('organization') or None,
                                        'OPENAI_ORGANIZATION': api_state.get('organization') or None,
                                        'MOCK_EXTRACT': 'true' if mock_run else None,
                                    }

                                    status = 'success'
                                    result_payload: Optional[Dict[str, Any]] = None
                                    meta_info: Dict[str, Any] = {}
                                    error_message: Optional[str] = None

                                    with st.spinner("Running extraction..."):
                                        try:
                                            with temporary_env(env_overrides):
                                                result_payload, meta_info = run_extraction(
                                                    str(pdf_path),
                                                    target_paper.get('citation') or '',
                                                    str(ai_codebook_path),
                                                    str(ai_prompt_path),
                                                    citation_format=target_paper.get('citation_format'),
                                                )
                                        except Exception as exc:
                                            status = 'error'
                                            error_message = str(exc)

                                    if status == 'success' and result_payload is not None:
                                        preview = {k: v for k, v in list(result_payload.items())[:5]}
                                        append_outputs(
                                            str(outputs_dir / "master.csv"),
                                            str(outputs_dir / "evidence_log.csv"),
                                            target_paper['paper_id'],
                                            result_payload,
                                            str(ai_codebook_path),
                                            raw_dir=str(raw_dir),
                                        )
                                        add_extraction(
                                            db_path,
                                            paper_id=target_paper['paper_id'],
                                            project_id=selected_project['project_id'],
                                            profile=ai_group['profile'],
                                            codebook_path=str(ai_codebook_path),
                                            model=selected_model,
                                            base_url=api_state.get('base_url'),
                                            mock=bool(meta_info.get('mock', mock_run)),
                                            prompt_tokens=meta_info.get('prompt_tokens'),
                                            status='success',
                                            result=result_payload,
                                        )
                                        st.session_state[feedback_key] = {
                                            'status': 'success',
                                            'paper_id': target_paper['paper_id'],
                                            'profile': ai_group['profile'],
                                            'preview': preview,
                                            'meta': meta_info,
                                            'mock': bool(meta_info.get('mock', mock_run)),
                                        }
                                        trigger_rerun()
                                    else:
                                        add_extraction(
                                            db_path,
                                            paper_id=target_paper['paper_id'],
                                            project_id=selected_project['project_id'],
                                            profile=ai_group['profile'],
                                            codebook_path=str(ai_codebook_path) if ai_codebook_path else '',
                                            model=selected_model,
                                            base_url=api_state.get('base_url'),
                                            mock=mock_run,
                                            prompt_tokens=None,
                                            status='error',
                                            result=None,
                                            error_msg=error_message,
                                        )
                                        st.session_state[feedback_key] = {
                                            'status': 'error',
                                            'paper_id': target_paper['paper_id'],
                                            'profile': ai_group['profile'],
                                            'message': error_message or 'Extraction failed.',
                                            'mock': mock_run,
                                        }
                                        trigger_rerun()

                    with manual_tab:
                        if not group_labels:
                            st.info("No feature groups available. Create one in Project Settings.")
                        else:
                            manual_group_label = st.selectbox(
                                "Feature group",
                                options=group_labels,
                                key=f"manual_group_{selected_project['project_id']}",
                            )
                            manual_option = next(opt for opt in group_options if opt['label'] == manual_group_label)

                            manual_codebook_path = manual_option.get('codebook')
                            outputs_dir: Path = manual_option['outputs_dir']
                            outputs_dir.mkdir(parents=True, exist_ok=True)
                            raw_dir = outputs_dir / "raw"
                            raw_dir.mkdir(parents=True, exist_ok=True)

                            st.caption(f"Codebook: {manual_codebook_path}")
                            st.caption(f"Outputs folder: {outputs_dir}")

                            json_input = st.text_area(
                                "Manual Extraction Result",
                                height=220,
                                placeholder='{"field_name": {"value": "...", "evidence": "...", "location": "..."}}',
                                key=f"manual_json_{selected_project['project_id']}",
                            )

                            if st.button("Save Manual Data", key=f"manual_submit_{selected_project['project_id']}"):
                                if not json_input.strip():
                                    st.error("Enter JSON content.")
                                else:
                                    try:
                                        payload = json.loads(json_input)
                                    except json.JSONDecodeError as exc:
                                        st.error(f"Failed to parse JSON: {exc}")
                                        payload = None

                                    if payload is not None and not isinstance(payload, dict):
                                        st.error("Top-level JSON must be an object mapping field -> data.")
                                        payload = None

                                    if payload is not None:
                                        normalized: Dict[str, Dict[str, Any]] = {}
                                        errors: List[str] = []
                                        for field_name, item in payload.items():
                                            if not isinstance(item, dict):
                                                errors.append(f"Field {field_name}: value must be an object.")
                                                continue
                                            if "value" not in item:
                                                errors.append(f"Field {field_name}: missing required key 'value'.")
                                                continue
                                            value = item.get("value")
                                            evidence = item.get("evidence", "NA")
                                            location = item.get("location", "NA")
                                            normalized[field_name] = {
                                                "value": value,
                                                "evidence": evidence,
                                                "location": location,
                                            }

                                        if errors:
                                            st.error("Validation failed:\n" + "\n".join(errors))
                                            payload = None
                                    if payload is not None:
                                        allowed_fields = None
                                        field_validation_failed = False
                                        codebook_path = manual_codebook_path
                                        if codebook_path and Path(codebook_path).exists():
                                            try:
                                                cfg = read_yaml(codebook_path)
                                                allowed_fields = {f["name"] for f in cfg.get("fields", [])}
                                            except Exception as exc:
                                                st.error(f"Failed to read codebook: {exc}")
                                                field_validation_failed = True
                                        else:
                                            st.error("Codebook file not found; cannot save.")
                                            field_validation_failed = True

                                        if allowed_fields and not field_validation_failed:
                                            unknown_fields = [f for f in normalized if f not in allowed_fields]
                                            if unknown_fields:
                                                st.error("These fields are not defined in the codebook: " + ", ".join(unknown_fields))
                                                field_validation_failed = True

                                        if not field_validation_failed and payload is not None:
                                            master_csv = str(outputs_dir / "master.csv")
                                            evidence_csv = str(outputs_dir / "evidence_log.csv")
                                            raw_dir_path = str(raw_dir)

                                            append_outputs(
                                                master_csv,
                                                evidence_csv,
                                                target_paper['paper_id'],
                                                normalized,
                                                codebook_path,
                                                raw_dir=raw_dir_path,
                                            )

                                            add_extraction(
                                                db_path,
                                                paper_id=target_paper['paper_id'],
                                                project_id=selected_project['project_id'],
                                                profile=manual_option['profile'],
                                                codebook_path=codebook_path,
                                                model="manual-entry",
                                                base_url=None,
                                                mock=False,
                                                prompt_tokens=None,
                                                status="manual",
                                                result=normalized,
                                            )
                                            st.success("Manual data saved.")
                                            trigger_rerun()

            details_col, actions_col = st.columns([2, 1])
            with details_col:
                st.markdown(f"**Paper ID:** `{target_paper['paper_id']}`")
                st.markdown(f"**Title:** {target_paper.get('title') or '—'}")
                st.caption(f"PDF path: {target_paper.get('pdf_path')}")
                latest_run = list_extractions(db_path, target_paper['paper_id'])
                if latest_run:
                    last = latest_run[0]
                    status = last.get('status', 'unknown').title()
                    ts = datetime.fromtimestamp(last.get('created_at', int(time.time()))).strftime('%Y-%m-%d %H:%M')
                    st.caption(f"Last extraction: {status} @ {ts}")
                if not codebook_path or not codebook_path.exists():
                    st.warning(f"Codebook missing: {codebook_path}")
                if not prompt_path or not prompt_path.exists():
                    st.warning(f"Prompt missing: {prompt_path}")
            with actions_col:
                mock_run = st.checkbox(
                    "Mock run (no API call)",
                    value=not has_api_key,
                    key=f"extraction_mock_{selected_project['project_id']}",
                )
                run_button = st.button(
                    "Run Extraction",
                    type="primary",
                    key=f"run_extraction_{selected_project['project_id']}",
                )

            if run_button:
                pdf_path = Path(target_paper.get('pdf_path') or '')
                errors: List[str] = []
                if not mock_run and not has_api_key:
                    errors.append("API key required. Add one in Model & API Settings or enable mock mode.")
                if not pdf_path.exists():
                    errors.append(f"PDF file not found: {pdf_path}")
                if not codebook_path or not codebook_path.exists():
                    errors.append(f"Codebook not found: {codebook_path}")
                if not prompt_path or not prompt_path.exists():
                    errors.append(f"Prompt template not found: {prompt_path}")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    api_state = st.session_state.get('api_settings', {})
                    env_overrides = {
                        'OPENAI_MODEL': selected_model if model_options else os.getenv('OPENAI_MODEL', 'gpt-5'),
                        'OPENAI_API_KEY': api_state.get('api_key') or None,
                        'OPENAI_BASE_URL': api_state.get('base_url') or None,
                        'OPENAI_ORG': api_state.get('organization') or None,
                        'OPENAI_ORGANIZATION': api_state.get('organization') or None,
                        'MOCK_EXTRACT': 'true' if mock_run else None,
                    }

                    status = 'success'
                    result_payload: Optional[Dict[str, Any]] = None
                    meta_info: Dict[str, Any] = {}
                    error_message: Optional[str] = None

                    with st.spinner("Running extraction..."):
                        try:
                            with temporary_env(env_overrides):
                                result_payload, meta_info = run_extraction(
                                    str(pdf_path),
                                    target_paper.get('citation') or '',
                                    str(codebook_path),
                                    str(prompt_path),
                                    citation_format=target_paper.get('citation_format'),
                                )
                        except Exception as exc:
                            status = 'error'
                            error_message = str(exc)

                    if status == 'success' and result_payload is not None:
                        preview = {k: v for k, v in list(result_payload.items())[:5]}
                        append_outputs(
                            str(outputs_dir / "master.csv"),
                            str(outputs_dir / "evidence_log.csv"),
                            target_paper['paper_id'],
                            result_payload,
                            str(codebook_path),
                            raw_dir=str(raw_dir),
                        )
                        add_extraction(
                            db_path,
                            paper_id=target_paper['paper_id'],
                            project_id=selected_project['project_id'],
                            profile=selected_group['profile'],
                            codebook_path=str(codebook_path),
                            model=selected_model if model_options else (os.getenv('OPENAI_MODEL', 'gpt-5')),
                            base_url=api_state.get('base_url'),
                            mock=bool(meta_info.get('mock', mock_run)),
                            prompt_tokens=meta_info.get('prompt_tokens'),
                            status='success',
                            result=result_payload,
                        )
                        st.session_state[feedback_key] = {
                            'status': 'success',
                            'paper_id': target_paper['paper_id'],
                            'profile': selected_group['profile'],
                            'preview': preview,
                            'meta': meta_info,
                            'mock': bool(meta_info.get('mock', mock_run)),
                        }
                        trigger_rerun()
                    else:
                        add_extraction(
                            db_path,
                            paper_id=target_paper['paper_id'],
                            project_id=selected_project['project_id'],
                            profile=selected_group['profile'],
                            codebook_path=str(codebook_path) if codebook_path else '',
                            model=selected_model if model_options else (os.getenv('OPENAI_MODEL', 'gpt-5')),
                            base_url=api_state.get('base_url'),
                            mock=mock_run,
                            prompt_tokens=None,
                            status='error',
                            result=None,
                            error_msg=error_message,
                        )
                        st.session_state[feedback_key] = {
                            'status': 'error',
                            'paper_id': target_paper['paper_id'],
                            'profile': selected_group['profile'],
                            'message': error_message or 'Extraction failed.',
                            'mock': mock_run,
                        }
                        trigger_rerun()

        with st.expander("✍️ Manual Entry", expanded=False):
            if not project_papers:
                st.warning("Upload papers to this project first.")
            elif not filtered_project_papers:
                st.info("No papers match your search.")
            else:
                selected_group_label = st.selectbox(
                    "Select Feature Group",
                    options=[opt["label"] for opt in group_options],
                )
                selected_option = next(opt for opt in group_options if opt["label"] == selected_group_label)

                paper_display = [f"{paper['paper_id']} · {paper.get('title') or '(no title)'}" for paper in filtered_project_papers]
                selected_paper_label = st.selectbox("Choose Paper", options=paper_display)
                paper_index = paper_display.index(selected_paper_label)
                target_paper = filtered_project_papers[paper_index]

                st.markdown("**Paste JSON (field -> {value, evidence, location})**")
                json_input = st.text_area(
                    "Manual Extraction Result",
                    height=220,
                    placeholder='{"field_name": {"value": "...", "evidence": "...", "location": "..."}}',
                    key=f"manual_json_{selected_project['project_id']}",
                )

                submit_key = f"manual_submit_{selected_project['project_id']}"
                if st.button("Save Manual Data", key=submit_key):
                    if not json_input.strip():
                        st.error("Enter JSON content.")
                    else:
                        try:
                            payload = json.loads(json_input)
                        except json.JSONDecodeError as exc:
                            st.error(f"Failed to parse JSON: {exc}")
                            payload = None

                        if payload is not None:
                            if not isinstance(payload, dict):
                                st.error("Top-level JSON must be an object mapping field -> data.")
                                payload = None

                        if payload is not None:
                            normalized: Dict[str, Dict[str, Any]] = {}
                            errors: List[str] = []
                            for field_name, item in payload.items():
                                if not isinstance(item, dict):
                                    errors.append(f"Field {field_name}: value must be an object.")
                                    continue
                                if "value" not in item:
                                    errors.append(f"Field {field_name}: missing required key 'value'.")
                                    continue
                                value = item.get("value")
                                evidence = item.get("evidence", "NA")
                                location = item.get("location", "NA")
                                normalized[field_name] = {
                                    "value": value,
                                    "evidence": evidence,
                                    "location": location,
                                }

                            if errors:
                                st.error("Validation failed:\n" + "\n".join(errors))
                            elif not normalized:
                                st.error("Provide at least one field.")
                            else:
                                codebook_path = selected_option["codebook"]
                                allowed_fields = None
                                field_validation_failed = False
                                if codebook_path and Path(codebook_path).exists():
                                    try:
                                        cfg = read_yaml(codebook_path)
                                        allowed_fields = {f["name"] for f in cfg.get("fields", [])}
                                    except Exception as exc:
                                        st.error(f"Failed to read codebook: {exc}")
                                        field_validation_failed = True
                                else:
                                    st.error("Codebook file not found; cannot save.")
                                    field_validation_failed = True

                                if allowed_fields and not field_validation_failed:
                                    unknown_fields = [f for f in normalized if f not in allowed_fields]
                                    if unknown_fields:
                                        st.error("These fields are not defined in the codebook: " + ", ".join(unknown_fields))
                                        field_validation_failed = True

                                if not field_validation_failed:
                                    outputs_dir: Path = selected_option["outputs_dir"]
                                    outputs_dir.mkdir(parents=True, exist_ok=True)
                                    master_csv = str(outputs_dir / "master.csv")
                                    evidence_csv = str(outputs_dir / "evidence_log.csv")
                                    raw_dir = str(outputs_dir / "raw")

                                    append_outputs(
                                        master_csv,
                                        evidence_csv,
                                        target_paper['paper_id'],
                                        normalized,
                                        codebook_path,
                                        raw_dir=raw_dir,
                                    )

                                    add_extraction(
                                        db_path,
                                        paper_id=target_paper['paper_id'],
                                        project_id=selected_project['project_id'],
                                        profile=selected_option["profile"],
                                        codebook_path=codebook_path,
                                        model="manual-entry",
                                        base_url=None,
                                        mock=False,
                                        prompt_tokens=None,
                                        status="manual",
                                        result=normalized,
                                    )
                                    st.success("Manual data saved.")
                                    trigger_rerun()

        st.markdown("#### Recent Extractions")
        if project_extractions:
            for ext in project_extractions[:5]:
                title = ext.get('title') or 'No title'
                status = ext.get('status', 'unknown')
                label = f"{ext['paper_id']} – {title} ({status})"
                with st.expander(label, expanded=False):
                    st.write(f"**Profile:** {normalize_profile_name(ext.get('profile'))}")
                    st.write(f"**Model:** {ext.get('model', 'Unknown')}")
                    ts = ext.get('created_at')
                    if ts:
                        st.write(f"**Date:** {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')}")
                    if ext.get('status') == 'error' and ext.get('error_msg'):
                        st.error(f"Error: {ext['error_msg']}")
                    elif ext.get('status') == 'success' and ext.get('result_json'):
                        try:
                            result = json.loads(ext['result_json'])
                            st.json({k: v for k, v in list(result.items())[:5]})
                        except Exception:
                            st.text("Could not parse result JSON")
        else:
            st.caption("No extractions recorded yet.")

    with tab3:
        st.markdown("### 📊 Project Analytics")
        st.caption("View extraction statistics and results")

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
        
        group_records = list_project_groups(db_path, selected_project['project_id'])
        profile_options_set = {
            normalize_profile_name(ext.get('profile'))
            for ext in project_extractions
            if ext.get('profile')
        }
        profile_options_set.update({normalize_profile_name(g['group_name']) for g in group_records})
        profile_options_set.discard(DEFAULT_PROFILE_NAME)
        profile_options = sorted(profile_options_set)

        if profile_options:
            selected_profiles = st.multiselect(
                "Filter feature groups",
                options=profile_options,
                default=profile_options,
                key=f"analytics_profile_filter_{selected_project['project_id']}",
            )
        else:
            selected_profiles = []

        select_mode_key = f"analytics_select_mode_{selected_project['project_id']}"
        select_mode = st.session_state.get(select_mode_key, False)
        toggle_cols = st.columns([1, 1, 4])
        with toggle_cols[0]:
            toggle_label = "Select Papers" if not select_mode else "Done Selecting"
            if st.button(toggle_label, key=f"toggle_select_mode_{selected_project['project_id']}"):
                st.session_state[select_mode_key] = not select_mode
                trigger_rerun()
        with toggle_cols[1]:
            if select_mode:
                if st.button("Clear Selection", key=f"clear_selection_{selected_project['project_id']}"):
                    selection_state_key = f"analytics_selection_{selected_project['project_id']}"
                    selection_state = st.session_state.setdefault(selection_state_key, {})
                    for pid in list(selection_state.keys()):
                        selection_state[pid] = False
                    trigger_rerun()
        if select_mode:
            st.caption("Use the checkboxes in the table to choose papers for bulk export.")

        latest_by_profile: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for ext in project_extractions:
            pid = ext['paper_id']
            profile_name = normalize_profile_name(ext.get('profile'))
            bucket = latest_by_profile.setdefault(pid, {})
            current = bucket.get(profile_name)
            if current is None or ext.get('created_at', 0) > current.get('created_at', 0):
                bucket[profile_name] = dict(ext)

        paper_lookup = {paper['paper_id']: paper for paper in project_papers}
        selection_state_key = f"analytics_selection_{selected_project['project_id']}"
        selection_state = st.session_state.setdefault(selection_state_key, {})
        for paper in project_papers:
            selection_state.setdefault(paper['paper_id'], False)

        display_profiles = [normalize_profile_name(p) for p in selected_profiles] if selected_profiles else []
        column_widths = [0.6, 1.8, 3.0] + [1.8 for _ in display_profiles]
        if not select_mode:
            column_widths = column_widths[1:]

        if project_papers:
            st.caption("💡 Tip: click the Paper ID button to copy the BibTeX reference to your clipboard.")
            header_cols = st.columns(column_widths)
            idx = 0
            if select_mode:
                header_cols[idx].markdown("**Select**")
                idx += 1
            header_cols[idx].markdown("**Paper ID**")
            idx += 1
            header_cols[idx].markdown("**Title**")
            idx += 1
            for profile_name in display_profiles:
                header_cols[idx].markdown(f"**{profile_name}**")
                idx += 1

            for paper in project_papers:
                row_cols = st.columns(column_widths)
                col_idx = 0
                if select_mode:
                    current_value = selection_state.get(paper['paper_id'], False)
                    selection_state[paper['paper_id']] = row_cols[col_idx].checkbox(
                        "",
                        value=current_value,
                        label_visibility="hidden",
                        key=f"analytics_select_{selected_project['project_id']}_{paper['paper_id']}",
                    )
                    col_idx += 1

                citation = paper.get('citation')
                citation_format = paper.get('citation_format')
                bib_available = bool(citation) and citation_format == 'bibtex'
                button_label = paper['paper_id'] if len(paper['paper_id']) <= 20 else paper['paper_id'][:17] + '…'
                with row_cols[col_idx]:
                    if bib_available:
                        render_clipboard_button(
                            citation,
                            button_label,
                            help_text="Copy BibTeX to clipboard",
                        )
                    else:
                        st.markdown(f"`{paper['paper_id']}`")
                        st.caption("No BibTeX reference stored")
                col_idx += 1

                title_text = paper.get('title') or "—"
                row_cols[col_idx].write(title_text)
                col_idx += 1

                for profile_name in display_profiles:
                    info = latest_by_profile.get(paper['paper_id'], {}).get(profile_name)
                    if info:
                        status = (info.get('status') or 'unknown').lower()
                        icon = "✅" if status == 'success' else "⚠️" if status == 'error' else "✍️" if status == 'manual' else "ℹ️"
                        ts = info.get('created_at')
                        if ts:
                            stamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                            row_cols[col_idx].markdown(
                                f"{icon} {status.title()}<br/><span style='font-size:0.8em;color:#666;'>{stamp}</span>",
                                unsafe_allow_html=True,
                            )
                        else:
                            row_cols[col_idx].markdown(f"{icon} {status.title()}")
                    else:
                        row_cols[col_idx].markdown("—")
                    col_idx += 1
        else:
            st.info("No papers uploaded for this project yet. Upload papers to populate analytics.")

        if select_mode and project_papers:
            selected_ids = [pid for pid, val in selection_state.items() if val]
            selected_bib = [
                paper_lookup[pid]['citation']
                for pid in selected_ids
                if paper_lookup.get(pid) and paper_lookup[pid].get('citation_format') == 'bibtex' and paper_lookup[pid].get('citation')
            ]
            export_cols = st.columns([1, 1, 3])
            with export_cols[0]:
                st.metric("Selected", len(selected_ids))
            with export_cols[1]:
                if selected_bib:
                    combined = "\n\n".join(selected_bib)
                    st.download_button(
                        "Download Selected (.bib)",
                        data=combined.encode('utf-8'),
                        file_name=f"{selected_project['project_id']}_selected.bib",
                        mime="application/x-bibtex",
                        key=f"download_selected_bib_{selected_project['project_id']}",
                    )
                else:
                    st.download_button(
                        "Download Selected (.bib)",
                        data="".encode('utf-8'),
                        file_name=f"{selected_project['project_id']}_selected.bib",
                        mime="application/x-bibtex",
                        disabled=True,
                        key=f"download_selected_bib_disabled_{selected_project['project_id']}",
                    )
            with export_cols[2]:
                if selected_bib:
                    combined = "\n\n".join(selected_bib)
                    render_clipboard_button(
                        combined,
                        "Copy Selected BibTeX",
                        help_text="Copy all selected BibTeX entries",
                    )
                else:
                    st.caption("Select papers with BibTeX references to enable export and copy actions.")

        if project_extractions:
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
        else:
            st.info("No extractions for this project yet.")
            st.metric("Papers", len(project_papers))
    
    with tab4:
        st.markdown("### ⚙️ Project Settings")
        st.caption("Configure project metadata, defaults, and template files")

        project_meta_cols = st.columns(4)
        with project_meta_cols[0]:
            st.metric("Project ID", selected_project['project_id'])
        with project_meta_cols[1]:
            st.metric("Created", datetime.fromtimestamp(selected_project['created_at']).strftime('%Y-%m-%d'))
        with project_meta_cols[2]:
            updated_at = selected_project.get('updated_at') or selected_project['created_at']
            st.metric("Updated", datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d'))
        with project_meta_cols[3]:
            st.metric("Default Model", selected_project.get('model') or '—')

        st.markdown("#### Update Project Details")
        global_conf = st.session_state.get('global_model_configs', {'models': [], 'default_model': 'gpt-5'})
        model_options = [m.get('name') for m in global_conf.get('models', []) if m.get('name')]

        with st.form(f"project_settings_form_{selected_project['project_id']}"):
            new_name = st.text_input("Project Name", value=selected_project['name'])
            if model_options:
                current_model = selected_project.get('model') or global_conf.get('default_model')
                default_index = model_options.index(current_model) if current_model in model_options else 0
                new_model = st.selectbox("Default Model", options=model_options, index=default_index)
            else:
                new_model = st.text_input("Default Model", value=selected_project.get('model') or '', help="Add models via Global Settings first.")
            new_notes = st.text_area("Notes", value=selected_project.get('notes') or '')

            submitted_settings = st.form_submit_button("Save Project Settings")
            if submitted_settings:
                if not new_name.strip():
                    st.error("Project name cannot be empty.")
                else:
                    upsert_project(
                        db_path,
                        selected_project['project_id'],
                        new_name.strip(),
                        selected_project['codebook_path'],
                        selected_project['template_path'],
                        new_model.strip() if new_model else None,
                        new_notes.strip(),
                    )
                    st.success("Project settings updated.")
                    trigger_rerun()

        project_dir = resolve_project_dir(selected_project)

        st.markdown("#### Manage Feature Group Templates")
        group_records = list_project_groups(db_path, selected_project['project_id'])
        group_fields_map: Dict[str, List[str]] = {}
        for record in group_records:
            try:
                group_fields_map[record['group_name']] = json.loads(record.get('fields_json') or "[]")
            except Exception:
                group_fields_map[record['group_name']] = []

        existing_group_names_lower = {record['group_name'].lower() for record in group_records}

        if not group_records:
            st.info("No feature groups yet. Use the section below to create one.")

        for record in group_records:
            group_name = record['group_name']
            label = f"Group: {group_name}"
            codebook_path = Path(record.get('codebook_path') or (project_dir / "feature_groups" / group_name / "codebook.yaml"))
            prompt_path = Path(record.get('prompt_path') or (project_dir / "feature_groups" / group_name / "prompt.j2"))

            with st.expander(label, expanded=False):
                form_key = f"project_fg_form_{selected_project['project_id']}_{group_name}"
                with st.form(form_key):
                    new_group_name = st.text_input("Group Name", value=group_name)
                    new_group_desc = st.text_area("Description", value=record.get('description') or "")
                    new_codebook = st.file_uploader(
                        "Upload new codebook (YAML)",
                        type=["yaml", "yml"],
                        key=f"proj_codebook_upload_{selected_project['project_id']}_{group_name}",
                    )
                    new_prompt = st.file_uploader(
                        "Upload new prompt template (Jinja2)",
                        type=["j2", "txt"],
                        key=f"proj_prompt_upload_{selected_project['project_id']}_{group_name}",
                    )
                    submitted_files = st.form_submit_button("Save Changes")

                if submitted_files:
                    actions: List[str] = []
                    metadata_updated = False

                    group_dir = codebook_path.parent if codebook_path else project_dir / "feature_groups" / group_name
                    group_dir.mkdir(parents=True, exist_ok=True)

                    desired_name = new_group_name.strip()
                    if not desired_name:
                        st.error("Group name cannot be empty.")
                        continue
                    desired_name_lower = desired_name.lower()
                    if desired_name_lower != group_name.lower() and desired_name_lower in existing_group_names_lower:
                        st.error("Another feature group already uses that name.")
                        continue

                    target_desc = new_group_desc.strip() if new_group_desc else None

                    current_dir = group_dir
                    target_dir_base = sanitize_group_dir_name(desired_name, f"group-{uuid4().hex[:6]}")
                    target_dir = ensure_unique_group_dir(project_dir / "feature_groups", target_dir_base, current=current_dir if desired_name == group_name else None)

                    rename_needed = desired_name != group_name
                    if rename_needed and current_dir.exists() and current_dir.resolve(strict=False) != target_dir.resolve(strict=False):
                        try:
                            current_dir.rename(target_dir)
                        except Exception as exc:
                            st.error(f"Failed to rename feature group folder: {exc}")
                            continue
                    elif rename_needed:
                        target_dir = current_dir

                    target_dir.mkdir(parents=True, exist_ok=True)
                    (target_dir / "outputs").mkdir(exist_ok=True)

                    target_codebook_path = target_dir / "codebook.yaml"
                    target_prompt_path = target_dir / "prompt.j2"

                    try:
                        if rename_needed:
                            rename_project_group(
                                db_path,
                                selected_project['project_id'],
                                group_name,
                                desired_name,
                            )
                            existing_group_names_lower.discard(group_name.lower())
                            existing_group_names_lower.add(desired_name_lower)
                            actions.append("renamed")
                        upsert_project_group(
                            db_path,
                            selected_project['project_id'],
                            desired_name,
                            fields=group_fields_map.get(group_name, []),
                            codebook_path=str(target_codebook_path),
                            prompt_path=str(target_prompt_path),
                            description=target_desc,
                        )
                        metadata_updated = True
                    except ValueError as exc:
                        st.error(str(exc))
                        continue
                    except Exception as exc:
                        st.error(f"Failed to update feature group: {exc}")
                        continue

                    if new_codebook:
                        with open(target_codebook_path, "wb") as f:
                            f.write(new_codebook.getbuffer())
                        actions.append("codebook")
                    if new_prompt:
                        with open(target_prompt_path, "wb") as f:
                            f.write(new_prompt.getbuffer())
                        actions.append("prompt")

                    if metadata_updated and "renamed" not in actions and (target_desc != (record.get('description') or None)):
                        actions.append("details")

                    if actions:
                        st.success(f"Updated {', '.join(actions)} for {desired_name}")
                        trigger_rerun()
                    else:
                        st.info("No changes were submitted.")

                st.caption(
                    f"Codebook: {codebook_path}\nPrompt: {prompt_path}"
                )

                delete_state_key = f"delete_fg_confirm_{selected_project['project_id']}_{group_name}"
                if st.button(
                    "Delete Feature Group",
                    key=f"delete_fg_{selected_project['project_id']}_{group_name}",
                ):
                    st.session_state[delete_state_key] = True

                if st.session_state.get(delete_state_key):
                    st.warning("Deleting this feature group removes its templates and metadata. This action cannot be undone.")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button(
                            "Confirm Delete",
                            key=f"confirm_delete_fg_{selected_project['project_id']}_{group_name}",
                        ):
                            try:
                                delete_project_group(db_path, selected_project['project_id'], group_name)
                                group_dir = codebook_path.parent
                                if group_dir.exists():
                                    shutil.rmtree(group_dir, ignore_errors=True)
                                st.success("Feature group deleted")
                            except Exception as exc:
                                st.error(f"Failed to delete feature group: {exc}")
                            finally:
                                st.session_state.pop(delete_state_key, None)
                                trigger_rerun()
                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_fg_{selected_project['project_id']}_{group_name}",
                        ):
                            st.session_state.pop(delete_state_key, None)
                            trigger_rerun()

        with st.expander("➕ Add Feature Group", expanded=False):
            with st.form(f"add_feature_group_form_{selected_project['project_id']}"):
                new_name = st.text_input("Group Name")
                new_desc = st.text_area("Description", value="")
                new_codebook = st.file_uploader(
                    "Codebook (YAML)",
                    type=["yaml", "yml"],
                    key=f"add_group_codebook_{selected_project['project_id']}",
                )
                new_prompt = st.file_uploader(
                    "Prompt Template (Jinja2)",
                    type=["j2", "txt"],
                    key=f"add_group_prompt_{selected_project['project_id']}",
                )
                submitted_new_group = st.form_submit_button("Create Feature Group")

            if submitted_new_group:
                clean_name = new_name.strip()
                if not clean_name:
                    st.error("Group name is required.")
                elif clean_name.lower() == DEFAULT_PROFILE_NAME.lower():
                    st.error("Group name conflicts with the default profile name.")
                elif clean_name.lower() in existing_group_names_lower:
                    st.error("A feature group with this name already exists.")
                else:
                    existing_group_names_lower.add(clean_name.lower())
                    safe_slug = sanitize_group_dir_name(clean_name, f"group-{uuid4().hex[:6]}")
                    target_dir = ensure_unique_group_dir(project_dir / "feature_groups", safe_slug)
                    target_dir.mkdir(parents=True, exist_ok=True)
                    (target_dir / "outputs").mkdir(exist_ok=True)

                    codebook_dest = target_dir / "codebook.yaml"
                    prompt_dest = target_dir / "prompt.j2"

                    if new_codebook:
                        with open(codebook_dest, "wb") as f:
                            f.write(new_codebook.getbuffer())
                    elif Path(selected_project['codebook_path']).exists():
                        shutil.copy(selected_project['codebook_path'], codebook_dest)
                    else:
                        codebook_dest.write_text("fields: []\nsettings:\n  unknown_token: NA\nprofiles: {}\nenums: {}\n", encoding="utf-8")

                    if new_prompt:
                        with open(prompt_dest, "wb") as f:
                            f.write(new_prompt.getbuffer())
                    elif Path(selected_project['template_path']).exists():
                        shutil.copy(selected_project['template_path'], prompt_dest)
                    else:
                        prompt_dest.write_text("{{ pdf_text }}\n", encoding="utf-8")

                    try:
                        upsert_project_group(
                            db_path,
                            selected_project['project_id'],
                            clean_name,
                            fields=[],
                            codebook_path=str(codebook_dest),
                            prompt_path=str(prompt_dest),
                            description=new_desc.strip() or None,
                        )
                    except Exception as exc:
                        st.error(f"Failed to create feature group: {exc}")
                    else:
                        st.success(f"Added feature group: {clean_name}")
                        trigger_rerun()

        st.markdown("#### Danger Zone")
        delete_project_state_key = f"delete_project_confirm_{selected_project['project_id']}"
        if st.button("🗑️ Delete Project", type="primary", help="Remove this project, its feature groups, papers, and extractions."):
            st.session_state[delete_project_state_key] = True

        if st.session_state.get(delete_project_state_key):
            st.error("Deleting a project removes all associated metadata, papers, and extractions. This cannot be undone.")
            confirm_col, cancel_col = st.columns([0.25, 0.25])
            with confirm_col:
                if st.button("Confirm Delete", key=f"confirm_delete_project_{selected_project['project_id']}"):
                    try:
                        delete_project(db_path, selected_project['project_id'])
                        project_path = Path(f"data/projects/{selected_project['project_id']}")
                        if project_path.exists():
                            shutil.rmtree(project_path, ignore_errors=True)
                        st.success("Project deleted")
                        st.session_state.pop(delete_project_state_key, None)
                        trigger_rerun()
                    except Exception as exc:
                        st.error(f"Failed to delete project: {exc}")
            with cancel_col:
                if st.button("Cancel", key=f"cancel_delete_project_{selected_project['project_id']}"):
                    st.session_state.pop(delete_project_state_key, None)

        st.markdown("#### File Locations")
        st.code(str(project_dir))
        st.caption("Feature group templates reside under the `feature_groups/` directory inside the project folder.")

# Show create project form if requested
if st.session_state.get('show_create_project', False):
    st.markdown("---")
    st.subheader("🆕 Create New Project")

    global_conf = st.session_state.get('global_model_configs', load_global_model_configs())
    model_options = [m.get('name') for m in global_conf.get('models', []) if m.get('name')]

    group_state_key = "create_project_groups"
    if group_state_key not in st.session_state:
        st.session_state[group_state_key] = []

    with st.form("create_project"):
        project_name = st.text_input("Project Name", value="")

        if model_options:
            default_model = global_conf.get('default_model')
            default_index = model_options.index(default_model) if default_model in model_options else 0
            selected_model = st.selectbox(
                "Default Model",
                options=model_options,
                index=default_index,
                key="create_project_model",
            )
        else:
            selected_model = None
            st.warning("Add at least one model in Model & API Settings before creating a project.")

        notes = st.text_area("Notes", value="")

        st.markdown("---")
        st.markdown("**Optional Feature Groups**")
        st.caption("Add feature groups now or skip this step and configure them later in Project Settings.")

        group_uploads: Dict[str, Dict[str, Optional[Any]]] = {}
        groups_to_remove: List[str] = []
        groups_state: List[Dict[str, Any]] = st.session_state[group_state_key]

        for idx, group in enumerate(groups_state):
            group.setdefault('id', str(uuid4()))
            prefix = f"create_group_{group['id']}"
            current_name = st.session_state.get(f"{prefix}_name", group.get('name', ''))
            expander_label = current_name.strip() or f"Feature Group {idx + 1}"
            with st.expander(expander_label, expanded=True):
                name_value = st.text_input("Group Name", value=group.get('name', ''), key=f"{prefix}_name", help="Display name shown throughout the app.")
                desc_value = st.text_area("Description", value=group.get('description', ''), key=f"{prefix}_desc")
                codebook_file = st.file_uploader("Codebook (YAML)", type=["yaml", "yml"], key=f"{prefix}_codebook")
                prompt_file = st.file_uploader("Prompt Template (Jinja2)", type=["j2", "txt"], key=f"{prefix}_prompt")
                remove_requested = st.form_submit_button("Remove This Group")

            group['name'] = st.session_state.get(f"{prefix}_name", name_value).strip()
            group['description'] = st.session_state.get(f"{prefix}_desc", desc_value).strip()
            group_uploads[group['id']] = {"codebook": codebook_file, "prompt": prompt_file}
            if remove_requested:
                groups_to_remove.append(group['id'])

        add_group_requested = st.form_submit_button("➕ Add Feature Group")
        cancel_requested = st.form_submit_button("Cancel Project Creation")
        submit_requested = st.form_submit_button("Create Project", disabled=not model_options)

    if groups_to_remove:
        for gid in groups_to_remove:
            st.session_state[group_state_key] = [g for g in st.session_state[group_state_key] if g['id'] != gid]
            for suffix in ("_name", "_desc", "_codebook", "_prompt", "_remove"):
                st.session_state.pop(f"create_group_{gid}{suffix}", None)
        trigger_rerun()

    if add_group_requested:
        st.session_state[group_state_key].append({'id': str(uuid4()), 'name': '', 'description': ''})
        trigger_rerun()

    if cancel_requested:
        st.session_state.show_create_project = False
        st.session_state.pop(group_state_key, None)
        trigger_rerun()

    if submit_requested:
        if not project_name.strip():
            st.error("Project name is required")
        elif not selected_model:
            st.error("Select a default model before creating a project.")
        else:
            project_id = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name.lower()).strip('-')
            if not project_id:
                project_id = f"project-{int(time.time())}"

            project_dir = Path(f"data/projects/{project_id}")
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "papers").mkdir(exist_ok=True)
            feature_groups_dir = project_dir / "feature_groups"
            default_group_dir = feature_groups_dir / "default"
            feature_groups_dir.mkdir(exist_ok=True)
            default_group_dir.mkdir(exist_ok=True)
            (default_group_dir / "outputs").mkdir(exist_ok=True)

            project_codebook_path = default_group_dir / "codebook.yaml"
            project_prompt_path = default_group_dir / "prompt.j2"

            if os.path.exists("config/codebook.yaml"):
                shutil.copy("config/codebook.yaml", project_codebook_path)
            else:
                st.warning(
                    "No default codebook found at config/codebook.yaml. A placeholder will be created; update it later via Project Settings.",
                    icon="⚠️",
                )
                placeholder_codebook = """fields: []\nsettings:\n  unknown_token: NA\nprofiles: {}\nenums: {}\n"""
                project_codebook_path.write_text(placeholder_codebook, encoding="utf-8")

            if os.path.exists("prompts/extract.j2"):
                shutil.copy("prompts/extract.j2", project_prompt_path)
            else:
                st.warning(
                    "No default prompt found at prompts/extract.j2. A placeholder will be created; upload a proper template later.",
                    icon="⚠️",
                )
                placeholder_prompt = """
{% for field in field_list %}
- {{ field }}
{% endfor %}

Document summary:
{{ citation_header }}

Full text:
{{ pdf_text }}
"""
                project_prompt_path.write_text(placeholder_prompt.strip() + "\n", encoding="utf-8")

            # Persist the core project record before attaching feature groups (FK requirement).
            upsert_project(
                db_path,
                project_id,
                project_name,
                str(project_codebook_path),
                str(project_prompt_path),
                selected_model,
                notes,
            )

            extra_groups = []
            used_group_dirs = set()
            for idx, group in enumerate(st.session_state[group_state_key]):
                gid = group['id']
                prefix = f"create_group_{gid}"
                name_value = st.session_state.get(f"{prefix}_name", "").strip()
                desc_value = st.session_state.get(f"{prefix}_desc", "").strip()
                uploads = group_uploads.get(gid, {})
                codebook_upload = uploads.get('codebook')
                prompt_upload = uploads.get('prompt')

                if not name_value and not codebook_upload and not prompt_upload and not desc_value:
                    continue

                base_dir = re.sub(r'[^a-zA-Z0-9_-]', '-', name_value.lower()).strip('-') or f"group-{idx + 1}"
                safe_dir = base_dir
                counter = 1
                while safe_dir in used_group_dirs:
                    counter += 1
                    safe_dir = f"{base_dir}-{counter}"
                used_group_dirs.add(safe_dir)
                group_dir = feature_groups_dir / safe_dir
                group_dir.mkdir(parents=True, exist_ok=True)
                (group_dir / "outputs").mkdir(exist_ok=True)

                codebook_dest = group_dir / "codebook.yaml"
                prompt_dest = group_dir / "prompt.j2"

                if codebook_upload:
                    with open(codebook_dest, "wb") as f:
                        f.write(codebook_upload.getbuffer())
                if prompt_upload:
                    with open(prompt_dest, "wb") as f:
                        f.write(prompt_upload.getbuffer())

                upsert_project_group(
                    db_path,
                    project_id,
                    name_value or safe_dir,
                    description=desc_value or None,
                    codebook_path=str(codebook_dest),
                    prompt_path=str(prompt_dest),
                )
                extra_groups.append(name_value or safe_dir)

            st.success(f"Created project: {project_name}")
            st.info(f"Project directory: {project_dir}")
            if extra_groups:
                st.caption("Feature groups created: " + ", ".join(extra_groups))

            st.session_state.show_create_project = False
            st.session_state.pop(group_state_key, None)
            trigger_rerun()

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
