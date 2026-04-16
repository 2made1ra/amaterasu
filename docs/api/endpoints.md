# API Endpoints Overview

The backend exposes a RESTful API built with FastAPI. All endpoints are prefixed with `/api/v1`.

You can view the fully interactive Swagger UI documentation by running the backend server and navigating to `http://localhost:8000/docs`.

Below is a conceptual overview of the primary endpoint groups.

## 1. Authentication (`/api/v1/auth`)

These endpoints handle user registration, login, and token generation. They utilize JWT (JSON Web Tokens) for secure, stateless authentication. The system requires an initial admin user role to manage general users.

* **`POST /auth/register`**: Register a new user account.
* **`POST /auth/login`**: Authenticate a user with a username and password. Returns an access token (JWT) upon success.
* *(Protected routes hereafter require the `Authorization: Bearer <token>` header).*

## 2. Documents (`/api/v1/documents`)

These endpoints handle the uploading, processing, and management of files.

* **`POST /documents/upload`**: Upload a new PDF and start the human-in-the-loop confirmation flow.
* **`POST /documents/{id}/confirm`**: Confirm the extracted metadata and mark the document as confirmed.
* **`GET /documents/`**: Retrieve a list of all documents owned by the authenticated user.
* **`GET /documents/{id}/preview`**: Return the PDF file for inline preview in the contract modal.
* **`POST /documents/{id}/chat`**: Send a temporary contract-scoped query. This chat is not persisted in session history.

## 3. Workspace Sessions (`/api/v1/chat-sessions`)

These endpoints back the main three-panel workspace.

* **`GET /chat-sessions/`**: List the current user's saved main chat sessions.
* **`POST /chat-sessions/`**: Create a new main workspace session.
* **`GET /chat-sessions/{id}`**: Load a session's messages and persisted explorer snapshot.
* **`DELETE /chat-sessions/{id}`**: Delete a saved main workspace session and its persisted history.
* **`POST /chat-sessions/{id}/messages`**: Send a message to the main session.
  * **Payload:** `{ "query": "..." }`
  * **Response:** returns the assistant message, the updated snapshot, the current session title, and basic search metadata.
* **`PATCH /chat-sessions/{id}/snapshot`**: Persist changes to the results pane state, such as selected node or expanded folders.

## 4. Legacy Chat (`/api/v1/chat`)

This endpoint still exists for the earlier global/document chat flow, but the main dashboard no longer depends on it.

* **`POST /chat/`**: Send a natural-language query with an optional `document_id`.
