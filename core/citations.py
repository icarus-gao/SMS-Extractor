import re
from typing import Optional


def replace_bibtex_key(entry: str, new_key: str) -> str:
    """Replace the citation key in a BibTeX entry with the provided paper_id."""
    pattern = re.compile(r"(@[a-zA-Z]+\s*\{)\s*([^,\s]+)")

    def _sub(match: re.Match[str]) -> str:
        return f"{match.group(1)}{new_key}"

    return pattern.sub(_sub, entry, count=1)


def _cleanup_bibtex_value(value: str) -> str:
    text = value.strip()
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
