# LM Studio with Amaterasu (learning guide)

This guide is the **short path**: why LM Studio, how to start the server, minimal env vars, and where to read the full reference. It follows the [learning guide README](README.md) idea: enough to be productive, with pointers into the repo.

**Canonical reference (variables, chunking, chat vs embeddings, verification):** [Agent — LM Studio integration](../agent/lm_studio.md).

**Operations (LAN, Docker, two workers):** [Project SETUP § LM Studio networking](../SETUP.md#lm-studio-networking).

---

## Why LM Studio?

1. **Separate process** — GPU and model swaps happen in LM Studio, not inside every Celery worker.
2. **Same API shape as OpenAI** — the backend uses `langchain_openai` with `base_url` → LM Studio (`app/services/llm.py`).
3. **Optional embeddings** — you can route **only** the chat model to LM Studio and keep Hugging Face embeddings locally (default), or send both to LM Studio.

---

## Prerequisites

- LM Studio installed; at least one **chat** model downloaded.
- Backend deps: `uv sync` in `backend/`.
- Infrastructure (Postgres, Redis, Qdrant) running if you exercise the full pipeline — see [Infrastructure](infrastructure.md) and [Backend learning guide](backend.md).

---

## Step 1 — Start the server

1. LM Studio → **Local Server**.
2. Load a **chat** model → **Start Server**.
3. Note the **base URL** (often `http://localhost:1234/v1`). The path must include **`/v1`** where the OpenAI-compatible routes live.

Optional: load a dedicated **embedding** model if you plan `EMBEDDINGS_PROVIDER=lmstudio`.

---

## Step 2 — Minimal environment

Put variables in **`backend/.env`** (or export the same names for workers). Pydantic loads that file when `settings` is imported.

**LLM only (typical first step):**

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=<id-from-GET-/v1/models>
LMSTUDIO_API_BASE=http://localhost:1234/v1
LMSTUDIO_API_KEY=not-needed
```

**Align context and generation with the chat model** (see [chat vs embedding context](../agent/lm_studio.md#lm-studio-chat-vs-embedding-context)):

```env
LLM_CONTEXT_WINDOW=32287
LLM_RESERVED_OUTPUT_TOKENS=4096
LLM_MAX_OUTPUT_TOKENS=4096
LLM_PROMPT_OVERHEAD_TOKENS=1024
```

Use numbers that match **your** chat model’s *Context Length* in LM Studio — not the embedding model’s smaller window.

**Optional — embeddings via LM Studio:**

```env
EMBEDDINGS_PROVIDER=lmstudio
EMBEDDINGS_MODEL=<embedding-model-id>
```

Changing embedding model or vector size usually requires **re-indexing** Qdrant — see the reference doc.

---

## Step 3 — Same env for API and workers

Celery must see **`LLM_PROVIDER=lmstudio`** (and the same `LMSTUDIO_*` / `LLM_*` values) or workers will still use the default Hugging Face LLM path. Restart **uvicorn** and **both** worker queues after edits.

---

## Step 4 — Verify

1. Restart FastAPI; trigger chat or document processing that calls the LLM.
2. LM Studio’s log should show HTTP requests.
3. If the **LLM** still downloads Hugging Face weights, the worker process is missing env — re-check exports / `.env` for Celery.

Automated check (server must be up): `backend/tests/test_lmstudio_llm_availability.py` with `LLM_PROVIDER=lmstudio`.

---

## When something breaks

| Symptom | Where to look |
|--------|----------------|
| Connection refused | Server running; port; `LMSTUDIO_API_BASE` includes `/v1` if required. |
| Wrong model / 404 | `LLM_MODEL` must match LM Studio’s model id. |
| Truncated JSON / fact extraction failed | Raise `LLM_MAX_OUTPUT_TOKENS`; align `LLM_CONTEXT_WINDOW` with chat model — [fact extraction & JSON](../backend/fact-extraction-llm-json-error.md). |
| Workers behave differently from API | Same env for **both** Celery processes and uvicorn. |

---

## See also

| Doc | Role |
|-----|------|
| [Agent LM Studio reference](../agent/lm_studio.md) | Full table, chunking vs `INDEXING_*`, embeddings trade-offs, tests. |
| [Agent setup](../agent/setup.md) | Entry point for agent-side config. |
| [SETUP.md](../SETUP.md) | End-to-end local run, LM Studio on another PC, Docker + `host.docker.internal`. |
| [Backend setup](../backend/setup.md) | `uv`, migrations, worker commands. |
