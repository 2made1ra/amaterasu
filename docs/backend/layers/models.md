# Models Layer (`app/models`)

## Purpose
The Models layer defines the database schema using SQLAlchemy ORM (Object Relational Mapping). These models represent the actual tables, columns, and relationships in the PostgreSQL database.

## Internal Structure
- **`user.py`**: Defines the `User` model, including fields like id, email, hashed_password, and role.
- **`document.py`**: Defines the `Document` model for uploaded files and their lifecycle fields, including file metadata, review/processing/indexing statuses, active extraction version, last error, and batch-ingestion metadata.
- **`contract_fact.py`**: Defines extracted JSON facts stored per document and per extraction version.
- **`extraction_run.py`**: Defines processing attempts for a document, including extraction version, run status, timestamps, and error payloads.

## Interactions
- **Inherits from `db`**: All models inherit from the declarative base class provided by `app/db/base_class.py`.
- **Used by `crud`**: CRUD operations query and modify instances of these models.
- **Used by Alembic**: `app/db/base.py` imports all models so Alembic can resolve the project metadata for migrations.
