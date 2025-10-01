"""UI components for the Streamlit SMS extractor."""

from .papers import render_papers_tab
from .extraction import render_extraction_tab
from .analytics import render_analytics_tab
from .settings import render_settings_tab

__all__ = [
    "render_papers_tab",
    "render_extraction_tab",
    "render_analytics_tab",
    "render_settings_tab",
]
