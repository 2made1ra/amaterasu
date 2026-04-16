# Database Layer (`app/db`)

## Purpose
The Database layer is responsible for managing the connection to the underlying relational database (PostgreSQL). It handles session creation, connection pooling, and provides the base class for all SQLAlchemy ORM models.

## Internal Structure
- **`session.py`**: Configures the SQLAlchemy `Engine` and `sessionmaker`. It creates the database connection pool using the connection string defined in the core configuration.
- **`base_class.py`**: Defines the declarative base class (`Base`) from which all SQLAlchemy models inherit. It includes automatic table name generation based on the class name.
- **`base.py`**: A convenience file that imports the `Base` class and all model classes. Alembic uses this module to resolve the full model metadata during migration generation and execution.

## Migration Notes

Schema creation is migration-driven.

* Alembic configuration lives under `backend/alembic.ini` and `backend/alembic/`.
* The current phase-1 migration creates the `documents`, `contract_facts`, and `extraction_runs` tables and prepares the schema for controlled bulk ingestion.
* The application entrypoint no longer calls `Base.metadata.create_all(...)`.

## Interactions
- **Consumes from `core`**: Uses the configuration settings (like `DATABASE_URL`) from `core/config.py` to connect to the database.
- **Used by `models`**: SQLAlchemy models inherit from the `Base` class defined here.
- **Used by `api` (via `deps.py`)**: Provides database sessions to API endpoints on a per-request basis.
