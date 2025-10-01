import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st

from core import trigger_rerun
from utils.db import upsert_project, upsert_project_group


def render_project_creation_form(db_path: str, global_conf: Dict[str, Any]) -> None:
    st.markdown("---")
    st.subheader("🆕 Create New Project")

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
            return
        if not selected_model:
            st.error("Select a default model before creating a project.")
            return

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
