# Core Layer (`app/core`)

## Purpose
The Core layer is responsible for application-wide configurations, environment variable management, and common security mechanisms. It sets up the foundational settings required by the rest of the application to run properly.

## Internal Structure
- **`config.py`**: Utilizes Pydantic's `BaseSettings` to load, validate, and store environment variables (e.g., database URLs, JWT secret keys, Qdrant host/collections/vector size, Celery broker/queues/rate limits, upload and parsed-artifact directories, chunking for indexing). It also holds LLM and embeddings provider defaults (`LLM_PROVIDER`, `LLM_MODEL`, `EMBEDDINGS_*`) and LM Studio client settings (`LMSTUDIO_API_BASE`, `LMSTUDIO_API_KEY`) used by the services layer.
- **`security.py`**: Contains utility functions for security, such as:
  - Password hashing and verification (using bcrypt/passlib).
  - JWT token generation and decoding.

## Interactions
- **Used by `api`**: The API layer uses the security utilities to issue tokens and verify passwords, and reads configuration for setup.
- **Used by `db`**: The database layer uses the configuration to establish connections to PostgreSQL.
- **Used by `tasks`**: Celery configuration and worker rate limits are read from core settings.
- **Used by `services`**: The services layer uses configuration settings (like LLM API keys) to initialize external clients.
