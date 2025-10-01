import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from uuid import uuid4

import streamlit as st

from core import (
    ensure_unique_group_dir,
    sanitize_group_dir_name,
    trigger_rerun,
    resolve_project_dir,
)
from utils.db import (
    list_project_groups,
    upsert_project,
    upsert_project_group,
    delete_project_group,
    delete_project,
    rename_project_group,
)


def render_settings_tab(selected_project: Dict[str, Any], db_path: str, global_conf: Dict[str, Any]) -> None:
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

    model_options = [m.get('name') for m in global_conf.get('models', []) if m.get('name')]

    with st.form(f"project_settings_form_{selected_project['project_id']}"):
        new_name = st.text_input("Project Name", value=selected_project['name'])
        if model_options:
            current_model = selected_project.get('model') or global_conf.get('default_model')
            default_index = model_options.index(current_model) if current_model in model_options else 0
            new_model = st.selectbox("Default Model", options=model_options, index=default_index)
        else:
            new_model = st.text_input(
                "Default Model",
                value=selected_project.get('model') or '',
                help="Add models via Global Settings first.",
            )
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
                target_dir = ensure_unique_group_dir(
                    project_dir / "feature_groups",
                    target_dir_base,
                    current=current_dir if desired_name == group_name else None,
                )

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
    if st.button(
        "🗑️ Delete Project",
        type="primary",
        help="Remove this project, its feature groups, papers, and extractions.",
    ):
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
