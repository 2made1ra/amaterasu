# Main page, chats, and contract window refactor plan

Date: 2026-04-16
Status: Draft
Scope: Frontend + Backend + API + documentation

## 1. Refactor goals

Rebuild the main page from the current flow “document upload on the left + single chat on the right” into a new working scenario:

- a narrow left column with history of the manager’s main chat sessions;
- in the main work area, the screen splits into two parts:
  - on the left, a results pane styled like a file system;
  - on the right, chat with the agent;
- chat history must store not only the thread but also the associated state of the left results pane;
- chat history must not be tied to a single uploaded file;
- clicking a found contract opens a modal:
  - contract preview on the left;
  - chat about the selected contract on the right;
- chat inside the modal is a temporary work context and is not saved to history.

## 2. Current state and why it is insufficient

Current code:

- [frontend/src/pages/Dashboard.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/pages/Dashboard.svelte) composes the screen from two zones: `DocumentUpload` on the left, `Chat` on the right.
- [frontend/src/components/Chat.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/Chat.svelte) only supports `global` or `local by document_id` mode.
- [frontend/src/components/DocumentUpload.svelte](/Users/2madeira/DEV/PROJECTS/amaterasu/frontend/src/components/DocumentUpload.svelte) combines document upload and document list, so the left panel is already logically file-centric.
- [backend/app/api/api_v1/endpoints/chat.py](/Users/2madeira/DEV/PROJECTS/amaterasu/backend/app/api/api_v1/endpoints/chat.py) only accepts `query` and optional `document_id`.
- [backend/app/models/document.py](/Users/2madeira/DEV/PROJECTS/amaterasu/backend/app/models/document.py) stores document metadata only, not chat sessions, retrieval results, or user workspace state.

Key gaps between current architecture and target UX:

- no “main manager chat session” entity;
- no message history storage separate from documents;
- no snapshot of the results pane;
- no structured search response as a “supplier → contracts” tree;
- no temporary dialog mode for a specific contract without persisting history;
- no API for previewing the selected contract in a modal.

## 3. Target interaction model

### 3.1 Main work screen

The main page should become a three-zone workspace:

- left column: list of manager chat sessions;
- center column: results pane resembling a file system;
- right column: chat with the agent.

Behavior:

- the manager opens an existing session or creates a new one;
- they send a query in the main chat;
- the agent returns a text answer and a structured set of results;
- results appear to the left of the chat as a tree:
  - list of contracts;
  - or list of supplier folders;
  - contracts live inside folders;
- the state of this tree is persisted with the main chat session;
- when reopening a session, the following are restored:
  - message history;
  - the last results tree;
  - selected node;
  - expanded-folder mode.

### 3.2 Contract window

Clicking a contract in the results tree opens a modal over the main workspace:

- preview of the PDF or document on the left;
- chat scoped to the selected contract on the right.

Behavior:

- this chat is not included in main session history;
- after closing the modal, its thread may be discarded;
- if needed, modal chat state can live only in frontend memory until the window closes, without DB writes.

## 4. Required changes

## 4.1 Frontend

- Split current `Dashboard` into layout-level shell and independent work panels.
- Remove the hard coupling of main chat to `activeDocumentId`.
- Introduce separate state for:
  - list of main chat sessions;
  - active chat session;
  - main session messages;
  - results pane snapshot;
  - modal contract view state;
  - temporary contract chat.
- Split the left UI into two distinct roles:
  - chat history;
  - results pane / explorer.
- Move document upload out of the “primary left panel” role into a dedicated workspace control:
  - toolbar;
  - upload button;
  - separate import screen/panel;
  - or a block inside the results pane, but not in place of history.
- Add a dedicated contract preview component.
- Add a modal container for the contract-focused workflow.
- Add explicit loading/empty/error states for:
  - session list;
  - agent response;
  - results tree;
  - contract preview.

Recommended component breakdown:

- `DashboardWorkspace.svelte` or an updated `Dashboard.svelte` as orchestration layer;
- `ChatSessionSidebar.svelte`;
- `AgentChatPanel.svelte`;
- `ResultExplorerPanel.svelte`;
- `ResultTreeNode.svelte`;
- `WorkspaceToolbar.svelte`;
- `ContractViewerModal.svelte`;
- `ContractPreviewPane.svelte`;
- `ContractChatPanel.svelte`.

Recommended frontend state:

- Svelte store for list and active main session;
- Svelte store for results tree and explorer UI state;
- local state for modal and temporary contract chat;
- optional `sessionId -> workspace snapshot` map for fast restore without extra requests.

## 4.2 Backend

- Introduce a persistent main manager chat session entity.
- Persist message history for the main chat session.
- Persist a results-pane snapshot bound to the main session, not a single document.
- Extend search orchestration so it returns not only `answer` but structured results for the tree.
- Add APIs to load and restore session history.
- Add API to fetch and/or stream contract file for preview.
- Add a separate endpoint for contract-scoped chat without persistent storage.
- Lay groundwork for grouping results by supplier.

New or extended domain entities:

- `chat_sessions`
  - `id`
  - `owner_id`
  - `title`
  - `created_at`
  - `updated_at`
  - `last_message_at`
- `chat_messages`
  - `id`
  - `session_id`
  - `role`
  - `content`
  - `created_at`
  - optional `metadata`
- `workspace_snapshots`
  - `id`
  - `session_id`
  - `result_tree_json`
  - `selected_node_id`
  - `expanded_node_ids`
  - `view_mode`
  - `updated_at`

To shrink the first iteration, `workspace_snapshots` can be stored as JSON on `chat_sessions`; for growth, keep it separate.

Additional document fields needed for the results tree:

- supplier / counterparty name;
- result entity type;
- path in the tree;
- “contract / folder” flag;
- human-readable title;
- preview link.

If supplier is not extracted reliably yet, as an interim approach:

- start with a flat list of contracts;
- enable supplier grouping in a later iteration;
- or place such contracts in a temporary “No supplier” folder.

## 4.3 API contract

New or revised endpoints:

- `GET /chat-sessions`
  - list of the user’s main chat sessions;
- `POST /chat-sessions`
  - create a new main session;
- `GET /chat-sessions/{id}`
  - load message history and persisted results-pane snapshot;
- `POST /chat-sessions/{id}/messages`
  - send a message to the main session;
  - response should include:
    - assistant message;
    - updated results-tree snapshot;
    - optional `session_title` if auto-generated;
- `PATCH /chat-sessions/{id}/snapshot`
  - persist user state of the left pane if we save it separately from the agent response;
- `GET /documents/{id}/preview`
  - URL, stream, or raw file for contract preview;
- `POST /documents/{id}/chat`
  - chat for a specific contract without writing to history.

Prefer not to grow `POST /chat/` without bounds. Cleaner split:

- main workspace chat;
- contract chat;
- documents and preview.

## 4.4 Search / RAG orchestration

Main chat must return not only plain text but structure for the left pane. That requires:

- extending the search orchestration layer;
- normalizing the result response schema;
- agreeing on a single tree format.

Proposed result node shape:

- `id`
- `type`: `folder | supplier | contract`
- `title`
- `document_id`
- `children`
- `has_children`
- `preview_available`
- `badges`
- `meta`

Main chat command response should include:

- `assistant_message`;
- `result_tree`;
- `session_metadata`;
- `search_metadata`:
  - route;
  - total_matches;
  - grouping_mode.

## 5. Implementation phases

## Phase 1. Lock UX contract and new workspace boundaries

What we do:

- describe final screen composition;
- define what persists in main session history;
- confirm contract chat is not persisted;
- decide where document upload lives in the new layout.

Phase outcome:

- agreed UX flow;
- list of required entities and APIs;
- updated UI-state contract between frontend and backend.

## Phase 2. Backend data model for sessions and workspace snapshots

What we do:

- add models for main chat sessions, messages, and snapshots;
- add CRUD/services for read/write;
- prepare DB migrations if needed;
- plan how to attach supplier metadata to documents or `contract_facts`.

Phase outcome:

- backend can store independent main session history;
- history no longer depends on `document_id`;
- there is a place to persist results-pane state.

## Phase 3. Backend API for the new work scenario

What we do:

- add endpoints for listing, creating, and loading sessions;
- add endpoint to send messages to the main session;
- extend agent response with structured `result_tree`;
- add contract preview endpoint;
- add separate temporary contract-chat endpoint.

Phase outcome:

- frontend gets a stable API contract for the new UX;
- main chat session and contract window become two distinct backend flows.

## Phase 4. Frontend layout and page state refactor

What we do:

- reshape `Dashboard` into a three-zone workspace;
- move chat history into its own left column;
- add a dedicated results pane;
- create stores for sessions, messages, snapshots, and active selection;
- decouple main chat from direct `activeDocumentId` coupling.

Phase outcome:

- main page matches target layout;
- chat history and search results have distinct roles;
- page state is manageable and extensible.

## Phase 5. Main chat and results-pane flow

What we do:

- on send, create or update the main session;
- persist messages and associated results snapshot;
- render results tree as an “explorer”;
- restore pane state when switching sessions;
- add empty/loading/error states.

Phase outcome:

- left history truly stores “this pane,” not only messages;
- users can return to a prior search scenario and continue.

## Phase 6. Contract modal with temporary chat

What we do:

- open contract from results tree in a modal overlay;
- show contract preview on the left;
- open contract-scoped chat on the right;
- do not persist this chat in main session history;
- after close, clear temp state or keep it only until page unload.

Phase outcome:

- separate loop: “view contract + quick chat”;
- main session history is not cluttered with narrow-context threads.

## Phase 7. Testing, stabilization, and migration of the old flow

What we do:

- test new backend entities and APIs;
- verify history/snapshot restore;
- test opening contract from tree;
- check degradation when supplier metadata is missing;
- move old document-upload flow into new layout without losing the feature.

Phase outcome:

- new flow is stable;
- old “upload document → ask question” path does not break main workflow;
- team knows how to migrate existing UI pieces.

## Phase 8. Documentation update

Run this last, after implementation stabilizes.

What we update:

- [docs/plans/prd.md](/Users/2madeira/DEV/PROJECTS/amaterasu/docs/plans/prd.md)
  - document new main-page UX;
  - describe split: session history, results pane, main chat;
  - describe contract modal and non-persisted contract chat;
- [docs/frontend/overview.md](/Users/2madeira/DEV/PROJECTS/amaterasu/docs/frontend/overview.md)
  - reflect new page composition pattern;
- [docs/frontend/state-and-routing.md](/Users/2madeira/DEV/PROJECTS/amaterasu/docs/frontend/state-and-routing.md)
  - document stores and new state model;
- [docs/backend/overview.md](/Users/2madeira/DEV/PROJECTS/amaterasu/docs/backend/overview.md)
  - reflect session and snapshot entities;
- [docs/api/endpoints.md](/Users/2madeira/DEV/PROJECTS/amaterasu/docs/api/endpoints.md)
  - document new endpoints.

Phase outcome:

- product and technical docs match the new behavior;
- PRD reflects the manager’s new workflow.

## 6. Implementation priorities

High priority:

- decouple chat history from a single file;
- implement main session and results-pane snapshot storage;
- split main chat and contract chat;
- ship the new main-page layout.

Medium priority:

- supplier grouping;
- auto-generated session title;
- fine-grained sync of tree UI state between frontend and backend.

Lower priority for v1:

- advanced operations in the file tree;
- persisting temporary contract-chat state across modal opens;
- extended sort/filter modes in the results pane.

## 7. Recommended order of code changes

To avoid breaking the working flow, prefer this order:

1. Backend model and APIs for sessions first.
2. Then new frontend state layer and layout.
3. Then structured results and tree.
4. Then modal contract workflow.
5. Documentation and PRD last.

## 8. Summary

The refactor changes not only main-page appearance but the system’s core interaction model:

- primary unit of work shifts from “document as entry point” to “chat session as work context”;
- search results become a first-class UI entity and backend response;
- contracts get a dedicated temporary view-and-chat mode;
- documentation should be updated only after the new architecture and user scenario are fixed.
