# Backend Setup Guide

This guide describes how to run and set up the FastAPI backend application and its dependencies using `uv`.

## Prerequisites

* **uv:** Ensure you have [uv](https://github.com/astral-sh/uv) installed.
* **Docker & Docker Compose:** Required to run the PostgreSQL and Qdrant databases.

## Infrastructure Setup

The backend relies on two database services:
1. **PostgreSQL** (Relational DB)
2. **Qdrant** (Vector DB)

Start these services using Docker Compose from the root of the project:

```bash
docker-compose up -d
```

This will start PostgreSQL on port `5432` and Qdrant on ports `6333` and `6334`.

## Backend Application Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Sync dependencies and create a virtual environment:
   ```bash
   uv sync
   ```
   *Note: This creates a `.venv` directory and installs all dependencies listed in `pyproject.toml`.*

3. Configure Environment Variables:
   Create a `.env` file in the `backend/` directory or ensure the environment variables are set. Key variables typically include:
   * `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://user:password@localhost/app_db`).
   * `QDRANT_HOST`: e.g., `localhost`.
   * `QDRANT_PORT`: e.g., `6333`.
   * `SECRET_KEY`: A secure random string for JWT signing.
   * `UPLOAD_DIR`: Optional override for where uploaded PDFs are stored locally.
   * `MAX_UPLOAD_SIZE_BYTES`: Optional maximum allowed upload size. The current default is `20971520` bytes (`20 MB`).
   * `OPENAI_API_KEY` (or equivalent for your LLM provider).

## Running the Application

To start the FastAPI development server:

```bash
uv run uvicorn app.main:app --reload
```

The API will be accessible at `http://localhost:8000`.

## Interactive Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can view it at:
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

## Database Initialization

The backend now uses **Alembic** as the primary schema mechanism.

Run migrations from the `backend/` directory:

```bash
uv run alembic upgrade head
```

For SQL review before applying a migration:

```bash
uv run alembic upgrade head --sql
```

`main.py` no longer creates tables automatically on startup.
