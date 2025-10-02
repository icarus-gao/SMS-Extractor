import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import time


def _connect(db_path: str) -> sqlite3.Connection:
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
    except Exception:
        pass
    return conn


def init_db(db_path: str = None) -> str:
    db_path = db_path or str(Path("data/app.db").resolve())
    with _connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                paper_id TEXT PRIMARY KEY,
                project_id TEXT,
                title TEXT,
                citation TEXT,
                citation_format TEXT,
                pdf_sha256 TEXT,
                pdf_path TEXT,
                created_at INTEGER,
                updated_at INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
            """
        )
        # Projects table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT,
                codebook_path TEXT,
                template_path TEXT,
                model TEXT,
                notes TEXT,
                created_at INTEGER,
                updated_at INTEGER
            )
            """
        )
        # Project attribute groups
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS project_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                group_name TEXT NOT NULL,
                fields_json TEXT NOT NULL,
                codebook_path TEXT,
                prompt_path TEXT,
                description TEXT,
                created_at INTEGER,
                updated_at INTEGER,
                UNIQUE(project_id, group_name),
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT NOT NULL,
                project_id TEXT,
                profile TEXT,
                codebook_path TEXT,
                model TEXT,
                base_url TEXT,
                mock INTEGER,
                prompt_tokens INTEGER,
                status TEXT,
                result_json TEXT,
                error_msg TEXT,
                batch_id TEXT,
                part_index INTEGER,
                part_total INTEGER,
                created_at INTEGER,
                FOREIGN KEY (paper_id) REFERENCES papers(paper_id),
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
            """
        )
        # migration: add missing columns if upgrading from older versions
        try:
            cols = {r[1] for r in c.execute("PRAGMA table_info(papers)").fetchall()}
            if "project_id" not in cols:
                c.execute("ALTER TABLE papers ADD COLUMN project_id TEXT")
            if "citation_format" not in cols:
                c.execute("ALTER TABLE papers ADD COLUMN citation_format TEXT")
            if "pdf_sha256" not in cols:
                c.execute("ALTER TABLE papers ADD COLUMN pdf_sha256 TEXT")
        except Exception:
            pass
        try:
            gcols = {r[1] for r in c.execute("PRAGMA table_info(project_groups)").fetchall()}
            if "codebook_path" not in gcols:
                c.execute("ALTER TABLE project_groups ADD COLUMN codebook_path TEXT")
            if "prompt_path" not in gcols:
                c.execute("ALTER TABLE project_groups ADD COLUMN prompt_path TEXT")
            if "description" not in gcols:
                c.execute("ALTER TABLE project_groups ADD COLUMN description TEXT")
        except Exception:
            pass
        try:
            ecols = {r[1] for r in c.execute("PRAGMA table_info(extractions)").fetchall()}
            if "project_id" not in ecols:
                c.execute("ALTER TABLE extractions ADD COLUMN project_id TEXT")
            if "batch_id" not in ecols:
                c.execute("ALTER TABLE extractions ADD COLUMN batch_id TEXT")
            if "part_index" not in ecols:
                c.execute("ALTER TABLE extractions ADD COLUMN part_index INTEGER")
            if "part_total" not in ecols:
                c.execute("ALTER TABLE extractions ADD COLUMN part_total INTEGER")
        except Exception:
            pass
        # indexes
        # helpful index for dedup lookup
        c.execute("CREATE INDEX IF NOT EXISTS idx_papers_pdfsha ON papers(pdf_sha256)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_papers_project ON papers(project_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_extractions_batch ON extractions(batch_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_groups_project ON project_groups(project_id)")
        conn.commit()
    return db_path


def insert_or_update_paper(
    db_path: str,
    paper_id: str,
    project_id: Optional[str],
    citation: str,
    pdf_path: str,
    title: Optional[str] = None,
    citation_format: Optional[str] = None,
    pdf_sha256: Optional[str] = None,
) -> None:
    now = int(time.time())
    with _connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT paper_id FROM papers WHERE paper_id=?", (paper_id,))
        exists = c.fetchone() is not None
        if exists:
            c.execute(
                "UPDATE papers SET project_id=?, title=?, citation=?, citation_format=?, pdf_sha256=?, pdf_path=?, updated_at=? WHERE paper_id=?",
                (project_id, title, citation, citation_format, pdf_sha256, pdf_path, now, paper_id),
            )
        else:
            c.execute(
                "INSERT INTO papers (paper_id, project_id, title, citation, citation_format, pdf_sha256, pdf_path, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (paper_id, project_id, title, citation, citation_format, pdf_sha256, pdf_path, now, now),
            )
        conn.commit()


def add_extraction(
    db_path: str,
    paper_id: str,
    project_id: Optional[str],
    profile: Optional[str],
    codebook_path: str,
    model: str,
    base_url: Optional[str],
    mock: bool,
    prompt_tokens: Optional[int],
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_msg: Optional[str] = None,
    batch_id: Optional[str] = None,
    part_index: Optional[int] = None,
    part_total: Optional[int] = None,
) -> int:
    payload = json.dumps(result, ensure_ascii=False) if result is not None else None
    now = int(time.time())
    with _connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO extractions (
                paper_id, project_id, profile, codebook_path, model, base_url, mock, prompt_tokens, status, result_json, error_msg, batch_id, part_index, part_total, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                paper_id,
                project_id,
                profile,
                codebook_path,
                model,
                base_url,
                1 if mock else 0,
                prompt_tokens,
                status,
                payload,
                error_msg,
                batch_id,
                part_index,
                part_total,
                now,
            ),
        )
        conn.commit()
        return int(c.lastrowid)


def list_papers(db_path: str) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT paper_id, project_id, title, citation, citation_format, pdf_sha256, pdf_path, created_at, updated_at FROM papers ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_paper(db_path: str, paper_id: str) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT paper_id, project_id, title, citation, citation_format, pdf_sha256, pdf_path, created_at, updated_at FROM papers WHERE paper_id=?",
            (paper_id,),
        ).fetchone()
    return dict(row) if row else None


def list_extractions(db_path: str, paper_id: str) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, paper_id, project_id, profile, codebook_path, model, base_url, mock, prompt_tokens, status, result_json, error_msg, batch_id, part_index, part_total, created_at
            FROM extractions
            WHERE paper_id=?
            ORDER BY created_at DESC
            """,
            (paper_id,),
        ).fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        # Defer result JSON parsing; the UI will parse it only when needed.
        out.append(item)
    return out


def latest_extraction(db_path: str, paper_id: str) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, paper_id, project_id, profile, codebook_path, model, base_url, mock, prompt_tokens, status, result_json, error_msg, batch_id, part_index, part_total, created_at
            FROM extractions
            WHERE paper_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (paper_id,),
        ).fetchone()
    return dict(row) if row else None


def get_paper_by_sha(db_path: str, pdf_sha256: str) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT paper_id, project_id, title, citation, citation_format, pdf_sha256, pdf_path, created_at, updated_at FROM papers WHERE pdf_sha256=?",
            (pdf_sha256,),
        ).fetchone()
    return dict(row) if row else None


def delete_extraction(db_path: str, extraction_id: int) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM extractions WHERE id=?", (extraction_id,))
        conn.commit()


def delete_paper(db_path: str, paper_id: str) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM extractions WHERE paper_id=?", (paper_id,))
        conn.execute("DELETE FROM papers WHERE paper_id=?", (paper_id,))
        conn.commit()


def rename_paper_id(db_path: str, old_id: str, new_id: str) -> None:
    with _connect(db_path) as conn:
        c = conn.cursor()
        # ensure new_id not exists
        exist = c.execute("SELECT 1 FROM papers WHERE paper_id=?", (new_id,)).fetchone()
        if exist:
            raise ValueError("Target paper_id already exists")
        # update in a txn
        c.execute("UPDATE extractions SET paper_id=? WHERE paper_id=?", (new_id, old_id))
        c.execute("UPDATE papers SET paper_id=? WHERE paper_id=?", (new_id, old_id))
        conn.commit()


# Project CRUD
def upsert_project(db_path: str, project_id: str, name: str, codebook_path: str, template_path: str, model: Optional[str] = None, notes: Optional[str] = None) -> None:
    now = int(time.time())
    with _connect(db_path) as conn:
        c = conn.cursor()
        exists = c.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone() is not None
        if exists:
            c.execute(
                "UPDATE projects SET name=?, codebook_path=?, template_path=?, model=?, notes=?, updated_at=? WHERE project_id=?",
                (name, codebook_path, template_path, model, notes, now, project_id),
            )
        else:
            c.execute(
                "INSERT INTO projects (project_id, name, codebook_path, template_path, model, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (project_id, name, codebook_path, template_path, model, notes, now, now),
            )
        conn.commit()


def rename_project_id(db_path: str, old_id: str, new_id: str) -> None:
    now = int(time.time())
    with _connect(db_path) as conn:
        c = conn.cursor()
        exists = c.execute("SELECT 1 FROM projects WHERE project_id=?", (new_id,)).fetchone()
        if exists:
            raise ValueError("Target project_id already exists")
        c.execute("UPDATE projects SET project_id=?, updated_at=? WHERE project_id=?", (new_id, now, old_id))
        c.execute("UPDATE papers SET project_id=? WHERE project_id=?", (new_id, old_id))
        c.execute("UPDATE extractions SET project_id=? WHERE project_id=?", (new_id, old_id))
        c.execute("UPDATE project_groups SET project_id=? WHERE project_id=?", (new_id, old_id))
        conn.commit()


def list_projects(db_path: str) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT project_id, name, codebook_path, template_path, model, notes, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_project(db_path: str, project_id: str) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT project_id, name, codebook_path, template_path, model, notes, created_at, updated_at FROM projects WHERE project_id=?",
            (project_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_project(db_path: str, project_id: str) -> None:
    """Delete a project including database records and filesystem directory"""
    import shutil
    
    # Delete from database (cascade delete related records)
    with _connect(db_path) as conn:
        # Delete papers associated with this project
        conn.execute("DELETE FROM papers WHERE project_id=?", (project_id,))
        # Delete extractions
        conn.execute("DELETE FROM extractions WHERE project_id=?", (project_id,))
        # Delete project groups
        conn.execute("DELETE FROM project_groups WHERE project_id=?", (project_id,))
        # Delete the project itself
        conn.execute("DELETE FROM projects WHERE project_id=?", (project_id,))
        conn.commit()
    
    # Delete project directory from filesystem
    project_path = Path(db_path).parent / "projects" / project_id
    if project_path.exists():
        try:
            shutil.rmtree(project_path)
        except Exception as e:
            # Log error but don't fail - database deletion succeeded
            print(f"Warning: Could not delete project directory {project_path}: {e}")


# Project groups CRUD
def upsert_project_group(
    db_path: str,
    project_id: str,
    group_name: str,
    fields: Optional[List[str]] = None,
    codebook_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    now = int(time.time())
    payload = json.dumps(list(fields or []), ensure_ascii=False)
    with _connect(db_path) as conn:
        c = conn.cursor()
        exists = c.execute("SELECT 1 FROM project_groups WHERE project_id=? AND group_name=?", (project_id, group_name)).fetchone() is not None
        if exists:
            c.execute(
                "UPDATE project_groups SET fields_json=?, codebook_path=?, prompt_path=?, description=?, updated_at=? WHERE project_id=? AND group_name=?",
                (payload, codebook_path, prompt_path, description, now, project_id, group_name),
            )
        else:
            c.execute(
                "INSERT INTO project_groups (project_id, group_name, fields_json, codebook_path, prompt_path, description, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (project_id, group_name, payload, codebook_path, prompt_path, description, now, now),
            )
        conn.commit()


def list_project_groups(db_path: str, project_id: str) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, project_id, group_name, fields_json, codebook_path, prompt_path, description, created_at, updated_at
            FROM project_groups
            WHERE project_id=?
            ORDER BY group_name
            """,
            (project_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def rename_project_group(db_path: str, project_id: str, old_name: str, new_name: str) -> None:
    if old_name == new_name:
        return
    now = int(time.time())
    with _connect(db_path) as conn:
        c = conn.cursor()
        exists = c.execute(
            "SELECT 1 FROM project_groups WHERE project_id=? AND group_name=?",
            (project_id, new_name),
        ).fetchone()
        if exists:
            raise ValueError("Target feature group name already exists")
        c.execute(
            "UPDATE project_groups SET group_name=?, updated_at=? WHERE project_id=? AND group_name=?",
            (new_name, now, project_id, old_name),
        )
        c.execute(
            "UPDATE extractions SET profile=? WHERE project_id=? AND profile=?",
            (new_name, project_id, old_name),
        )
        conn.commit()


def delete_project_group(db_path: str, project_id: str, group_name: str) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM project_groups WHERE project_id=? AND group_name=?", (project_id, group_name))
        conn.commit()
