# CRUD Layer (`app/crud`)

## Purpose
The CRUD (Create, Read, Update, Delete) layer provides an abstraction over database operations. It encapsulates the SQLAlchemy queries required to interact with the database, ensuring that database logic is not leaked into the API or Services layers.

## Internal Structure
- **`crud_user.py`**: Contains functions to create users, retrieve users by username or ID, and update user information.
- **`crud_document.py`**: Contains functions to save document metadata, route lifecycle transitions, create/update extraction runs, upsert extracted facts, aggregate batch progress, and manage review status.
- **`crud_chat_session.py`**: Persists workspace `chat_sessions` and `chat_messages`, including explorer snapshot fields and message history for the main panel.

## Interactions
- **Consumes from `models`**: Operates on SQLAlchemy models to interact with the database tables.
- **Consumes from `schemas`**: Takes Pydantic schemas as input to create or update database records, validating data before it hits the database.
- **Used by `api`**: Endpoints call CRUD functions directly for simple data retrieval or modification tasks.
- **Used by `services`**: Complex business operations may call CRUD functions to persist state or fetch required data for processing.
