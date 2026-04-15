# Frontend Setup Guide

This guide describes how to run, configure, and build the Svelte frontend application. It also explains the underlying tooling used to run the app.

## The Tooling: Vite

This project uses **Vite** (French for "quick", pronounced `/vit/`) as its build tool and development server.

### Why Vite?
Older tools like Webpack would bundle your entire application before the server could start, which could take a long time on large projects. Vite, on the other hand, takes advantage of native ES modules in the browser. It serves your source code directly to the browser, and only compiles the files you are currently editing.

This results in:
* **Near-instant server start time.**
* **Extremely fast Hot Module Replacement (HMR)**: When you save a file, only that specific component updates on your screen instantly, without losing the application state (like form inputs).

---

## Prerequisites

* **Node.js:** Ensure you have Node.js installed (v18 or higher is recommended).
* **NPM or Yarn:** A package manager to install dependencies.

## Installation

1. Navigate to the `frontend` directory from the root of the repository:
   ```bash
   cd frontend
   ```

2. Install the project dependencies listed in `package.json`:
   ```bash
   npm install
   ```

---

## Development & Configuration

### Starting the Dev Server

To start the Vite development server with Hot Module Replacement:

```bash
npm run dev
```

The application will be accessible in your browser, typically at `http://localhost:3000/` (Vite will print the exact URL in your terminal).

### Integrating with the Backend

For the frontend to work, the backend API must also be running.

1. **Default Setup:** By default, the frontend is hardcoded (in `src/lib/api.js`) to look for the backend at `http://localhost:8000/api/v1`. If your backend is running locally via `uvicorn` or Docker on port 8000, no configuration is needed.

2. **Docker Compose:** If you are running the entire stack via Docker Compose from the root directory (`docker-compose up`), the frontend might be served via a web server container, or you might run the frontend locally while connecting to the Dockerized backend. Ensure the backend container exposes port `8000` to your host machine so the browser can reach it.

### Changing the Backend URL (Environment Variables)

Currently, the backend URL is hardcoded in `src/lib/api.js`. In a production environment, you should replace this with an environment variable.

Vite exposes environment variables that start with `VITE_`.
1. Create a `.env` file in the `frontend` directory:
   ```env
   VITE_API_BASE_URL=http://your-production-api.com/api/v1
   ```
2. Update `src/lib/api.js` to use it:
   ```javascript
   const api = axios.create({
     // Fallback to localhost if the env var isn't set
     baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
   });
   ```

---

## Building for Production

When you are ready to deploy, you cannot run `npm run dev`. You need to compile the Svelte code into plain HTML, CSS, and optimized JavaScript.

1. Run the build command:
   ```bash
   npm run build
   ```
2. Vite will create a `dist/` directory containing your production-ready static assets.
3. These files are completely static. You do not need Node.js to serve them in production. You can host the `dist/` folder on any static web host, S3 bucket, or serve them using Nginx/Apache.

To preview the built application locally to ensure it works before deploying:
```bash
npm run preview
```

---

## Troubleshooting

### "Network Error" or CORS Issues in the Console
* **Cause:** The frontend cannot reach the backend.
* **Fix:**
  1. Verify the backend server is running and accessible at `localhost:8000`.
  2. Open the browser's Network tab (F12) to see exactly what URL the frontend is trying to hit.
  3. Ensure the backend has CORS properly configured to accept requests from `http://localhost:3000`.

### Port Already in Use
* **Cause:** Another application is running on port `3000`.
* **Fix:** Vite will usually automatically pick the next available port (e.g., `3001`). Check your terminal output to see the actual port Vite assigned.

### Changes Aren't Showing Up
* **Cause:** Browser caching or Vite HMR crashed.
* **Fix:** Do a hard refresh in your browser (Ctrl+F5 or Cmd+Shift+R). If that fails, stop the terminal process (`Ctrl+C`) and restart `npm run dev`.
