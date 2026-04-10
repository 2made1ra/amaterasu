# Backend Setup Guide

This guide describes how to run and set up the FastAPI backend application and its dependencies.

## Prerequisites

* **Python:** Ensure you have Python 3.9+ installed.
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

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Environment Variables:
   Create a `.env` file in the `backend/` directory or ensure the environment variables are set. Key variables typically include:
   * `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://user:password@localhost/app_db`).
   * `QDRANT_HOST`: e.g., `localhost`.
   * `QDRANT_PORT`: e.g., `6333`.
   * `SECRET_KEY`: A secure random string for JWT signing.
   * `OPENAI_API_KEY` (or equivalent for your LLM provider).

## Running the Application

To start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be accessible at `http://localhost:8000`.

## Interactive Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can view it at:
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

## Database Initialization

In the current setup, tables are created automatically on startup via `Base.metadata.create_all(bind=engine)` in `main.py`. For production or complex migrations, you should configure and use **Alembic**.
