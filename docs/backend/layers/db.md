# Database Layer (`app/db`)

## Purpose
The Database layer is responsible for managing the connection to the underlying relational database (PostgreSQL). It handles session creation, connection pooling, and provides the base class for all SQLAlchemy ORM models.

## Internal Structure
- **`session.py`**: Configures the SQLAlchemy `Engine` and `sessionmaker`. It creates the database connection pool using the connection string defined in the core configuration.
- **`base_class.py`**: Defines the declarative base class (`Base`) from which all SQLAlchemy models inherit. It often includes automatic table name generation based on the class name.
- **`base.py`**: A convenience file that imports the `Base` class and all model classes. This is useful for Alembic migrations to detect all models from a single import point.

## Interactions
- **Consumes from `core`**: Uses the configuration settings (like `DATABASE_URL`) from `core/config.py` to connect to the database.
- **Used by `models`**: SQLAlchemy models inherit from the `Base` class defined here.
- **Used by `api` (via `deps.py`)**: Provides database sessions to API endpoints on a per-request basis.
