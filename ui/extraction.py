import math
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import streamlit as st

from core import (
    DEFAULT_PAGE_SIZES,
    build_feature_group_options,
    filter_papers_by_query,
    normalize_profile_name,
    render_clipboard_button,
    resolve_project_dir,
    trigger_rerun,
)
from core import temporary_env
from utils.db import (
    list_papers,
    list_project_groups,
    list_extractions,
    add_extraction,
    _connect,
)
from utils.extractor import run_extraction, append_outputs
from utils.extractor import read_yaml


def _compute_model_state(global_conf: Dict[str, Any]) -> Dict[str, Any]:
    model_options = [m.get('name') for m in global_conf.get('models', []) if m.get('name')]
    default_model_name = st.session_state['api_settings'].get('default_model') or (
        model_options[0] if model_options else 'gpt-5'
    )
    api_state = st.session_state.setdefault('api_settings', {})

    if model_options:
        selected_model = st.selectbox(
            "Model Selection",
            options=model_options,
            index=model_options.index(default_model_name) if default_model_name in model_options else 0,
            key="extraction_model_select",
        )
        model_conf = next((m for m in global_conf.get('models', []) if m.get('name') == selected_model), None)
        if model_conf:
            api_state['default_model'] = selected_model
            api_state['api_key'] = model_conf.get('api_key', '')
            api_state['base_url'] = model_conf.get('base_url', '')
            api_state['organization'] = model_conf.get('organization', '')
            st.info("Credentials for the selected model have been loaded. Manage them from System Settings.")
    else:
        st.warning('No models configured yet. Go to "Model & API Settings" to add one.')
        selected_model = api_state.get('default_model', 'gpt-5')

    return {
        'model_options': model_options,
        'selected_model': selected_model,
        'api_state': api_state,
    }


def _load_project_papers(selected_project: Dict[str, Any], db_path: str) -> List[Dict[str, Any]]:
    project_papers: List[Dict[str, Any]] = []
    all_papers = list_papers(db_path)
    for paper in all_papers:
        if paper['paper_id'].startswith(selected_project['project_id'] + '-'):
            project_papers.append(paper)
        else:
            with _connect(db_path) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT COUNT(*) FROM extractions WHERE paper_id = ? AND project_id = ?",
                    (paper['paper_id'], selected_project['project_id']),
                )
                if c.fetchone()[0] > 0:
                    project_papers.append(paper)
    return project_papers


def render_extraction_tab(
    selected_project: Dict[str, Any],
    db_path: str,
    project_extractions: List[Dict[str, Any]],
    has_api_key: bool,
    global_conf: Dict[str, Any],
) -> None:
    st.markdown("### 🔍 Data Extraction")
    st.caption("Extract data from papers using AI or manual entry")

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

    model_state = _compute_model_state(global_conf)
    model_options = model_state['model_options']
    selected_model = model_state['selected_model']
    api_state = model_state['api_state']

    project_papers = _load_project_papers(selected_project, db_path)
    groups = list_project_groups(db_path, selected_project['project_id'])
    group_options, project_dir = build_feature_group_options(selected_project, groups)

    if not group_options:
        st.info("Create a feature group in Project Settings before running extractions.")
        return

    search_query_extract = st.text_input(
        "Search papers (ID or title)",
        value=st.session_state.get(f"extraction_search_{selected_project['project_id']}", ""),
        key=f"extraction_search_{selected_project['project_id']}",
    )
    filtered_project_papers = filter_papers_by_query(project_papers, search_query_extract)

    if not project_papers:
        st.info("Upload some papers first to run extraction.")
        return
    if not filtered_project_papers:
        st.info("No papers match your search.")
        return

    page_size = st.selectbox(
        "Papers per page",
        options=DEFAULT_PAGE_SIZES,
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
        return

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
                env_overrides = {
                    'OPENAI_MODEL': selected_model,
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
                return
            try:
                payload = json.loads(json_input)
            except json.JSONDecodeError as exc:
                st.error(f"Failed to parse JSON: {exc}")
                return

            if not isinstance(payload, dict):
                st.error("Top-level JSON must be an object mapping field -> data.")
                return

            normalized: Dict[str, Dict[str, Any]] = {}
            errors: List[str] = []
            for field_name, item in payload.items():
                if not isinstance(item, dict):
                    errors.append(f"Field {field_name}: value must be an object.")
                    continue
                if "value" not in item:
                    errors.append(f"Field {field_name}: missing required key 'value'.")
                    continue
                normalized[field_name] = {
                    "value": item.get("value"),
                    "evidence": item.get("evidence", "NA"),
                    "location": item.get("location", "NA"),
                }

            if errors:
                st.error("Validation failed:\n" + "\n".join(errors))
                return

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

            if field_validation_failed:
                return

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
