from datetime import datetime
from typing import Dict, Any, List

import streamlit as st

from core import (
    filter_papers_by_query,
    normalize_profile_name,
    render_clipboard_button,
)
from utils.db import (
    list_papers,
    list_project_groups,
    _connect,
)


def render_analytics_tab(
    selected_project: Dict[str, Any],
    db_path: str,
    project_extractions: List[Dict[str, Any]],
) -> None:
    st.markdown("### 📊 Project Analytics")
    st.caption("View extraction statistics and results")

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

    group_records = list_project_groups(db_path, selected_project['project_id'])
    profile_options_set = {
        normalize_profile_name(ext.get('profile'))
        for ext in project_extractions
        if ext.get('profile')
    }
    profile_options_set.update({normalize_profile_name(g['group_name']) for g in group_records})
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

    search_query = st.text_input(
        "Search papers (ID or title)",
        key=f"analytics_search_{selected_project['project_id']}",
    )

    selection_state_key = f"analytics_selection_{selected_project['project_id']}"
    selection_state = st.session_state.setdefault(selection_state_key, {})

    filtered_papers = filter_papers_by_query(project_papers, search_query)

    select_mode_key = f"analytics_select_mode_{selected_project['project_id']}"
    select_mode = st.session_state.get(select_mode_key, False)
    toggle_cols = st.columns([1, 1, 4])
    with toggle_cols[0]:
        toggle_label = "Select Papers" if not select_mode else "Done Selecting"
        if st.button(toggle_label, key=f"toggle_select_mode_{selected_project['project_id']}"):
            st.session_state[select_mode_key] = not select_mode
            st.experimental_rerun()
    with toggle_cols[1]:
        if select_mode:
            if st.button("Clear Selection", key=f"clear_selection_{selected_project['project_id']}"):
                selection_state.clear()
                st.experimental_rerun()
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

    for paper in filtered_papers:
        selection_state.setdefault(paper['paper_id'], False)

    display_profiles = [normalize_profile_name(p) for p in selected_profiles] if selected_profiles else []
    column_widths = [0.6, 1.8, 3.0] + [1.8 for _ in display_profiles]
    if not select_mode:
        column_widths = column_widths[1:]

    if filtered_papers:
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

        for paper in filtered_papers:
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

            row_cols[col_idx].markdown(f"`{paper['paper_id']}`")
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

    if select_mode and filtered_papers:
        selected_ids = [pid for pid, val in selection_state.items() if val]
        selected_bib = []
        lookup = {paper['paper_id']: paper for paper in filtered_papers}
        for pid in selected_ids:
            paper = lookup.get(pid)
            if paper and paper.get('citation_format') == 'bibtex' and paper.get('citation'):
                selected_bib.append(paper['citation'])
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
