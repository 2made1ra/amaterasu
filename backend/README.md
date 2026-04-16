# Backend

## Phase 2 local runtime

Start Redis locally for Celery:

```bash
docker compose up -d redis
```

Run the API:

```bash
uv run uvicorn app.main:app --reload
```

Run a worker dedicated to interactive uploads:

```bash
uv run celery -A app.worker worker -Q document-high-priority --loglevel=info
```

Run a second worker for bulk ingestion traffic:

```bash
uv run celery -A app.worker worker -Q document-bulk --loglevel=info
```

This queue split keeps UI uploads from being starved behind low-priority archive imports.

## Bulk importer

The controlled bulk importer reuses `POST /documents/upload` and keeps the one-file-per-request contract intact.

```bash
uv run python -m app.services.bulk_ingestion /path/to/pdfs \
  --api-base-url http://localhost:8000 \
  --token <bearer-token> \
  --batch-prefix quarterly-archive \
  --trusted-import
```

The importer will:

- scan a folder for `.pdf` files
- split work into batches of at most `50` files
- upload each file individually with `batch_id`, `BULK_IMPORT`, and low queue priority

## Verification

Run the non-integration backend suite with:

```bash
uv run pytest -q -m "not integration"
```
