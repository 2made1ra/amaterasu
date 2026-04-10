# Models Layer (`app/models`)

## Purpose
The Models layer defines the database schema using SQLAlchemy ORM (Object Relational Mapping). These models represent the actual tables, columns, and relationships in the PostgreSQL database.

## Internal Structure
- **`user.py`**: Defines the `User` model, including fields like id, email, hashed_password, and role.
- **`document.py`**: Defines the `Document` model, representing metadata about uploaded documents, such as filename, upload date, status (for the HitL process), and extracted AI metadata.

## Interactions
- **Inherits from `db`**: All models inherit from the declarative base class provided by `app/db/base_class.py`.
- **Used by `crud`**: CRUD operations query and modify instances of these models.
- **Used by Alembic**: (If configured) Alembic uses these models to auto-generate database migration scripts.
