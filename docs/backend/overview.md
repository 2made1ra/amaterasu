# Backend Overview

The backend serves as the core API and orchestration layer of the application. It handles user authentication, document management, database interactions, and coordinates the AI Agent for the RAG pipeline.

## Technologies Used

* **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic interactive API documentation (Swagger UI and ReDoc).
* **Uvicorn:** An ASGI web server implementation for Python used to run the FastAPI application.
* **SQLAlchemy:** The Python SQL toolkit and Object Relational Mapper (ORM) used to interact with the PostgreSQL database. It allows defining database schemas as Python classes.
* **Alembic:** A lightweight database migration tool for usage with SQLAlchemy. It manages changes to the database schema over time.
* **PostgreSQL:** The primary relational database used to store structured data like user accounts and metadata about uploaded documents.
* **JWT (JSON Web Tokens):** Used for stateless authentication. The `python-jose` library is used to encode and decode tokens, while `passlib` handles password hashing (bcrypt).

## Architecture & Organization

The backend code is organized following a standard full-stack FastAPI template structure:

* **`app/api/`:** Contains the API routers and endpoints, organized by version (e.g., `api_v1`). Includes route definitions for auth, documents, and chat.
* **`app/core/`:** Contains core configuration settings (e.g., environment variables management via Pydantic) and security utilities.
* **`app/crud/`:** Contains CRUD (Create, Read, Update, Delete) operations for interacting with the database models.
* **`app/db/`:** Database connection setup, session management, and Base classes for SQLAlchemy models.
* **`app/models/`:** SQLAlchemy ORM models defining the database schema.
* **`app/schemas/`:** Pydantic models used for data validation, serialization, and deserialization of API requests and responses.
* **`app/services/`:** Contains business logic and integration code, such as the LangChain RAG pipeline (`rag.py`) and LLM integrations (`llm.py`).
* **`main.py`:** The entry point of the FastAPI application.

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
