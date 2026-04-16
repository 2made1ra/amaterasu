# API Integration & Backend Guidelines

This document explains how the Svelte frontend communicates with the backend and provides guidelines on how the backend should be structured to optimally support this SPA (Single Page Application).

## How the Frontend Connects to the Backend

The frontend uses **Axios** as its HTTP client. The configuration is centralized in `src/lib/api.js`.

### 1. Base URL
By default, the Axios instance points to `http://localhost:8000/api/v1`. All API calls made using this instance will automatically prefix this base URL.
```javascript
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});
```

### 2. Authentication (JWT Interceptor)
The application uses JSON Web Tokens (JWT) for authentication. When a user logs in, the backend returns an `access_token` which is saved in the browser's `localStorage`.

An Axios interceptor automatically attaches this token to the `Authorization` header of every outgoing request:
```javascript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## Guidelines for the Backend

To ensure smooth integration, the backend (FastAPI in this project) should adhere to the following principles:

### 1. CORS (Cross-Origin Resource Sharing)
Since the frontend (running on `localhost:3000`) and the backend (running on `localhost:8000`) operate on different ports, they are considered different origins. The backend **must** have CORS properly configured to allow requests from the frontend origin.
* Allow HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.
* Allow headers: `Authorization`, `Content-Type`.

### 2. Authentication Endpoints
The frontend expects specific endpoints for authentication:
* **POST `/auth/login`**: Expects a form data payload (`application/x-www-form-urlencoded`) with `username` and `password`. It should return a JSON response containing:
  ```json
  {
    "access_token": "your_jwt_string",
    "token_type": "bearer"
  }
  ```
* **POST `/auth/register`**: Expects a JSON payload with `username` and `password`.
* **GET `/auth/me`**: A protected route that validates the JWT token and returns the current user's profile data. If the token is invalid or expired, it should return a `401 Unauthorized` status.

### 3. Error Handling and Status Codes
The backend should use appropriate HTTP status codes:
* **200 OK / 201 Created**: For successful requests.
* **400 Bad Request**: For validation errors or malformed requests.
* **401 Unauthorized**: When authentication is required and has failed or hasn't been provided. The frontend will intercept a 401 error on `/auth/me` and log the user out.
* **403 Forbidden**: When a user is authenticated but lacks permission.
* **404 Not Found**: When a requested resource doesn't exist.

Error messages should ideally be returned in a consistent JSON format, such as `{"detail": "Error message"}`. The frontend catches these details to display to the user.

### 4. RESTful Principles
API endpoints should be logically structured using standard REST HTTP methods:
* `GET /documents/`: Retrieve a list of documents.
* `POST /documents/upload`: Create a new document from one PDF file and optional service metadata.
* `GET /documents/{id}`: Poll the current lifecycle state and extracted facts for one document.
* `POST /documents/{id}/confirm`: Perform a review action on a document.
* `POST /chat/`: Send a message and receive a response.

By maintaining these conventions on the backend, the frontend API integration remains clean, predictable, and easy to debug.
