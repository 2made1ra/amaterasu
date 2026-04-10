# Schemas Layer (`app/schemas`)

## Purpose
The Schemas layer defines Pydantic models. These models are used to validate incoming HTTP request payloads, serialize data into JSON for HTTP responses, and enforce type safety across the application. They ensure that the API receives and returns exactly the data it expects.

## Internal Structure
- **`user.py`**: Schemas for user operations, such as `UserCreate` (input for registration), `UserResponse` (output format hiding the password), and `UserUpdate`.
- **`document.py`**: Schemas for document metadata, including inputs for updating extracted metadata during the Human-in-the-Loop review process.
- **`token.py`**: Schemas representing the JWT token payload and the response structure for authentication endpoints.

## Interactions
- **Used by `api`**: Endpoints use schemas in their function signatures to automatically validate request bodies and format responses.
- **Used by `crud`**: CRUD functions often accept "Create" or "Update" schemas as input to know what data to write to the database.
