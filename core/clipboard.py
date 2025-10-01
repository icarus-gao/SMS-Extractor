import html
import json
from typing import Optional
import streamlit as st
import streamlit.components.v1 as components
from uuid import uuid4


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
    <div style=\"width:{width}; display:flex; flex-direction:column; gap:0.25rem; align-items:flex-start;\">
      <button id=\"{button_id}\" title={js_tooltip}
              style=\"background:#f1f3f5;border:1px solid #ced4da;border-radius:0.5rem;padding:0.35rem 0.8rem;font-size:0.88rem;font-weight:600;color:#1f2933;cursor:pointer;\">
        {safe_label}
      </button>
      <span id=\"{status_id}\" style=\"font-size:0.72rem;color:#64748b;\"></span>
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
