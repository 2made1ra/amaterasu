# API Endpoints Overview

The backend exposes a RESTful API built with FastAPI. All endpoints are prefixed with `/api/v1`.

You can view the fully interactive Swagger UI documentation by running the backend server and navigating to `http://localhost:8000/docs`.

Below is a conceptual overview of the primary endpoint groups.

## 1. Authentication (`/api/v1/auth`)

These endpoints handle user registration, login, and token generation. They utilize JWT (JSON Web Tokens) for secure, stateless authentication. The system requires an initial admin user role to manage general users.

* **`POST /auth/register`**: Register a new user account.
* **`POST /auth/login`**: Authenticate a user with a username and password. Returns an access token (JWT) upon success.
* *(Protected routes hereafter require the `Authorization: Bearer <token>` header).*

## 2. Documents (`/api/v1/documents`)

These endpoints handle single-file upload, asynchronous processing dispatch, status polling, and document management.

* **`POST /documents/upload`**: Upload a single PDF, validate it, save it to storage, create a document row, and enqueue background processing.
  * Supports optional service metadata fields for controlled bulk ingestion: `batch_id`, `ingestion_source`, `queue_priority`, and `trusted_import`.
  * The request stays lightweight: parsing and extraction are performed in Celery workers, not inline in the request cycle.
  * Queue routing is explicit (`document-high-priority` for UI uploads, `document-bulk` for bulk/low-priority paths).
* **`GET /documents/{id}`**: Return the current document lifecycle fields plus extracted facts when they exist.
  * Intended for frontend polling.
  * Returns `404` when the document does not exist or belongs to another user.
* **`POST /documents/{id}/confirm`**: Mark the document as approved.
  * Accepts optional edited `facts` and writes them back to the active `contract_facts` version.
  * Updates review status, records approval metadata, and enqueues `index_document` asynchronously.
  * Trusted bulk imports can bypass manual confirmation after fact validation and are marked with `approval_source=TRUSTED_IMPORT`.
* **`GET /documents/`**: Retrieve a list of all documents owned by the authenticated user.
* **`GET /documents/{id}/preview`**: Return the PDF file for inline preview in the contract modal.
* **`POST /documents/{id}/chat`**: Send a temporary contract-scoped query. This chat is not persisted in session history.

## 3. Batches (`/api/v1/batches`)

This endpoint provides aggregate progress for controlled bulk ingestion batches.

* **`GET /batches/{batch_id}`**: Return aggregate counters derived from `documents.batch_id`.
  * Includes raw status counters (`processing_status_counts`, `review_status_counts`, `indexing_status_counts`).
  * Includes derived progress counters (`queued`, `parsing`, `ready_for_review`, `failed`, `approved`, `indexed`).
  * Returns `404` when the batch does not exist or is not visible to the current user.

## 4. Workspace Sessions (`/api/v1/chat-sessions`)

These endpoints back the main three-panel workspace.

* **`GET /chat-sessions/`**: List the current user's saved main chat sessions.
* **`POST /chat-sessions/`**: Create a new main workspace session.
* **`GET /chat-sessions/{id}`**: Load a session's messages and persisted explorer snapshot.
* **`DELETE /chat-sessions/{id}`**: Delete a saved main workspace session and its persisted history.
* **`POST /chat-sessions/{id}/messages`**: Send a message to the main session.
  * **Payload:** `{ "query": "..." }`
  * **Response:** returns the assistant message, the updated snapshot, the current session title, and basic search metadata.
* **`PATCH /chat-sessions/{id}/snapshot`**: Persist changes to the results pane state, such as selected node or expanded folders.

## 5. Legacy Chat (`/api/v1/chat`)

This endpoint still exists for the earlier global/document chat flow, but in the current implementation it is backed by the new phase-4 search orchestration layer rather than the legacy single-collection RAG path.

* **`POST /chat/`**: Send a natural-language query with an optional `document_id`.
  * Without `document_id`, the workspace flow classifies the query and routes it to SQL, summary search, chunk search, or a hybrid path.
  * With `document_id`, the contract-scoped flow uses the same orchestration layer and constrains the search to the selected document context.
  * The implementation uses `app/services/search_orchestration.py`, `app/services/query_router.py`, `app/services/sql_search.py`, and `app/services/vector_search.py`.
