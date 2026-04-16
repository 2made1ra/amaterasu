# Backend Setup Guide

This guide describes how to run and set up the FastAPI backend and its dependencies using [uv](https://github.com/astral-sh/uv).

## Prerequisites

* **Python 3.12+** (see `requires-python` in `backend/pyproject.toml`).
* **uv:** Install [uv](https://github.com/astral-sh/uv).
* **Docker** with Compose: used for PostgreSQL, Qdrant, and Redis locally.

## Infrastructure

The backend expects:

1. **PostgreSQL** — relational data (users, documents, chat sessions, facts, extraction runs).
2. **Qdrant** — vector collections for approved document summaries and chunks after indexing.
3. **Redis** — Celery broker and result backend for the document pipeline.

From the **repository root**, start all three services:

```bash
docker compose up -d
```

(On older Docker installs, `docker-compose up -d` is equivalent.)

Services in `docker-compose.yml`:

| Service   | Image            | Host ports   | Notes                                      |
|----------|------------------|--------------|--------------------------------------------|
| `db`     | `postgres:15`    | `5432`       | Default DB: `app_db`, user `user`, password `password` |
| `qdrant` | `qdrant/qdrant`  | `6333`, `6334` | REST API and dashboard on `6333`         |
| `redis`  | `redis:7-alpine` | `6379`       | Broker for Celery                          |

**Redis-only (optional):** If PostgreSQL and Qdrant are already running elsewhere, you can start only Redis for workers, for example:

```bash
docker compose up -d redis
```

## Backend application setup

1. Go to the backend directory:

   ```bash
   cd backend
   ```

2. Install dependencies and the virtualenv:

   ```bash
   uv sync
   ```

   This creates `.venv` and installs everything from `pyproject.toml`.

3. **Environment variables**

   Settings are defined in `app/core/config.py` and read from the process environment (`os.getenv` / Pydantic Settings). Set them in your shell, IDE run configuration, or deployment secrets.

   The API process does **not** automatically load a `.env` file at startup (the pytest suite loads `backend/.env` in `tests/conftest.py` for tests only). If you keep secrets in `backend/.env`, load them into the environment before `uvicorn` (for example via your IDE, direnv, or `export`).

   **Database & API**

   * `DATABASE_URL` — PostgreSQL URL. Default matches Compose: `postgresql://user:password@localhost/app_db`.
   * `SECRET_KEY` — JWT signing secret (change in any non-local deployment).
   * `API_V1_PREFIX` — Optional; default `/api/v1`.

   **Qdrant**

   * `QDRANT_HOST`, `QDRANT_PORT` — Default `localhost` / `6333`.
   * `QDRANT_SUMMARY_COLLECTION`, `QDRANT_CHUNK_COLLECTION` — Collection names (defaults: `contract_summaries`, `contract_chunks`).
   * `QDRANT_VECTOR_SIZE` — Embedding size (default `384`, aligned with the default embeddings model).

   **Redis & Celery**

   * `REDIS_URL` — Default `redis://localhost:6379/0`; used as fallback for broker/backend when those are unset.
   * `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — Override Redis URLs for Celery if needed.
   * `CELERY_HIGH_PRIORITY_QUEUE`, `CELERY_BULK_QUEUE` — Queue names (defaults: `document-high-priority`, `document-bulk`).
   * `CELERY_EXTRACTION_RATE_LIMIT` — Fact extraction task rate limit (default `10/m`).
   * `BULK_IMPORT_BATCH_SIZE` — Max files per batch when using the bulk importer CLI (default `50`).

   **Uploads & artifacts**

   * `UPLOAD_DIR` — PDF storage (default `backend/uploads`).
   * `PARSED_MARKDOWN_DIR` — Parsed Markdown artifacts (default `backend/artifacts/markdown`).
   * `MAX_UPLOAD_SIZE_BYTES` — Default `20971520` (20 MB).

   **Indexing (chunking for Qdrant)**

   * `INDEXING_CHUNK_SIZE` — Default `1000`.
   * `INDEXING_CHUNK_OVERLAP` — Default `200`.

   **LLM & embeddings**

   Implemented in `app/services/llm.py`:

   * Defaults: `LLM_PROVIDER` / `EMBEDDINGS_PROVIDER` = effective Hugging Face path (`LLM_MODEL`, `EMBEDDINGS_MODEL` as above).
   * For **LM Studio** (OpenAI-compatible server): set `LLM_PROVIDER=lmstudio` and/or `EMBEDDINGS_PROVIDER=lmstudio`, plus `LMSTUDIO_API_BASE` (default `http://localhost:1234/v1`) and `LMSTUDIO_API_KEY`.

## Running the API

```bash
uv run uvicorn app.main:app --reload
```

Base URL: `http://localhost:8000`. JSON routes live under `/api/v1` (see `app/main.py`).

## Celery workers

Run two workers so interactive uploads are not blocked by bulk traffic:

```bash
uv run celery -A app.worker worker -Q document-high-priority --loglevel=info
```

```bash
uv run celery -A app.worker worker -Q document-bulk --loglevel=info
```

Queue names match `CELERY_HIGH_PRIORITY_QUEUE` and `CELERY_BULK_QUEUE` if you override them.

## Interactive API docs

With the server running:

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

## Database migrations

Schema changes are managed with **Alembic**. From `backend/`:

```bash
uv run alembic upgrade head
```

Preview SQL without applying (optional):

```bash
uv run alembic upgrade head --sql
```

Tables are not created automatically in `main.py`; migrations are required after pulling schema changes.

## Bulk import CLI

The controlled bulk importer calls `POST /documents/upload` once per file and passes batch metadata.

Example:

```bash
uv run python -m app.services.bulk_ingestion /path/to/pdfs \
  --api-base-url http://localhost:8000 \
  --token <bearer-token> \
  --batch-prefix quarterly-archive \
  --trusted-import
```

Behavior:

* Collects `.pdf` files in the given folder only (top-level entries; subfolders are not scanned).
* Splits work into batches of at most `BULK_IMPORT_BATCH_SIZE` files (default `50`).
* Uploads each file with `batch_id`, `BULK_IMPORT`, and low-priority queue metadata.

## Tests

Fast non-integration tests:

```bash
uv run pytest -q -m "not integration"
```

Integration-marked tests may call a real LM Studio instance; see `pyproject.toml` marker description and your `.env` for integration runs.
