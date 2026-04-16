# API Layer (`app/api`)

## Purpose
The API layer acts as the entry point for all client requests. It defines the HTTP endpoints, routes, and handles incoming HTTP requests, mapping them to the appropriate business logic or database operations. It serves as the bridge between the external world (e.g., frontend, external API consumers) and the internal application logic.

## Internal Structure
- **`deps.py`**: Contains dependency injection functions. These are reusable components that resolve request dependencies, such as extracting the current user from a JWT token or obtaining a database session.
- **`api_v1/api.py`**: The main API router that aggregates all sub-routers from the `endpoints` directory into a single v1 router.
- **`api_v1/endpoints/`**: Contains the actual route definitions, organized by domain:
  - `auth.py`: Endpoints for user login, authentication, and token generation.
  - `chat.py`: Endpoints for the query-orchestrated chat flow. Global workspace chat and contract-scoped chat both route through the search orchestration layer.
  - `documents.py`: Endpoints for single-file upload, async dispatch, document polling, confirmation/editing, approval metadata, indexing enqueue, preview, and temporary contract chat.
  - `batches.py`: Endpoint for aggregate batch progress (`GET /batches/{batch_id}`).
  - `chat_sessions.py`: CRUD and messaging for persistent main workspace sessions (`/chat-sessions`, messages, snapshot updates).

## Interactions
- **Consumes from `schemas`**: Uses Pydantic models to validate incoming request bodies and format outgoing response payloads.
- **Consumes from `services`**: Delegates workspace shaping, query routing, SQL search, vector search, document indexing helpers, and contract-chat behavior to the services layer. Upload keeps request-cycle work lightweight and dispatches heavy processing asynchronously.
- **Consumes from `tasks`**: Upload dispatches `process_document` to Celery with queue routing based on ingestion metadata.
- **Consumes from `crud`**: Calls CRUD operations to read from or write to the database.
- **Consumes from `db`**: Uses database sessions provided via dependency injection (from `deps.py`).
- **Consumes from `core`**: Uses configuration and security utilities for authentication and authorization.
