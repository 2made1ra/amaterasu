# State Management and Routing

This document explains how the current workspace frontend manages persistent main chat sessions, explorer state, modal contract chat, and simple client-side routing.

## State Model

The state is split into three layers.

### 1. Shared workspace stores

The shared state for the main dashboard lives in [frontend/src/lib/stores/workspace.js](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/lib/stores/workspace.js).

It stores:

* `sessions`: the list shown in the session sidebar;
* `activeSessionId`: the currently selected persistent main session;
* `activeSessionTitle`: the title restored from the backend or generated from the first query;
* `activeSessionMessages`: the main chat history for the active session;
* `workspaceSnapshot`: the persisted results-pane state, including `result_tree`, `selected_node_id`, `expanded_node_ids`, and `view_mode`.

This store layer is intentionally small and focused on the main workspace. It does not store the temporary modal contract chat.

### 2. Dashboard-local orchestration state

The dashboard page keeps request-specific UI state as local reactive variables, for example:

* bootstrapping and loading flags;
* API error messages for the session list, agent chat, and explorer;
* toolbar document count;
* the currently open contract node for the modal.

This separation keeps the shared stores stable while allowing the page component to manage request lifecycles and optimistic UI updates.

### 3. Modal-local temporary state

The contract modal chat is intentionally ephemeral.

[frontend/src/components/ContractChatPanel.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/ContractChatPanel.svelte) keeps its own local `messages`, `inputQuery`, and error state. When `documentId` changes or the modal is closed, the temporary contract chat is reset instead of being persisted into the main session history.

## Component Communication

The workspace still relies on standard Svelte props and custom events:

* `Dashboard.svelte` passes session data, messages, and snapshot props down into the sidebar, explorer, and main chat components.
* Child components dispatch events like `createSession`, `selectSession`, `send`, `selectNode`, `toggleNode`, and `openContract`.
* `DocumentUpload.svelte` dispatches `documentsChanged` so the toolbar and dashboard can update the visible contract count without coupling the uploader to global app state.

## Routing

Routing is handled by [frontend/src/lib/router.js](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/lib/router.js), not `svelte-routing`.

It provides:

* `currentPath`: a writable store that tracks `window.location.pathname`;
* `navigate(path, { replace })`: a lightweight helper for login and dashboard redirects.

`src/App.svelte` renders either the login page or the dashboard based on `currentPath`, and redirects unknown paths back to `/`.
