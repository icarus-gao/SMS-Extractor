# Django Migration Plan

## Current Scaffold
- Django project `sms_backend/` with apps:
  - `projects` – maps to the existing `projects` and `project_groups` tables.
  - `papers` – maps to the `papers` table.
  - `extractions` – maps to the `extractions` table.
- Models mirror the SQLite schema located at `data/app.db`; migrations read/write the same file.
- Admin site registered for quick inspection of existing records.
- Primitive JSON endpoints under `/api/` (`projects`, `papers`, `extractions`) returning list/detail payloads.

## Next Integration Steps
1. **Authentication & Permissions**
   - Decide on auth strategy (session vs token) for API endpoints.
   - Restrict write operations (create/update/delete) accordingly.
2. **Service Layer**
   - Port Streamlit business logic (uploads, extraction orchestration, manual entry validation) into dedicated Django services or Django REST Framework viewsets.
   - Reuse helpers from the new `core/` package or convert them into pure Python utilities shared between UI and backend.
3. **API Design**
   - Expand endpoints for CRUD operations (project creation, paper uploads, feature-group management, extraction execution triggers).
   - Consider GraphQL or DRF for richer querying; include pagination and filtering aligned with current Streamlit searches.
4. **File Handling**
   - Mirror the `data/projects/<id>/` directory conventions using Django storage backends; ensure proper media/static configuration.
   - Implement secure upload endpoints for PDFs, codebooks, and prompts.
5. **Task Execution**
   - For long-running extractions, integrate Celery or Django Q; store statuses in the `extractions` table and emit WebSocket or polling updates.
6. **Frontend Strategy**
   - Decide whether to embed Django templates, build a SPA, or continue using Streamlit as a separate frontend consuming the new API.
   - If migrating UI entirely, replicate search, pagination, and tabbed workflows with Django templates or a modern JS framework.
7. **Testing & CI**
   - Port existing flows into Django tests: model factories, API endpoint tests, service layer tests.
   - Configure GitHub Actions (or preferred CI) to run `python manage.py test` and linting.
8. **Deployment Configuration**
   - Prepare environment settings (split `settings.py` into base/dev/prod), configure SECRET_KEY management, and static/media storage for production.

## Immediate TODOs
- Expose POST/PUT/DELETE endpoints for each resource.
- Backfill management commands to import/export data between Streamlit and Django contexts.
- Document environment variables required for OpenAI integrations in Django settings.
