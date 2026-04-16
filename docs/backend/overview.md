# Backend Overview

The backend serves as the API, persistence layer, and workspace orchestration layer for the application. It now supports two distinct chat modes:

* a persistent main workspace chat stored in chat sessions with saved explorer snapshots;
* a temporary contract-scoped chat used inside the contract modal without writing to session history.

## Technologies Used

* **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic interactive API documentation (Swagger UI and ReDoc).
* **Uvicorn:** An ASGI web server implementation for Python used to run the FastAPI application.
* **SQLAlchemy:** The Python SQL toolkit and Object Relational Mapper (ORM) used to interact with the PostgreSQL database. It allows defining database schemas as Python classes.
* **Alembic:** A lightweight database migration tool for usage with SQLAlchemy. It manages changes to the database schema over time.
* **PostgreSQL:** The primary relational database used to store structured data like user accounts and metadata about uploaded documents.
* **JWT (JSON Web Tokens):** Used for stateless authentication. The `python-jose` library is used to encode and decode tokens, while `passlib` handles password hashing (bcrypt).

## Architecture & Organization

The backend code is organized following a standard full-stack FastAPI template structure:

* **`app/api/`:** Contains the API routers and endpoints, including auth, documents, legacy chat, and workspace chat sessions.
* **`app/core/`:** Contains core configuration settings (e.g., environment variables management via Pydantic) and security utilities.
* **`app/crud/`:** Contains CRUD operations for documents, users, and persistent workspace sessions/messages.
* **`app/db/`:** Database connection setup, session management, and Base classes for SQLAlchemy models.
* **`app/models/`:** SQLAlchemy ORM models for users, documents, chat sessions, and chat messages.
* **`app/schemas/`:** Pydantic models used for data validation, serialization, and deserialization of API requests and responses.
* **`app/services/`:** Contains business logic and integration code, including the RAG pipeline (`rag.py`), LLM integrations (`llm.py`), and workspace response shaping (`workspace.py`).
* **`main.py`:** The entry point of the FastAPI application.

## Persistent Workspace Entities

The v1 workspace refactor introduces two new persistent entities:

* `chat_sessions`
  * owned by a user;
  * stores title and explorer snapshot fields (`result_tree_json`, `selected_node_id`, `expanded_node_ids`, `view_mode`);
  * tracks `created_at`, `updated_at`, and `last_message_at`.
* `chat_messages`
  * belongs to a `chat_session`;
  * stores `role`, `content`, optional `meta`, and `created_at`.

For the first iteration, the workspace snapshot is stored directly on `chat_sessions` rather than in a dedicated `workspace_snapshots` table.

## Current Flow Boundaries

The backend now exposes separate flows for:

* **Main workspace chat:** `GET/POST /chat-sessions`, `GET /chat-sessions/{id}`, `POST /chat-sessions/{id}/messages`, `PATCH /chat-sessions/{id}/snapshot`.
* **Document management:** upload, confirm, list, preview, and temporary contract chat under `/documents`.
* **Legacy chat endpoint:** `/chat` still exists, but the dashboard is built around `/chat-sessions`.

## Search Response Shaping

`app/services/workspace.py` is responsible for shaping the main workspace response into:

* an `assistant_message`;
* a normalized `result_tree` for the explorer;
* basic `search_metadata`.

The current implementation uses a flat contract list as the default grouping mode. This is the planned fallback until supplier-based grouping is available.

## Detailed Layer Documentation

For a deep dive into each architectural layer, refer to the following documents:
- [API Layer (`app/api`)](./layers/api.md)
- [Core Layer (`app/core`)](./layers/core.md)
- [CRUD Layer (`app/crud`)](./layers/crud.md)
- [Database Layer (`app/db`)](./layers/db.md)
- [Models Layer (`app/models`)](./layers/models.md)
- [Schemas Layer (`app/schemas`)](./layers/schemas.md)
- [Services Layer (`app/services`)](./layers/services.md)

## Core Processes & C4 Diagrams

The key workflows within the backend have been documented with C4 PlantUML diagrams. Refer to the following documents to understand these workflows in detail:
- [Authentication Flow](./processes/authentication.md)
- [Document Upload & Human-in-the-Loop Review](./processes/document_upload.md)
- [RAG Agent Chat & Search](./processes/rag_chat.md)
