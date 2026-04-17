# Fact extraction error: “LLM response was not valid JSON”

This note records why the PDF processing pipeline fails (Celery task `extract_document_facts`), how it surfaces in the UI (“Processing Error”), and what to do about it. Incident date: 2026-04-17.

---

## What went wrong

After LM Studio responds, the backend **does not receive a valid JSON object** that can be parsed in `fact_extraction._extract_json_payload()`. That raises `FactExtractionValidationError("LLM response was not valid JSON")`, the document moves to **FAILED**, and the user sees a modal with the same message.

Technically the failure comes from `json.loads()` as `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

Important: in Python, **“(char 0)”** does not only mean an empty string; it also applies when **the first character is not valid JSON** (for example the model outputs noise like `OM`, or plain text before the JSON block).

---

## Symptoms

### In the UI

- A **Processing Error** modal for the uploaded PDF.
- Message: **Document processing failed: LLM response was not valid JSON**.
- PDF parsing to markdown may succeed; the failure happens during **LLM fact extraction**.

### In Celery logs

- `process_document` completes and enqueues `extract_document_facts`.
- API call: `POST http://<host>:1234/v1/completions` with **HTTP 200**.
- Then: `document_fact_extraction_validation_error`, `extraction_run_failed`, `error_source=llm_validation`, transition `PARSING` → `FAILED`.

### In LM Studio logs (same request)

The model server really runs a completion and may log, for example:

- `[LM STUDIO SERVER] Running completion on text: Extract structured busine...`
- Model: `google/gemma-4-e4b` (or whatever you have loaded).
- In the API response, `choices[0].text` shows:
  - a prefix before JSON, e.g. `OM`, then separators and an opening markdown block labeled `json`;
  - **`finish_reason`: `"length"`**;
  - **`completion_tokens`: 256** (or another tight cap);
  - JSON **cuts off** mid-object (e.g. on `"summary"`), with **no closing** markdown fence.

So HTTP looks “fine”, but the **body is not complete JSON** and often **does not match** what the backend parser expects.

---

## Root cause (step by step)

### 1. Completions API and the LangChain wrapper

In `app/services/llm.py`, when `LLM_PROVIDER=lmstudio`, the code uses `langchain_openai.OpenAI`, which hits **`/v1/completions`**. LM Studio supports that, but many models are tuned for **chat** (`/v1/chat/completions`); generation limits are controlled by request parameters.

### 2. Output length limit (main factor in LM Studio logs)

If the API request allows **too few output tokens** (many clients default to something like **256**), the model:

- emits a prefix and the start of JSON;
- **does not** finish the object and/or the markdown fence (triple backticks + `json`);
- returns **`finish_reason: "length"`** — stopped by the cap.

### 3. JSON parsing on the backend

In `fact_extraction.py`, `_extract_json_payload()`:

1. Looks for a fenced block with regex `JSON_BLOCK_PATTERN` (opening tag `json` and closing triple backticks).
2. If there is **no closing** part (truncated reply), there is **no match**, and **`json.loads` receives the entire response string**.
3. The string does not start with `{`/`[` but with arbitrary text (`OM`, spaces, `***`, etc.) → **`JSONDecodeError` at position 0** — matching the stack trace.

Even when the regex matches, **truncated** JSON inside the fence still fails later — but the LM Studio log pattern is usually **no closing fence** because of the token limit.

### 4. Why the UI matches the backend

The same validation surfaces the error; a screenshot from **localhost:3000** around **~03:14** lines up with worker logs around **~03:13:54**.

---

## Recommended fixes

Prioritized: first stop truncation, then harden parsing.

### A. Raise the output token limit (required for large JSON)

- In **LM Studio** (Server / model), increase **max tokens** for completions so the full JSON for your fields fits (for a rich fact schema, often **512–2048+** depending on model and document).
- If only the client sets the cap, pass a higher **`max_tokens`** from code (see `OpenAI` / `ChatOpenAI` in LangChain) and align with `LLM_RESERVED_OUTPUT_TOKENS` in `app/core/config.py` (the reserve avoids filling the whole context with input but **must leave room for the answer**).

### B. Use Chat Completions with LM Studio (often better for instruct models)

- Replace `OpenAI` with **`ChatOpenAI`** using the same `base_url` and model so calls go to **`/v1/chat/completions`**.
- Send the prompt as a user message (and optionally a system message such as “reply with JSON only”). That reduces junk prefixes and matches how models are typically used in LM Studio.

### C. Harden JSON extraction in code (optional)

- Find the first `{` and parse **brace balance** through the matching `}` (careful with strings inside JSON).
- On truncation, surface a clear error (“model output truncated by token limit”) instead of a generic “not valid JSON”.
- Optionally retry with smaller input (chunking already exists) or ask for shorter fields.

### D. Environment parity

- The **Celery worker** must use the same `LLM_PROVIDER`, `LMSTUDIO_API_BASE`, and `FACT_EXTRACTION_MODEL` as the API — otherwise behavior diverges across processes.

---

## Short summary

| Observation | Interpretation |
|-------------|----------------|
| HTTP 200 from LM Studio | Network and server are fine; the issue is **completion content**. |
| `finish_reason: "length"`, ~256 completion tokens | Output **truncated**; JSON and markdown fence often **incomplete**. |
| Prefix before the fenced JSON block | Regex does not capture a block → full string goes to `json.loads` → error at **(char 0)**. |
| UI: “not valid JSON” | Same validation failure shown to the user. |

First step: **increase generation token limit** and, if needed, switch to the **chat** endpoint; second: **improve the parser** for truncated/non-fenced replies and error messages.
