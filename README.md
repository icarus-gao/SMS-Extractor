# Data Extractor with LLM — env-ready v3.1 (English UI)

This release includes:
- **English UI** and README
- **No sidebar API key input** — keys must come from `.env` or Streamlit `secrets.toml`
- **Connectivity test** (/models) to diagnose network/BASE_URL/SSL issues
- **Retry & clearer errors** in `call_llm`
- **Raw JSON save** under `data/raw`
- **Field Profiles** to reduce cost

## Quick start (macOS)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# .env (recommended)
cp .env.example .env
# edit .env:
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-5
# OPENAI_BASE_URL (optional for compatible endpoints)

streamlit run app.py
```

Open http://localhost:8501 :
1) Paste the citation header
2) Upload the PDF
3) Set `paper_id` → click **Run extraction**

Outputs:
- `data/master.csv` — values aligned with your Master schema
- `data/evidence_log.csv` — per-field `value | quote | location`
- `data/raw/*.json` — raw LLM outputs (audit/cache)

## Configuration precedence
`secrets.toml > .env`. The app does **not** expose an API-key input field.

## Field Profiles (cost control)
- **Full Schema** — all fields
- **Only Classification** — `desc.doc_type`, `survey.method_class`, `research.primary_type`, `research.validation_level`
- **RQ1 Modules Only** — `algorithm_family` + `module.*`

## Notes
- Use Python **3.11** to avoid SSL/CA quirks seen on some stacks.
- For scanned PDFs, add an OCR branch in `utils/extractor.py` if you need it.
- If you host an OpenAI-compatible endpoint, set `OPENAI_BASE_URL` in `.env`.
