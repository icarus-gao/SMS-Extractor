import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st

from .constants import DEFAULT_PROFILE_NAME


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


def trigger_rerun() -> None:
    """Safely force Streamlit to rerun, compatible with legacy APIs."""
    try:
        st.experimental_rerun()
    except AttributeError:
        try:
            st.rerun()
        except AttributeError:
            pass
