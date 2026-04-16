# Using LM Studio with Amaterasu

This guide explains how to point the Amaterasu backend at [LM Studio](https://lmstudio.ai/)’s **OpenAI-compatible** HTTP API so chat and/or embeddings can run in LM Studio instead of loading Hugging Face models inside the Python process.

## Why use LM Studio?

1. **Separate process** — Often better GPU utilization and simpler model switching than embedding large transformers directly in the API worker.
2. **Model choice** — Swap models in LM Studio without changing application code beyond env vars.
3. **OpenAI-compatible API** — The backend uses `langchain_openai` clients with `base_url` pointed at LM Studio (`app/services/llm.py`).

## Prerequisites

- LM Studio installed; a model downloaded; **local server** started.
- Backend dependencies installed (`uv sync` in `backend/`).

## Step 1: Start LM Studio server

1. Open LM Studio → **Local Server** (sidebar).
2. Pick a model and click **Start Server**.
3. Note the **Base URL** (commonly `http://localhost:1234/v1`) and port.

## Step 2: Environment variables

Configure the process environment (shell, IDE, or deployment). Settings are read in `app/core/config.py`; the API does not auto-load `.env` on startup (tests load `.env` via pytest).

### LLM (text generation)

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=<model-id-as-shown-in-LM-Studio>
LMSTUDIO_API_BASE=http://localhost:1234/v1
LMSTUDIO_API_KEY=not-needed
```

`LMSTUDIO_API_KEY` defaults to a placeholder; set a real value if your server requires it.

### Embeddings (optional)

You can keep **Hugging Face** embeddings (default) and only use LM Studio for the LLM—often a good balance.

To route embeddings through LM Studio (if your loaded model supports embedding endpoints):

```env
EMBEDDINGS_PROVIDER=lmstudio
EMBEDDINGS_MODEL=<embedding-model-id>
LMSTUDIO_API_BASE=http://localhost:1234/v1
```

Leave `EMBEDDINGS_PROVIDER` unset or `huggingface` to use **sentence-transformers** locally for vectors.

## Step 3: Verify

1. Restart the FastAPI process after changing env vars.
2. Trigger a flow that calls the LLM (e.g. fact extraction or chat). LM Studio’s log view should show incoming requests.
3. If you still see Hugging Face download logs for the **LLM**, check that `LLM_PROVIDER=lmstudio` is actually visible to the running process (`print(settings.LLM_PROVIDER)` in a pinch).

## Troubleshooting

- **Connection refused** — Server not started or wrong port; `LMSTUDIO_API_BASE` must match LM Studio (including `/v1` if required).
- **Wrong model** — `LLM_MODEL` / `EMBEDDINGS_MODEL` should match what LM Studio expects for the loaded stack.
- **Slow responses** — Confirm GPU acceleration in LM Studio; reduce model size or concurrency.

For broader LLM/Qdrant configuration, see [Agent Setup](../agent/setup.md) and [Backend Setup](../backend/setup.md).
