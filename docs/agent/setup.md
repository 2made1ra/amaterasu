# Agent setup & environment

This page summarizes how the **AI / RAG** side of the backend is configured. Operational steps (Docker, `uv`, migrations, workers) live in [Backend setup](../backend/setup.md) and [Project SETUP](../SETUP.md).

## LLM and embeddings

- **Implementation:** [`app/services/llm.py`](../../backend/app/services/llm.py) — `get_llm()`, `get_embeddings()`, context budget helpers.
- **Configuration:** [`app/core/config.py`](../../backend/app/core/config.py) — `LLM_PROVIDER`, `EMBEDDINGS_PROVIDER`, LM Studio URLs, token limits, Qdrant-related defaults.

**LM Studio (OpenAI-compatible local server):** full variable table, chat vs embedding context, chunking behavior, and verification — **[LM Studio integration (reference)](lm_studio.md)**.

**Quick path for learners:** [Learning guide: LM Studio](../learning_guide/lmstudio_setup.md).

**Fact extraction returns invalid JSON:** [Fact extraction & LLM JSON errors](../backend/fact-extraction-llm-json-error.md).

## Qdrant

Vector collections for summaries and chunks are configured with `QDRANT_*` variables (see `config.py`). Qdrant runs via Docker Compose; workers and API must reach the same host/port as in `.env`.

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

From the repo root:

```bash
docker compose up -d qdrant
```

REST API and dashboard: port **6333** (see [Infrastructure learning guide](../learning_guide/infrastructure.md)).

## Embeddings note

By default the backend can use **Hugging Face** / `sentence-transformers` for embeddings while only the **chat** model uses LM Studio. You can also set `EMBEDDINGS_PROVIDER=lmstudio`; changing embedding model or dimension usually implies **re-indexing** — details in [LM Studio reference](lm_studio.md#lm-studio-embeddings-choice).
