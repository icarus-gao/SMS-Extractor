# SMS-Extractor Project Overview

## Purpose
SMS-Extractor is a Streamlit application that helps researchers extract structured data from PDF papers using large language models (LLMs). The tool focuses on systematic mapping studies (SMS) and similar review workflows, guiding users through project management, paper ingestion, and automated field extraction aligned with a configurable codebook.

## High-Level Architecture
The application is organized into three main layers:

1. **Streamlit User Interface (`app.py`)** – Provides project creation, paper management, extraction, and analytics views. It orchestrates interactions between the database, configuration files, and LLM-driven extraction routines.
2. **Persistence Layer (`utils/db.py`)** – Wraps a SQLite database that tracks papers, projects, attribute groups, and extraction runs.
3. **Extraction Utilities (`utils/extractor.py`, `utils/schemas.py`)** – Convert PDFs into prompt-ready text, call an OpenAI-compatible API, normalize responses, and persist both structured CSV outputs and raw JSON logs.

```
 ┌─────────────┐      ┌──────────────────────┐      ┌─────────────────────┐
 │  Streamlit  │─────▶│  Extraction Helpers  │─────▶│  Output Artifacts   │
 │  Interface  │◀────┤│  (LLM + CSV export) │◀────┤│  (CSV / JSON files) │
 └─────────────┘      └──────────────────────┘      └─────────────────────┘
        │                         ▲
        ▼                         │
 ┌────────────────┐         ┌──────────┐
 │ SQLite Storage │◀────────│  PDFs    │
 └────────────────┘         └──────────┘
```

## Key Components

- Loads environment configuration and checks external connectivity before rendering the UI. The read-only preset in `config/default_global_models.json` is copied into `data/config/global_models.json` on first start; all later edits happen in that generated copy.【F:app.py†L1-L120】
- Initializes the SQLite database and exposes settings via the sidebar, including project selection, creation, and global settings access.【F:app.py†L54-L208】【F:app.py†L320-L400】
- Provides tabs for managing papers, running extractions, viewing analytics, and configuring project details. Paper uploads are stored under each project's folder and deduplicated using PDF SHA-256 hashes.【F:app.py†L430-L600】
- The **Project Settings** tab exposes editable metadata (name, default model, notes) and lets users swap in updated codebooks/prompts for each feature group without touching the template directory. File locations are surfaced for quick navigation.【F:app.py†L1040-L1120】
- Includes a one-click “Reset Workspace” action in the sidebar to wipe local projects, databases, and outputs for fresh testing.【F:app.py†L320-L400】
- Renders analytics in a Zotero-style table: filter by feature group, toggle selection mode, copy individual BibTeX entries, or export the chosen subset in bulk.【F:app.py†L760-L990】

### Database Utilities (`utils/db.py`)
- Creates tables for papers, projects, attribute groups, and extraction logs, and applies lightweight migrations when the schema evolves.【F:utils/db.py†L1-L122】
- Offers CRUD helpers to insert papers, register projects, and record extraction results, including batch metadata for multi-part jobs.【F:utils/db.py†L124-L276】

### Extraction Pipeline (`utils/extractor.py`)
- Reads the YAML codebook to determine target fields and enumerations, then converts PDFs to text with page markers. Optional environment variables limit pages or characters processed.【F:utils/extractor.py†L1-L83】【F:utils/extractor.py†L101-L135】
- Renders a Jinja2 prompt that injects the citation, field list, and enum hints, and calls the configured LLM endpoint with retry-aware handling of connection, rate-limit, and API errors.【F:utils/extractor.py†L37-L100】
- Normalizes responses to ensure every field is populated with at least placeholder evidence, and appends results to `data/master.csv`, `data/evidence_log.csv`, and timestamped JSON archives.【F:utils/extractor.py†L137-L176】

### Data Schema Helpers (`utils/schemas.py`)
- Defines the `FieldEvidence` model and helper functions that flatten structured responses into CSV rows and expand them into per-field evidence logs for downstream auditing.【F:utils/schemas.py†L1-L22】

### Configuration (Uploads)
- During project creation or feature-group setup, upload the YAML codebook and Jinja2 prompt. The files are stored under `data/projects/<project_id>/feature_groups/<group>/` for later use.

## Data Flow
1. **Project Setup:** Users create a project via the Streamlit form, optionally uploading custom codebooks and prompt templates. The app stores the configuration paths in the database and scaffolds directories under `data/projects/<project_id>/`.【F:app.py†L400-L478】
2. **Paper Ingestion:** Uploaded PDFs are saved inside the selected project's `papers` folder. Metadata and file hashes are persisted in the `papers` table to prevent duplicates.【F:app.py†L210-L300】【F:utils/db.py†L124-L174】
3. **Extraction:** For each paper, the app reads the PDF, renders the extraction prompt, and calls the LLM. Responses populate structured outputs and evidence logs while raw JSON is archived for auditing.【F:utils/extractor.py†L101-L176】
4. **Analytics:** Extraction summaries and success rates are calculated from the database and displayed in the Streamlit analytics tab, helping teams monitor progress across projects.【F:app.py†L320-L380】

## Extensibility Considerations
- **Custom Models:** Set `OPENAI_BASE_URL`, `OPENAI_MODEL`, and optional `OPENAI_TEMPERATURE` in `.env` or Streamlit `secrets.toml` to target different LLM providers.【F:utils/extractor.py†L49-L88】
- **OCR Support:** For scanned PDFs, extend `extract_pdf_text` with an OCR branch (hinted in README) to improve recall.【F:README.md†L35-L37】
- **Field Profiles:** Future work can use `project_groups` to define attribute subsets that reduce token consumption, aligning with the profiles block in `app.py` and the configuration precedence outlined in the README.【F:app.py†L132-L173】【F:utils/db.py†L214-L260】

## Default Outputs
- `data/master.csv`: Flat table of extracted values.
- `data/evidence_log.csv`: Quote-level evidence per field.
- `data/raw/*.json`: Timestamped archives of raw LLM responses for auditing.【F:utils/extractor.py†L151-L176】

These artifacts enable reproducibility and downstream analysis for systematic reviews and consensus algorithm benchmarking.
