# Core Layer (`app/core`)

## Purpose
The Core layer is responsible for application-wide configurations, environment variable management, and common security mechanisms. It sets up the foundational settings required by the rest of the application to run properly.

## Internal Structure
- **`config.py`**: Utilizes Pydantic's `BaseSettings` to load, validate, and store environment variables (e.g., database URLs, API keys, JWT secret keys, Qdrant configurations). This ensures that configuration is strongly typed and validated at startup.
- **`security.py`**: Contains utility functions for security, such as:
  - Password hashing and verification (using bcrypt/passlib).
  - JWT token generation and decoding.

## Interactions
- **Used by `api`**: The API layer uses the security utilities to issue tokens and verify passwords, and reads configuration for setup.
- **Used by `db`**: The database layer uses the configuration to establish connections to PostgreSQL and Qdrant.
- **Used by `services`**: The services layer uses configuration settings (like LLM API keys) to initialize external clients.
