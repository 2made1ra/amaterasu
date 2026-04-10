# API Layer (`app/api`)

## Purpose
The API layer acts as the entry point for all client requests. It defines the HTTP endpoints, routes, and handles incoming HTTP requests, mapping them to the appropriate business logic or database operations. It serves as the bridge between the external world (e.g., frontend, external API consumers) and the internal application logic.

## Internal Structure
- **`deps.py`**: Contains dependency injection functions. These are reusable components that resolve request dependencies, such as extracting the current user from a JWT token or obtaining a database session.
- **`api_v1/api.py`**: The main API router that aggregates all sub-routers from the `endpoints` directory into a single v1 router.
- **`api_v1/endpoints/`**: Contains the actual route definitions, organized by domain:
  - `auth.py`: Endpoints for user login, authentication, and token generation.
  - `chat.py`: Endpoints for interacting with the RAG (Retrieval-Augmented Generation) agent.
  - `documents.py`: Endpoints for uploading, reviewing, and managing documents, including the Human-in-the-Loop (HitL) validation step.

## Interactions
- **Consumes from `schemas`**: Uses Pydantic models to validate incoming request bodies and format outgoing response payloads.
- **Consumes from `services`**: Delegates complex business logic (like LLM interactions or RAG pipelines) to the services layer.
- **Consumes from `crud`**: Calls CRUD operations to read from or write to the database.
- **Consumes from `db`**: Uses database sessions provided via dependency injection (from `deps.py`).
- **Consumes from `core`**: Uses configuration and security utilities for authentication and authorization.
