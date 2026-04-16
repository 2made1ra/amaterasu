# Amaterasu Setup & Quick Start Guide

This guide is for developers who want to run Amaterasu locally, verify core flows, and align configuration with how the repo actually behaves (Docker Compose, `uv`, migrations, Celery, and optional LM Studio—including a **separate PC on the same Wi‑Fi** running the model).

## 1. Prerequisites

- **Docker** with Compose plugin (`docker compose`; older installs may use `docker-compose`)
- **uv** — Python package manager ([install](https://github.com/astral-sh/uv))
- **Python 3.12+** (see `backend/pyproject.toml`)
- **Node.js 18+** and **npm**

---

## 2. What runs where (typical dev layout)

| Piece | Role |
|--------|------|
| **Docker** | PostgreSQL, Qdrant, Redis |
| **Backend** (`uvicorn`) | REST API on port **8000** |
| **Celery** (two terminals) | Document pipeline (queues `document-high-priority`, `document-bulk`) |
| **Frontend** (`npm run dev`) | Svelte app on port **3000** (Vite listens on `0.0.0.0`) |
| **LM Studio** (optional) | OpenAI-compatible HTTP API, default **1234** — on **this machine** or **another PC on the same LAN** |

The backend reads settings from the **process environment** (`app/core/config.py`). It does **not** automatically load `backend/.env` at API startup (tests load `.env` via pytest only). If you keep secrets in `backend/.env`, export them, use **direnv**, or paste them into your IDE run configuration before `uvicorn` and Celery.

---

## 3. Infrastructure (PostgreSQL, Qdrant, Redis)

From the **repository root**:

```bash
docker compose up -d
```

This default command starts only the infrastructure services (`db`, `redis`, `qdrant`). The containerized backend is available separately via the `app` profile:

```bash
docker compose --profile app up -d --build
```

Verify:

- PostgreSQL: `localhost:5432` (Compose defaults: user `user`, password `password`, database `app_db`)
- Redis: `localhost:6379`
- Qdrant dashboard: `http://localhost:6333/dashboard`

---

## 4. Backend setup

```bash
cd backend
uv sync
```

**Environment** — set in the shell or tooling (see note above about `.env`). Minimal example for local infrastructure:

```env
DATABASE_URL=postgresql://user:password@localhost/app_db
QDRANT_HOST=localhost
QDRANT_PORT=6333
SECRET_KEY=your_super_secret_key_here
REDIS_URL=redis://localhost:6379/0
```

Apply database migrations (required; tables are not created implicitly in `main.py`):

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

**Celery** — use **two** worker processes (interactive uploads vs bulk):

```bash
uv run celery -A app.worker worker -Q document-high-priority --loglevel=info
```

```bash
uv run celery -A app.worker worker -Q document-bulk --loglevel=info
```

Use the **same** environment for `uvicorn` and **both** workers (especially `LLM_*`, `EMBEDDINGS_*`, `LMSTUDIO_*`), or workers will call different providers than the API.

---

## 5. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:3000`.

The client uses a fixed API base in `frontend/src/lib/api.js` (`http://localhost:8000/api/v1`). That matches a browser on the **same machine** as the backend. If you open the UI from **another device** on the LAN via `http://<your-dev-pc-ip>:3000`, you must point the API base URL at a reachable host (change `baseURL` or introduce a build-time env pattern)—otherwise the browser will call `localhost` on the **client device**, not your dev PC.

---

## 6. Local LLM via LM Studio (same PC or another PC on Wi‑Fi)

Point the backend at LM Studio’s OpenAI-compatible API (`app/services/llm.py`). Details: [LM Studio Setup Guide](./learning_guide/lmstudio_setup.md).

### 6.1 LM Studio on the **same machine** as the backend

1. LM Studio → **Local Server** → load a model → **Start Server**.
2. Example env:

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=<model-id-as-shown-in-LM-Studio>
LMSTUDIO_API_BASE=http://localhost:1234/v1
LMSTUDIO_API_KEY=not-needed
```

Embeddings can stay on Hugging Face (default) or also use LM Studio—see the linked guide.

### 6.2 LM Studio on **another PC** on the same Wi‑Fi (recommended flow)

1. On the **GPU / model PC**: install LM Studio, download a model, start the **Local Server**.
2. Enable **Serve on Local Network** (or equivalent) so the server is reachable from LAN, not only `127.0.0.1`. Official docs: [Serve on Local Network](https://lmstudio.ai/docs/developer/core/server/serve-on-network).
3. Note that machine’s **LAN IPv4** (e.g. `192.168.1.50`) and the **port** (often `1234`). Allow the port in the **firewall** on that OS if connections fail.
4. On the machine where you run **FastAPI + Celery**, set:

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=<same-model-id-as-in-LM-Studio>
LMSTUDIO_API_BASE=http://192.168.1.50:1234/v1
LMSTUDIO_API_KEY=not-needed
```

Replace `192.168.1.50` with the real address. Restart `uvicorn` and **both** Celery workers after changes.

**Sanity check:** from the dev PC, `curl -sS http://192.168.1.50:1234/v1/models` (or open in a browser) should respond if the server is up and the network allows it.

**VPN / multiple interfaces:** If LM Studio shows the wrong “reachable” address (e.g. Tailscale instead of Wi‑Fi), you may still connect via the correct LAN IP if the server listens broadly; if not, adjust LM Studio / OS interface priority or bind options per LM Studio docs and your platform.

### 6.3 Backend in Docker, LM Studio on the host or another PC

The root `docker-compose.yml` includes `extra_hosts: host.docker.internal:host-gateway` for containers. Use:

- LM Studio on **the same host** as Docker: `LMSTUDIO_API_BASE=http://host.docker.internal:1234/v1` (see comment in `docker-compose.yml`).
- LM Studio on **another PC**: use that PC’s **LAN IP**, e.g. `http://192.168.1.50:1234/v1` — **not** `host.docker.internal`.

Pass `LLM_PROVIDER`, `LMSTUDIO_API_BASE`, `LLM_MODEL`, etc. via Compose `environment` or a `.env` file consumed by Compose.

---

## 7. Run the backend with Docker Compose (API + workers + infra)

From the repo root you can bring up PostgreSQL, Qdrant, Redis, the **api** service, and **both** Celery workers by enabling the `app` profile:

```bash
docker compose --profile app up -d --build
```

Configure LLM-related variables the same way as for local `uv`. Then use the frontend against `http://localhost:8000` as usual.

---

## 8. Manual feature verification

### A. Registration & login

1. Open `http://localhost:3000`.
2. Register; the first user becomes **Admin**.
3. Log in.

### B. Upload & human-in-the-loop (HitL)

1. **Upload** a PDF.
2. Status should move through `QUEUED` → parsing → `FACTS_READY` (or `FAILED`) with workers running.
3. Confirm facts → approval → indexing to Qdrant → `INDEXED` when indexing completes.

### C. RAG chat

1. Open **Chat** / assistant for a document.
2. Ask something grounded in the uploaded content. With LM Studio, watch the model PC’s server log for requests.

---

## 9. Troubleshooting

| Symptom | What to check |
|--------|----------------|
| **CORS / API errors** | Backend on **8000**, frontend on **3000**; `baseURL` in `frontend/src/lib/api.js`. |
| **DB errors on startup** | `docker compose` up; `DATABASE_URL` matches Compose credentials; run `uv run alembic upgrade head`. |
| **Qdrant / search** | `http://localhost:6333/dashboard`; `QDRANT_HOST` / `QDRANT_PORT`. |
| **LLM works in API but not in pipeline** | Celery workers missing `LLM_PROVIDER` / `LMSTUDIO_API_BASE`; restart workers with the same env as `uvicorn`. |
| **Connection refused to LM Studio** | Server started; correct port; **Serve on Local Network** if calling from another machine; **firewall** on the model PC; `LMSTUDIO_API_BASE` includes `/v1` if your client expects that base path. |
| **uv** | `uv self update`. |

For deeper backend reference, see [Backend Setup](./backend/setup.md).
