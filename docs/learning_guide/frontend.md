# Frontend SPA Foundations

The Amaterasu frontend is a **Svelte** single-page application: one initial load, then client-side updates as the user moves between views and loads data from the API.

## 1. Single Page Applications (SPA)

**Theory:** Instead of full page reloads for every navigation, the shell HTML loads once; scripts swap views and fetch JSON from the backend. That keeps the UI responsive and avoids losing client state on every click.

**In this project:** Navigation switches between screens (for example login vs dashboard) without a round-trip HTML reload. The dashboard hosts the main workspace (sessions, explorer, document flows) as Svelte components.

## 2. Components (Svelte)

**Theory:** UIs are built from reusable components: markup, style, and reactive state live together in `.svelte` files.

**In this project:** **Svelte 5** (see `frontend/package.json`) with **Vite** as the dev server and bundler. Components under `frontend/src/components/` and pages under `frontend/src/pages/` compose the experience.

## 3. Vite and Tailwind CSS

**Theory:** **Vite** provides fast dev startup and optimized production bundles. **Tailwind** supplies utility classes for layout and typography so styling stays consistent without large custom CSS files.

**In this project:** `npm run dev` runs Vite; Tailwind is configured for the Svelte app (see `postcss.config.js` / `tailwind.config.js`).

## 4. Client-side routing

**Theory:** The URL should reflect where the user is (bookmarking, back button) even without server-rendered pages. A small router listens to path changes and renders the matching component.

**In this project:** Routing is implemented in **`frontend/src/lib/router.js`** using the **History API** (`pushState` / `popstate`) and a Svelte store (`currentPath`). There is no `svelte-routing` package in dependencies—logic is minimal: e.g. `/` for login, `/dashboard` for the main app (see `App.svelte`).

## 5. API calls and JWT

**Theory:** The browser calls the REST API with `fetch` or an HTTP client. Authenticated apps attach a bearer token on each request.

**In this project:** **`axios`** is configured in **`frontend/src/lib/api.js`**: `baseURL` points to `http://localhost:8000/api/v1`, and a **request interceptor** reads the JWT from `localStorage` and sets `Authorization: Bearer …` when present. After login, subsequent calls to documents, chat sessions, and chat endpoints are authenticated automatically.
