import hashlib
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st

from core import (
    filter_papers_by_query,
    resolve_project_dir,
    replace_bibtex_key,
    extract_title_from_bibtex,
    trigger_rerun,
)
from utils.db import (
    _connect,
    get_paper,
    get_paper_by_sha,
    insert_or_update_paper,
    list_papers,
    delete_paper,
    rename_paper_id,
)
from utils.extractor import guess_title_from_citation


def render_papers_tab(selected_project: Dict[str, Any], db_path: str) -> None:
    st.markdown("### 📄 Papers Management")
    st.caption("Upload and manage papers for this project")

    uploader_key = f"upload_{selected_project['project_id']}"
    uploaded_files = st.file_uploader(
        f"Upload PDF files for {selected_project['name']}",
        type=["pdf"],
        accept_multiple_files=True,
        key=uploader_key,
    )

    if uploaded_files:
        st.info("Provide BibTeX citation for each paper; the citation key becomes the paper ID.")
        per_file_inputs = []
        ts_base = int(time.time() * 1000)
        for idx, pdf_file in enumerate(uploaded_files):
            section = st.container()
            with section:
                st.markdown(f"**{pdf_file.name}**")
                citation_key = f"{uploader_key}_citation_{idx}"
                paper_id_key = f"{uploader_key}_paper_id_{idx}"
                suggested_id = f"{selected_project['project_id']}-{ts_base + idx}"
                paper_id = st.text_input(
                    "Paper ID",
                    value=suggested_id,
                    key=paper_id_key,
                    help="Customize using letters, numbers, hyphen, underscore.",
                )
                citation_text = st.text_area(
                    "BibTeX Reference",
                    key=citation_key,
                    placeholder="@article{...}",
                )
                per_file_inputs.append((pdf_file, paper_id, citation_text))

        if st.button("Save Uploads", key=f"save_uploads_{selected_project['project_id']}"):
            for pdf_file, paper_id, citation_text in per_file_inputs:
                sanitized_id = re.sub(r'[^a-zA-Z0-9_-]', '-', paper_id).strip('-')
                default_id = f"{selected_project['project_id']}-{int(time.time())}"
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

                citation_format = None
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

    project_papers = []
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
                                if (
                                    existing_paper
                                    and existing_paper.get('citation_format') == 'bibtex'
                                    and existing_paper.get('citation')
                                ):
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
