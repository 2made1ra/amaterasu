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

The backend loads settings through **Pydantic Settings** in [`app/core/config.py`](../backend/app/core/config.py): `env_file` points at **`backend/.env`**, so variables defined there are picked up whenever the app imports `settings` (FastAPI via `uvicorn`, **Celery workers**, and other entrypoints that load the package). Values already set in the **real process environment** override the file.

Keep a local **`backend/.env`** (gitignored) with infrastructure URLs and, if you use HTTP LLMs, LM Studio variables. Optionally export the same file into your shell for tools that do not import the app:

```bash
cd backend
set -a && source .env && set +a   # bash/zsh: export all assignments from .env
```

You can also use **direnv**, paste variables into your IDE run configuration, or export them manually. The **pytest** suite additionally calls `load_dotenv(backend/.env)` in `tests/conftest.py`.

For LM Studio–specific variables (`LLM_PROVIDER`, `LMSTUDIO_API_BASE`, `LLM_MAX_OUTPUT_TOKENS`, etc.), see [Agent — LM Studio integration](./agent/lm_studio.md) and [Fact extraction / JSON errors](./backend/fact-extraction-llm-json-error.md). Quick tutorial: [Learning guide — LM Studio](./learning_guide/lmstudio_setup.md). The full variable list for the API is in [Backend setup](./backend/setup.md).

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

**Environment** — maintain `backend/.env` locally (not committed). The backend reads it automatically via Pydantic (see above). At minimum for local Docker infrastructure:

```env
DATABASE_URL=postgresql://user:password@localhost/app_db
QDRANT_HOST=localhost
QDRANT_PORT=6333
SECRET_KEY=your_super_secret_key_here
REDIS_URL=redis://localhost:6379/0
```

When you use **LM Studio** (`LLM_PROVIDER=lmstudio`), add at least the server URL, model ids, and **token-related** settings so chat completions are not truncated and prompt chunking matches your model:

- **`LMSTUDIO_API_BASE`** — OpenAI-compatible base URL, usually ending in `/v1` (e.g. `http://localhost:1234/v1` or `http://192.168.x.x:1234/v1`).
- **`LLM_MODEL`**, **`FACT_EXTRACTION_MODEL`**, **`SUMMARIZATION_MODEL`** — exact loaded model **id** strings from LM Studio (`GET …/v1/models`). You can point all three at the same chat model or use different ids if you load multiple models.
- **`LLM_CONTEXT_WINDOW`** — context length of your **chat** model as configured in LM Studio; used to compute how much markdown fits in one LLM call before splitting.
- **`LLM_MAX_OUTPUT_TOKENS`** — maximum **new** tokens for chat completions (passed to the API client). Set this to a value compatible with your LM Studio server limit (large enough for structured JSON from fact extraction). Defaults in code are **`2048`**; raise both this and **`LLM_RESERVED_OUTPUT_TOKENS`** if long JSON is truncated.
- **`LLM_RESERVED_OUTPUT_TOKENS`** — reserved slice of the context window when estimating **input** size for chunking (`split_text_for_llm`). Keep it modest relative to `LLM_CONTEXT_WINDOW` so prompts are not split unnecessarily; it is **not** the same as the embedding model’s token limit.

Embedding models use **`EMBEDDINGS_PROVIDER`**, **`EMBEDDINGS_MODEL`**, and indexing chunk sizes (`INDEXING_CHUNK_*`) — separate from chat `max_tokens`. Do not confuse a small embedding context (e.g. 2048 tokens) with **`LLM_CONTEXT_WINDOW`** for the chat model.

**Chat vs embedding context in LM Studio** (typical dual-model setup): table and example `.env` — [Agent LM Studio — chat vs embeddings](./agent/lm_studio.md#lm-studio-chat-vs-embedding-context).

See [Agent — LM Studio integration](./agent/lm_studio.md). Set `LLM_MODEL` (and siblings) to the exact model id from LM Studio (`GET …/v1/models`).

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

<a id="lm-studio-networking"></a>

## 6. Local LLM via LM Studio (same PC or another PC on Wi‑Fi)

Point the backend at LM Studio’s OpenAI-compatible API (`app/services/llm.py`). **Reference:** [Agent — LM Studio integration](./agent/lm_studio.md). **Tutorial:** [Learning guide — LM Studio](./learning_guide/lmstudio_setup.md).

### 6.1 LM Studio on the **same machine** as the backend

1. LM Studio → **Local Server** → load a model → **Start Server**.
2. Example `backend/.env` snippet (adjust ids and numbers to your loaded models and server):

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=<chat-model-id-as-shown-in-LM-Studio>
FACT_EXTRACTION_MODEL=<chat-model-id>
SUMMARIZATION_MODEL=<chat-model-id>
LMSTUDIO_API_BASE=http://localhost:1234/v1
LMSTUDIO_API_KEY=not-needed

# Align with your chat model in LM Studio (context / generation limits)
LLM_CONTEXT_WINDOW=8192
LLM_MAX_OUTPUT_TOKENS=4096
LLM_RESERVED_OUTPUT_TOKENS=2048
```

Embeddings can stay on Hugging Face (default) or also use LM Studio—see the linked guide. If both chat and embeddings run in LM Studio, keep **separate** model ids and remember embedding models often have a **smaller** input window than chat models; that limit does **not** replace `LLM_MAX_OUTPUT_TOKENS` for chat.

### 6.2 LM Studio on **another PC** on the same Wi‑Fi (recommended flow)

1. On the **GPU / model PC**: install LM Studio, download a model, start the **Local Server**.
2. Enable **Serve on Local Network** (or equivalent) so the server is reachable from LAN, not only `127.0.0.1`. Official docs: [Serve on Local Network](https://lmstudio.ai/docs/developer/core/server/serve-on-network).
3. Note that machine’s **LAN IPv4** (e.g. `192.168.1.50`) and the **port** (often `1234`). Allow the port in the **firewall** on that OS if connections fail.
4. On the machine where you run **FastAPI + Celery**, set (same pattern as §6.1; only `LMSTUDIO_API_BASE` changes to the LAN URL):

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=<same-model-id-as-in-LM-Studio>
FACT_EXTRACTION_MODEL=<same-model-id-as-in-LM-Studio>
SUMMARIZATION_MODEL=<same-model-id-as-in-LM-Studio>
LMSTUDIO_API_BASE=http://192.168.1.50:1234/v1
LMSTUDIO_API_KEY=not-needed
LLM_CONTEXT_WINDOW=8192
LLM_MAX_OUTPUT_TOKENS=4096
LLM_RESERVED_OUTPUT_TOKENS=2048
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
| **Document processing failed: LLM response was not valid JSON** / truncated JSON | Raise **`LLM_MAX_OUTPUT_TOKENS`** (and server-side max tokens in LM Studio) so the model can finish the JSON; align **`LLM_CONTEXT_WINDOW`** with the chat model. See [fact-extraction-llm-json-error](./backend/fact-extraction-llm-json-error.md). |
| **Connection refused to LM Studio** | Server started; correct port; **Serve on Local Network** if calling from another machine; **firewall** on the model PC; `LMSTUDIO_API_BASE` includes `/v1` if your client expects that base path. |
| **uv** | `uv self update`. |

For deeper backend reference, see [Backend Setup](./backend/setup.md).
