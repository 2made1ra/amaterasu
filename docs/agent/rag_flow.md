# The Query Orchestration Flow

This document describes the boundary between the ingestion/approval/indexing pipeline and the current search orchestration layer.

## 1. Current Upload Boundary

`POST /documents/upload` no longer runs the RAG pipeline inline.

The current request flow is:

1. validate the uploaded PDF;
2. save the file to local storage;
3. create a `documents` row with lifecycle fields such as `review_status`, `processing_status`, and `indexing_status`;
4. enqueue `process_document` on Celery (`document-high-priority` or `document-bulk`);
5. return immediately with a document id and initial statuses.

This means the upload endpoint itself does not call:

* `PyPDFLoader`;
* text splitting;
* metadata extraction prompts;
* Qdrant writes.

Those heavy steps are now shifted to background worker execution for parsing and fact extraction.

## 2. Current Data Preparation Layer

The backend foundation now includes PostgreSQL tables intended for the ingestion and approval pipeline:

* `documents`: file metadata, ownership, lifecycle statuses, active extraction version, last error, and batch-ingestion fields;
* `contract_facts`: extracted JSON facts keyed by document and extraction version;
* `extraction_runs`: processing attempts, timestamps, run status, and error details.

`GET /documents/{id}` reads this data so the frontend can poll document state and extracted facts.

`GET /batches/{batch_id}` now provides aggregate counters for controlled bulk ingestion progress.

Approved documents also carry audit metadata on the `documents` row itself:

* `approval_source` distinguishes manual approval from trusted bulk auto-approval;
* `approved_at` captures when the decision was made;
* `approved_by_user_id` captures the reviewer when manual confirmation is used.

## 3. Existing Querying Path

The current search path is routed through `app/services/search_orchestration.py`. When it is used:

1. **Classification:** `query_router.py` classifies the query into one of the explicit route types and extracts structured filters.
2. **SQL path:** `sql_search.py` builds a SQLAlchemy query against `contract_facts` for reporting-style questions.
3. **Summary-first vector path:** `vector_search.py` searches `contract_summaries` first, then searches `contract_chunks` within the shortlisted document ids.
4. **Contract-scoped narrowing:** if a `document_id` is provided, the query is constrained to that context.
5. **Response shaping:** `workspace.py` turns the result into the assistant message and explorer payload.

## 4. Important Note

The legacy `app/services/rag.py` file still exists, but the chat endpoints now use the query orchestration layer instead of relying on that single path.

The pipeline is now split cleanly:

* uploads run asynchronous parsing and fact extraction;
* approved uploads trigger idempotent indexing into separate summary and chunk collections;
* chat uses explicit query routing instead of sending everything through one generic vector search.
