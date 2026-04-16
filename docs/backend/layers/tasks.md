# Tasks Layer (`app/tasks`)

## Purpose

The Tasks layer defines Celery background jobs for the document pipeline. Parsing, LLM fact extraction, and Qdrant indexing run outside the HTTP request cycle so uploads stay fast and long-running work can be rate-limited and queued.

## Internal Structure

- **`base.py`**: Defines `LoggedTask`, a Celery `Task` subclass that logs success, failure, and retry events for observability.
- **`documents.py`**: Registers the main document pipeline tasks:
  - **`process_document`**: Loads the document, creates an `extraction_run`, parses the PDF to Markdown via `document_parser`, updates processing status, and enqueues `extract_document_facts` on the same queue family (high-priority vs bulk) as the document.
  - **`extract_document_facts`**: Reads the Markdown artifact, calls `fact_extraction` to produce validated facts, upserts `contract_facts`, completes the run, and may **auto-approve** trusted bulk imports before enqueueing indexing.
  - **`index_document`**: Verifies approval, loads facts and Markdown, builds summary + chunks via `document_indexing`, and performs idempotent Qdrant upserts through `qdrant_index`.
- **`__init__.py`**: Package marker; task modules are imported by Celery autodiscovery and by `app/worker.py`.

## Queue Selection

`select_document_queue` maps `queue_priority` and `ingestion_source` to either `CELERY_HIGH_PRIORITY_QUEUE` (default UI uploads) or `CELERY_BULK_QUEUE` (bulk / low priority). `index_document` enqueue after approval uses the same mapping so indexing follows the document’s intended lane.

## Worker Entry Point

- **`app/worker.py`**: Imports `celery_app` and the `documents` task module so task names are registered when workers start with `celery -A app.worker`.
- **`app/celery_app.py`**: Instantiates Celery with broker/result backend from `core.config`, declares the two document queues, and calls `autodiscover_tasks(["app.tasks"])`.

## Interactions

- **Consumes from `core`**: Broker URLs, queue names, extraction rate limits (`CELERY_EXTRACTION_RATE_LIMIT`).
- **Consumes from `crud`**: Document lifecycle, extraction runs, facts, and statuses.
- **Consumes from `services`**: PDF parsing, fact extraction, indexing splits/summary, Qdrant upserts.
- **Invoked from `api`**: Upload and confirm paths enqueue `process_document` / `index_document` via `apply_async` with explicit queues.
