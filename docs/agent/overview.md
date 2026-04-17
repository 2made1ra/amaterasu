# AI Agent Overview

The agent-facing backend is now organized around query orchestration rather than a single monolithic RAG path. It still answers questions about uploaded contracts, but the answer path is selected explicitly:

* structured questions can go to PostgreSQL-backed SQL search;
* broad discovery questions can go to summary vectors;
* explanation-style questions can use summary-first retrieval followed by chunk search;
* contract-scoped questions can be narrowed to the selected document.

The ingestion backbone remains the same:

* upload requests dispatch asynchronous PDF parsing and fact extraction through Celery workers;
* PostgreSQL lifecycle tables (`documents`, `contract_facts`, `extraction_runs`) store the document state and extracted facts;
* approved documents are indexed into separate Qdrant summary and chunk collections.

## Technologies Used

* **LangChain:** The core framework used for document loading, text splitting, prompt management, and generation helpers.
* **LM Studio (optional):** The backend can use an OpenAI-compatible local server instead of loading generative models inside the worker process — see [LM Studio integration](lm_studio.md).
* **Large Language Models (LLMs):** Used for two primary purposes:
  1. **Information Extraction:** Extracting structured facts from documents as part of the ingestion pipeline.
  2. **Question Answering:** Generating natural language responses to user queries based on retrieved context.
* **Embeddings (Sentence Transformers):** Used to convert text into high-dimensional vector representations, enabling semantic similarity search.
* **Qdrant:** The vector database where summary and chunk embeddings are stored and queried.

## Core Capabilities

1. **Document Ingestion:** The target pipeline parses uploaded PDFs and produces extracted facts plus indexable content.
2. **Structured Fact Storage:** Extracted facts are intended to be stored in PostgreSQL before any indexing begins.
3. **Semantic Search:** Uses vector embeddings to find the most relevant sections of a document based on a user's question.
4. **Contextual Answering:** Provides answers using the route selected by the query router, keeping SQL reporting and vector retrieval separate.
5. **Tenant Isolation:** Ensures users can only query information from documents they own or have access to, enforced in both SQL filters and Qdrant payload filtering.
