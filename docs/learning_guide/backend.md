# Backend Architecture & Foundations

To work on the backend of an app like Amaterasu, you need a clear picture of HTTP APIs, persistence, security, and where long-running work should live.

## 1. RESTful APIs

**Theory:** REST (Representational State Transfer) is a common style for HTTP APIs: resources map to URLs, and verbs (`GET`, `POST`, `PATCH`, `DELETE`) express intent. Responses use standard status codes and JSON bodies.

**In this project:** The app is built with **FastAPI**. Routes live under the **`/api/v1`** prefix (see `app/main.py` and `app/api/api_v1/`). Type hints and Pydantic models drive validation; Swagger UI is served at `/docs`.

*Example:* `POST /api/v1/documents/upload` accepts a PDF, persists metadata, and enqueues background work—heavy parsing and LLM calls do not block the request thread.

## 2. Object-Relational Mapping (ORM)

**Theory:** An ORM maps tables to classes so you work with Python objects and expressions instead of hand-written SQL for most operations.

**In this project:** **SQLAlchemy 2.x** with **PostgreSQL**. Models live in `app/models/`; database access is concentrated in `app/crud/` (e.g. users, documents, chat sessions). **Alembic** owns schema changes—run `alembic upgrade head` instead of relying on automatic table creation at startup.

## 3. JWT Authentication

**Theory:** The client sends `Authorization: Bearer <token>` after login; the server verifies the signature and reads claims (e.g. user id) without server-side session storage.

**In this project:** Login/register live under `/api/v1/auth`. Dependencies in `app/api/deps.py` resolve the current user for protected routes so uploads, documents, chat sessions, and batches stay scoped per user.

## 4. Layered layout (`backend/app/`)

**Theory:** Separating HTTP handlers, business logic, and data access keeps the codebase testable and easier to change.

**In this project:**

| Layer | Role |
|--------|------|
| `api/` | Routers and endpoint handlers (`auth`, `documents`, `batches`, `chat`, `chat-sessions`). |
| `schemas/` | Pydantic request/response models. |
| `services/` | Orchestration: query routing, SQL and vector search, PDF parsing, fact extraction, indexing helpers, workspace response shaping. |
| `crud/` | Database operations (users, documents, chat sessions/messages, facts, extraction runs). |
| `tasks/` | Celery tasks: `process_document`, `extract_document_facts`, `index_document`. |
| `core/` | Settings (`pydantic-settings`) and password/JWT helpers. |
| `db/` | Engine, session, declarative base. |

Changing how a query is stored usually touches `crud/` and `models/`; changing how a question is answered often touches `services/` without rewriting routers.

## 5. Asynchronous document pipeline

**Theory:** File ingestion, PDF parsing, and LLM calls can take seconds or minutes. Running them inside the HTTP worker ties up workers and times out clients—so production systems offload this to **background workers** and a **message broker**.

**In this project:** **Redis** backs **Celery**. Upload enqueues `process_document`; workers parse PDFs to Markdown, run **fact extraction** with an LLM, then (after human or trusted approval) **index** document summaries and text chunks into **Qdrant**. Two queues separate interactive uploads from bulk imports (`document-high-priority` vs `document-bulk`). Details: [Tasks layer](../backend/layers/tasks.md), [Document upload process](../backend/processes/document_upload.md).
