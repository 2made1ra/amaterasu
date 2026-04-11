# Backend Architecture & Foundations

To build the backend of a full-stack AI application like Amaterasu, you need to understand how to expose services via an API, how to interact with a relational database, and how to secure those endpoints.

## 1. RESTful APIs
**Theory:** REST (Representational State Transfer) is an architectural style for designing networked applications. It relies on a stateless, client-server protocol, usually HTTP. In a REST API, endpoints (URLs) represent resources (like a User or a Document), and standard HTTP methods define the actions:
*   `GET`: Retrieve data.
*   `POST`: Create new data.
*   `PUT/PATCH`: Update existing data.
*   `DELETE`: Remove data.

**Project Application:** We use **FastAPI**, a modern Python web framework. FastAPI uses Python type hints to automatically validate data and generate documentation (Swagger UI).
*   *Example:* When the frontend wants to upload a document, it sends an HTTP `POST` request to `/api/v1/documents/upload`. FastAPI catches this request, validates the incoming file, and triggers the logic to save it.

## 2. Object-Relational Mapping (ORM)
**Theory:** An ORM is a technique that lets you query and manipulate data from a database using an object-oriented paradigm. Instead of writing raw SQL queries (`SELECT * FROM users`), you work with Python classes and objects. This abstracts away the specific SQL dialect and makes code much easier to maintain.

**Project Application:** We use **SQLAlchemy** combined with **PostgreSQL**.
*   *Example:* We define a `User` class in Python that maps to a `users` table in the database. When we need to find a user, instead of `SELECT * FROM users WHERE email = 'x'`, we use SQLAlchemy syntax: `db.query(User).filter(User.email == email).first()`.

## 3. JWT Authentication (Security)
**Theory:** JSON Web Tokens (JWT) are a secure way to transmit information between parties as a JSON object. In modern web apps, they are the standard for stateless authentication.
1. The user logs in with credentials.
2. The server verifies them and generates a token (JWT) containing user info (like user ID) signed with a secret key.
3. The client stores this token and sends it in the HTTP headers of subsequent requests (`Authorization: Bearer <token>`).
4. The server validates the token's signature to ensure the user is authenticated.

**Project Application:** The Amaterasu backend has endpoints for login. Upon successful login, FastAPI generates a JWT. Any endpoint that requires security (like uploading a document) checks for a valid JWT before proceeding, ensuring only authenticated users can perform actions.

## 4. Layered Architecture (The "Clean" Approach)
**Theory:** Putting all your code in one file is a recipe for disaster. Good backend design separates concerns into layers:
*   **Routers/API Layer:** Handles incoming HTTP requests and returns HTTP responses.
*   **Services Layer:** Contains the core business logic (e.g., the actual steps to process a document).
*   **Data Access Layer (CRUD/DB):** Handles the direct database interactions using the ORM.

**Project Application:** The `backend/app/` folder is structured exactly this way:
*   `api/` contains the routing endpoints.
*   `services/` contains logic for AI, document processing, etc.
*   `crud/` handles the database queries.
*   This means if we decide to change our database later, we only need to update the `crud/` layer, leaving the APIs and Services untouched.