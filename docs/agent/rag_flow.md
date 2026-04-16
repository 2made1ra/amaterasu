# The RAG Pipeline Flow

This document describes the current boundary between the phase-1 ingestion foundation and the existing RAG service in `backend/app/services/rag.py`.

## 1. Current Upload Boundary

`POST /documents/upload` no longer runs the RAG pipeline inline.

The current request flow is:

1. validate the uploaded PDF;
2. save the file to local storage;
3. create a `documents` row with lifecycle fields such as `review_status`, `processing_status`, and `indexing_status`;
4. return immediately with a document id and initial statuses;
5. log a placeholder asynchronous dispatch event.

This means the upload endpoint does not currently call:

* `PyPDFLoader`;
* text splitting;
* metadata extraction prompts;
* Qdrant writes.

Those steps are planned to move into a background ingestion pipeline.

## 2. Current Data Preparation Layer

The backend foundation now includes PostgreSQL tables intended for the future ingestion pipeline:

* `documents`: file metadata, ownership, lifecycle statuses, active extraction version, last error, and batch-ingestion fields;
* `contract_facts`: extracted JSON facts keyed by document and extraction version;
* `extraction_runs`: processing attempts, timestamps, run status, and error details.

`GET /documents/{id}` reads this data so the frontend can poll document state and extracted facts.

## 3. Existing Querying Path

The project still contains an existing vector-search path in `app/services/rag.py`. When it is used:

1. **Filtering (Tenant Isolation):** `query_rag` receives the query, the `owner_id`, and an optional `document_id`. It constructs a Qdrant filter that must match `metadata.owner_id` and may match `metadata.document_id`.
2. **Retrieval:** The query is embedded and matched against stored vectors in Qdrant.
3. **Prompt Construction:** Retrieved chunks plus the user question are inserted into a prompt template.
4. **Generation:** The LLM generates an answer using the retrieved context.
5. **Response:** The backend returns the generated answer as plain text.

## 4. Important Note

The vector-search service and the upload lifecycle are currently in a transitional state:

* query-time RAG code still exists;
* phase-1 upload no longer feeds that index synchronously;
* the target architecture is to reintroduce extraction and indexing through background workers instead of HTTP request handling.
