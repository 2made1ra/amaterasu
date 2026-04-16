# Frontend Overview

The frontend is a Single Page Application (SPA) centered on a workspace for contract search and review. The main dashboard is no longer a simple "documents on the left, one chat on the right" screen. It is now a three-zone workspace with persistent main chat sessions, a results explorer, and a temporary modal flow for contract-specific review.

## Technologies Used

* **Svelte:** The core frontend framework. Unlike React or Vue, Svelte doesn't use a virtual DOM. Instead, it compiles components into highly efficient vanilla JavaScript at build time, resulting in excellent performance and small bundle sizes.
* **Vite:** Used as the build tool and development server. Vite significantly speeds up the development process by serving source code over native ESM, enabling instant Hot Module Replacement (HMR).
* **Tailwind CSS:** A utility-first CSS framework. It is used to style components directly within the HTML markup, allowing for rapid UI development and maintaining a consistent design system without writing custom CSS files.
* **Axios:** A promise-based HTTP client used to make requests to the FastAPI backend.
* **Custom lightweight routing store:** The app uses a small store-based router in `src/lib/router.js` for `/` and `/dashboard`.

## Architecture

The frontend communicates with the backend via REST API calls. Authentication state (JWT) is stored in `localStorage` and attached through the shared Axios client in `src/lib/api.js`.

## Workspace Composition

The dashboard is orchestrated by [frontend/src/pages/Dashboard.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/pages/Dashboard.svelte). Its responsibilities are:

* load the authenticated user;
* load and activate main chat sessions from `/chat-sessions`;
* send main session messages and keep the explorer snapshot in sync;
* open a contract modal when the user selects a contract in the explorer.

The UI is split into the following components:

* [frontend/src/components/WorkspaceToolbar.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/WorkspaceToolbar.svelte): top-level controls, new session button, document import toggle, logout.
* [frontend/src/components/ChatSessionSidebar.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/ChatSessionSidebar.svelte): saved main workspace sessions.
* [frontend/src/components/ResultExplorerPanel.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/ResultExplorerPanel.svelte): results tree / explorer.
* [frontend/src/components/AgentChatPanel.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/AgentChatPanel.svelte): persistent main chat.
* [frontend/src/components/ContractViewerModal.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/ContractViewerModal.svelte): modal shell for contract preview + temporary chat.
* [frontend/src/components/ContractPreviewPane.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/ContractPreviewPane.svelte): fetches the PDF preview through the protected preview endpoint and renders it in an `iframe`.
* [frontend/src/components/ContractChatPanel.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/ContractChatPanel.svelte): temporary per-contract chat that is cleared when the modal closes.

## Upload Flow in the New Layout

Document import is no longer the primary left panel. The upload UI now lives inside the workspace toolbar via [frontend/src/components/DocumentUpload.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/DocumentUpload.svelte), which:

* uploads a PDF;
* reflects asynchronous lifecycle states from the backend (`QUEUED`, `PARSING`, `FACTS_READY`, `APPROVED`, `INDEXING`, `INDEXED`, `FAILED`);
* shows the current document library;
* emits `documentsChanged` so the dashboard can refresh library counts in the toolbar.
