# Frontend SPA Foundations

The frontend of Amaterasu provides the user interface. It needs to be fast, responsive, and capable of maintaining state without constantly reloading the page.

## 1. Single Page Applications (SPA)
**Theory:** Traditionally, clicking a link meant the server built an entirely new HTML page and sent it to your browser, causing a full page refresh. A Single Page Application (SPA) changes this. The browser loads a single HTML file initially. As the user navigates, JavaScript dynamically rewrites the current web page with new data from the web server, making the app feel incredibly fast and responsive, like a native desktop app.

**Project Application:** Amaterasu's frontend is an SPA. When you navigate from the login screen to the document upload screen, the page doesn't refresh; JavaScript simply swaps out the login components for the upload components.

## 2. Component-Based Frameworks (Svelte)
**Theory:** Modern frontends are built using components—reusable, isolated pieces of UI (like a Button, a Navbar, or a Chat Interface). Components manage their own HTML structure, CSS styling, and JavaScript logic (state). Frameworks like React, Vue, or Svelte help manage these components.

**Project Application:** We use **Svelte**. Unlike React, which does most of its work in the browser, Svelte is a compiler. It takes your component files (`.svelte`) and compiles them into highly optimized vanilla JavaScript at build time.
*   *Example:* The chat interface is likely a Svelte component that maintains its own internal "state" (the list of chat messages). When a new message arrives from the backend, Svelte automatically updates the UI to reflect the new state.

## 3. Tooling: Vite and Tailwind CSS
**Theory:**
*   **Bundlers (Vite):** Modern JavaScript relies on hundreds of files and libraries. Bundlers take all these files and package them into optimized files that the browser can quickly download. **Vite** is a modern, extremely fast build tool.
*   **Utility-first CSS (Tailwind):** Instead of writing custom CSS classes in separate files, utility frameworks provide small, single-purpose CSS classes (e.g., `text-center`, `p-4` for padding) that you apply directly in your HTML/components.

**Project Application:** Amaterasu uses **Vite** to run the local development server and compile the Svelte code. For styling, it relies heavily on **Tailwind CSS**, allowing for rapid UI development without writing custom CSS files.

## 4. API Communication & Routing
**Theory:**
*   **Routing:** In an SPA, the URL in the browser still needs to change when the user navigates, even without a page reload. Client-side routers intercept URL changes and load the correct components.
*   **API Calls:** The frontend needs a way to request data from the backend. This is usually done asynchronously via the `fetch` API or libraries like `axios`.

**Project Application:**
*   Amaterasu uses `svelte-routing` to handle navigation between pages (e.g., `/login`, `/dashboard`).
*   It uses **Axios** to communicate with the FastAPI backend. Crucially, Axios is configured with an **Interceptor**. Every time the frontend sends a request to the backend, this interceptor automatically attaches the JWT token (stored in the browser's `localStorage` after login) to the request headers, ensuring all API calls are authenticated.