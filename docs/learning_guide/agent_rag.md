# AI & RAG Mechanics

Amaterasu answers questions in the context of **user-uploaded contracts**. The implementation combines **structured extraction**, **relational reporting**, **vector search**, and **LLM generation**—not a single generic “load PDF → chunk → one vector chain” for every answer.

## 1. Why not “just ask the LLM”?

**Theory:** General LLMs do not know your private PDFs and may **hallucinate** if asked without grounded context.

**In this project:** Grounding comes from (a) **validated facts** stored in PostgreSQL, (b) **retrieved passages** from Qdrant after approval, and (c) optional SQL-style reporting over `contract_facts` for quantitative questions. The LLM is invoked where the chosen route needs generation or synthesis—not as the only retrieval mechanism.

## 2. Retrieval-Augmented Generation (RAG) — concept

**Theory:** **Retrieve** relevant content, **augment** the prompt with that content, then **generate** an answer. That reduces reliance on the model’s parametric memory.

**In this project:** “Retrieve” is split across systems: sometimes **vector similarity** in Qdrant (summaries or chunks), sometimes **filtered SQL** over extracted JSON facts, sometimes **both** orchestrated by `search_orchestration`. The legacy module `app/services/rag.py` illustrates a classic LangChain RetrievalQA-style path; **current chat and workspace flows** use [query orchestration](../backend/processes/rag_chat.md) instead.

## 3. Ingestion: from PDF to searchable vectors

**Theory:** Raw files must become text, structured data, and vectors before search works well.

**In this project (high level):**

1. **Upload** stores the PDF and creates document rows in PostgreSQL.
2. **Celery** runs **`process_document`**: PDF → Markdown artifact.
3. **`extract_document_facts`** calls the LLM with schema validation; results land in **`contract_facts`** (versioned).
4. **Human-in-the-loop** (or **trusted bulk** auto-approval when allowed) gates the next step.
5. **`index_document`** builds a **document summary** and **text chunks**, embeds them, and upserts into **two Qdrant collections** (summary vs chunk) with idempotent delete-before-upsert.

Embeddings are created via `app/services/llm.py` (**Hugging Face** locally by default, or **LM Studio** when `EMBEDDINGS_PROVIDER=lmstudio`). Chunking for indexing uses **LangChain’s `RecursiveCharacterTextSplitter`** in `document_indexing.py`.

## 4. Vector embeddings and Qdrant

**Theory:** Embeddings map text to vectors; **nearest-neighbor search** finds semantically similar passages.

**In this project:** **Qdrant** stores vectors for **approved** documents only. Separate collections (configured via env, defaults `contract_summaries` and `contract_chunks`) let the system search at **document summary** level or **fine-grained chunk** level. Payloads include ownership fields so retrieval stays tenant-scoped.

## 5. Query orchestration (chat and workspace)

**Theory:** User questions vary: some need aggregation or filters (**“how many…”**), others need narrative grounding (**“what does clause X say?”**). One retrieval strategy rarely fits all.

**In this project:** **`query_router`** classifies the question. **`sql_search`** runs over extracted facts where appropriate; **`vector_search`** hits Qdrant for summary- or chunk-first retrieval; **`search_orchestration`** combines routes and hands results to **`workspace`** shaping for the main UI. Endpoints: `/api/v1/chat`, `/api/v1/chat-sessions/...`, and contract-scoped `/api/v1/documents/{id}/chat`.

See [Agent overview](../agent/overview.md) and [RAG flow](../agent/rag_flow.md) for diagrams and step-by-step detail.

## 6. Where LangChain appears

**Theory:** LangChain bundles loaders, splitters, vector store adapters, and chains.

**In this project:** LangChain is used **selectively**: HF/OpenAI-compatible wrappers in **`llm.py`**, text splitting in **`document_indexing.py`**, and the **legacy `rag.py`** path with Qdrant vectorstore + RetrievalQA. The **primary** production paths for chat are **orchestration services**, not a single global LangChain chain.
