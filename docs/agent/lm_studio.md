# LM Studio integration (reference)

Use this document when configuring the **generative LLM** (and optionally **embeddings**) to call [LM Studio](https://lmstudio.ai/) over its **OpenAI-compatible HTTP API** instead of loading Hugging Face models inside the API/Celery process.

**Code:** provider switch is env-driven — [`app/core/config.py`](../../backend/app/core/config.py) and [`app/services/llm.py`](../../backend/app/services/llm.py).

**Tutorial / first-time setup:** [Learning guide: LM Studio](../learning_guide/lmstudio_setup.md).

---

## 1. Environment variables

| Variable | LM Studio value | Notes |
|----------|-----------------|--------|
| `LLM_PROVIDER` | `lmstudio` | Uses HTTP client to LM Studio instead of local `transformers` pipeline. |
| `LMSTUDIO_API_BASE` | `http://localhost:1234/v1` (or your URL) | Must end with **`/v1`** like OpenAI’s base URL. |
| `LMSTUDIO_API_KEY` | `not-needed` or server key | Default placeholder if LM Studio auth is off. |
| `LLM_MODEL` | Model id **as in LM Studio** | Must match loaded model / `GET …/v1/models` — not necessarily a Hugging Face repo id. |
| `FACT_EXTRACTION_MODEL` | Usually same as `LLM_MODEL` | Fact extraction from markdown. |
| `SUMMARIZATION_MODEL` | Usually same as `LLM_MODEL` | Retrieval summaries during indexing. |
| `LLM_CONTEXT_WINDOW` | Same as **Context Length** of the **chat** model in LM Studio (e.g. `32287`) | Drives input budget and chunking for chat paths. **Do not** set this to the embedding model’s limit (often 2048). See [§4](#lm-studio-chat-vs-embedding-context). |
| `LLM_RESERVED_OUTPUT_TOKENS` | e.g. `2048` or `4096` | Reserved **output** tokens when estimating how much **input** fits before splitting. |
| `LLM_MAX_OUTPUT_TOKENS` | e.g. `2048` or `4096` | `max_tokens` for chat completions; raise if long JSON (fact extraction) is truncated. |
| `LLM_PROMPT_OVERHEAD_TOKENS` | e.g. `1024` | Reserve for system prompt, schema, metadata in input budget math. |

---

## 2. Where to set variables

- **FastAPI** (`uvicorn`) and **Celery workers** must see the **same** values. If workers omit `LLM_PROVIDER=lmstudio`, they fall back to the default Hugging Face path.
- Prefer `backend/.env`: Pydantic `Settings` uses `env_file` pointing at that file when the app imports `settings` (see `app/core/config.py`).

Example worker session (after env is loaded):

```bash
export LLM_PROVIDER=lmstudio
export LMSTUDIO_API_BASE=http://localhost:1234/v1
export LLM_MODEL=google/gemma-4-e4b
export FACT_EXTRACTION_MODEL=google/gemma-4-e4b
export SUMMARIZATION_MODEL=google/gemma-4-e4b
export EMBEDDINGS_PROVIDER=lmstudio
export EMBEDDINGS_MODEL=text-embedding-nomic-embed-text-v1.5
export LLM_CONTEXT_WINDOW=32287
export LLM_RESERVED_OUTPUT_TOKENS=4096
export LLM_MAX_OUTPUT_TOKENS=4096
export QDRANT_AUTO_DETECT_VECTOR_SIZE=true
uv run celery -A app.worker worker -Q document-high-priority --loglevel=info
```

`EMBEDDINGS_MODEL` must be the **embedding** model id in LM Studio, not the chat model id (see [§4](#lm-studio-chat-vs-embedding-context)).

---

## 3. LM Studio preparation

1. Install LM Studio; download models; start **Local Server** (default port 1234).
2. Load a **chat** model for generation; optionally a separate **embedding** model.
3. Confirm `GET …/v1/models` lists the ids you put in `LLM_MODEL` / `EMBEDDINGS_MODEL`.

No repo code changes are required beyond env.

<a id="lm-studio-chat-vs-embedding-context"></a>

## 4. Two context limits: chat vs embeddings

LM Studio often runs **two** models with **different** context sizes:

| In LM Studio UI | Typical role | Set in `.env` |
|-------------------|--------------|----------------|
| **Chat** model — *Context Length* (e.g. 32k, 131k max for some weights) | Chat, fact extraction, summarization | **`LLM_CONTEXT_WINDOW`** = same number as the slider for that chat model. Update when you change the slider. |
| **Embedding** model (e.g. Nomic **2048** tokens) | Vectors for Qdrant | **`EMBEDDINGS_MODEL`** = model id. The **2048** limit applies to the embedder only; **do not** copy it into `LLM_CONTEXT_WINDOW`. |

**Why:** `LLM_CONTEXT_WINDOW` only feeds `estimate_llm_input_char_budget()` in `app/services/llm.py` for **chat**-side chunking. Embeddings use `get_embeddings()` separately.

**Input budget formula:**  
`LLM_CONTEXT_WINDOW - LLM_RESERVED_OUTPUT_TOKENS - LLM_PROMPT_OVERHEAD_TOKENS` → approximate character budget for splitting.

**Example** (chat Gemma at **32287**, Nomic embed **2048** for reference only):

```env
LLM_CONTEXT_WINDOW=32287
LLM_RESERVED_OUTPUT_TOKENS=4096
LLM_PROMPT_OVERHEAD_TOKENS=1024
LLM_MAX_OUTPUT_TOKENS=4096
```

- Short answers: `2048` for reserved + max output is fine.
- Large structured JSON: try `4096` or `8192` if the server/model allows.

**Avoid** empty integer env values (`VAR=`) — either set a number or omit the key so defaults in `config.py` apply.

---

## 5. Chunking vs model context

Switching to LM Studio does not remove context limits; the backend accounts for them on long documents:

- **Fact extraction** splits markdown to fit the budget, then merges partial JSON.
- **Summarization** uses map-reduce: chunk summaries, then a final summary.

Implementation touchpoints: `app/services/llm.py` (splitter), `app/services/fact_extraction.py`, `app/services/document_indexing.py`.

**Not** LLM chunking: `INDEXING_CHUNK_SIZE` / `INDEXING_CHUNK_OVERLAP` control **Qdrant indexing** chunking, not the LLM prompt chunks for fact extraction.

<a id="lm-studio-embeddings-choice"></a>

## 6. Embeddings: local Hugging Face vs LM Studio

- **Default:** `EMBEDDINGS_PROVIDER` unset or `huggingface` — often enough to move **only** the generative LLM to LM Studio (`LLM_PROVIDER=lmstudio`).
- **`EMBEDDINGS_PROVIDER=lmstudio`:** `OpenAIEmbeddings` with the same `LMSTUDIO_API_BASE`. Useful to centralize GPU work in LM Studio or use a specific embedding model there.

**Risks when changing embedding model:** vector dimension must match `QDRANT_VECTOR_SIZE` and existing Qdrant collections — often requires **re-indexing** or new collections. `QDRANT_AUTO_DETECT_VECTOR_SIZE=true` helps when creating collections if size is unknown.

| Goal | Suggestion |
|------|------------|
| Only offload generative LLM (avoid local HF LLM in worker) | `LLM_PROVIDER=lmstudio`, keep **`EMBEDDINGS_PROVIDER=huggingface`**. |
| Chat + embeddings both via LM Studio | `EMBEDDINGS_PROVIDER=lmstudio`, set **`EMBEDDINGS_MODEL`** to the embedding model id; align Qdrant dimension. |

---

## 7. Verification

- Test (requires running LM Studio): `backend/tests/test_lmstudio_llm_availability.py` with `LLM_PROVIDER=lmstudio`.
- After changes: restart API and **both** Celery queues; upload a document with fact extraction and confirm no HF weight download for the **LLM** path and successful LM Studio responses.

**Truncated JSON / fact extraction errors:** [Fact extraction & LLM JSON errors](../backend/fact-extraction-llm-json-error.md).

**LAN / another PC / Docker:** [SETUP.md — LM Studio networking](../SETUP.md#lm-studio-networking).
