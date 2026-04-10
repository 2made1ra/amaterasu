# Frontend Overview

The frontend of this project is built as a Single Page Application (SPA) to provide a fast, dynamic, and seamless user experience.

## Technologies Used

* **Svelte:** The core frontend framework. Unlike React or Vue, Svelte doesn't use a virtual DOM. Instead, it compiles components into highly efficient vanilla JavaScript at build time, resulting in excellent performance and small bundle sizes.
* **Vite:** Used as the build tool and development server. Vite significantly speeds up the development process by serving source code over native ESM, enabling instant Hot Module Replacement (HMR).
* **Tailwind CSS:** A utility-first CSS framework. It is used to style components directly within the HTML markup, allowing for rapid UI development and maintaining a consistent design system without writing custom CSS files.
* **Axios:** A promise-based HTTP client used to make requests to the FastAPI backend.
* **Svelte Routing:** Used for client-side routing within the SPA to navigate between different views (e.g., login, dashboard, chat) without reloading the page.

## Architecture

The frontend communicates with the backend via REST API calls. Authentication state (JWT) is stored locally (e.g., in `localStorage` or memory) and passed in the `Authorization` header for protected requests.
