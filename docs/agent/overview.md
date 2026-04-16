# AI Agent Overview

The AI Agent in this project is built using the **Retrieval-Augmented Generation (RAG)** architecture. It allows users to ask questions about the contents of documents they have uploaded (e.g., contracts) and receive accurate, context-aware answers.

The current backend state is transitional:

* the RAG and contract-chat services still exist;
* phase-1 document upload no longer performs metadata extraction or vector indexing inside the HTTP request;
* the system is being reshaped toward an asynchronous ingestion pipeline backed by PostgreSQL lifecycle tables.

## Technologies Used

* **LangChain:** The core framework used to orchestrate the RAG pipeline. It handles document loading, text splitting, prompt management, and chains.
* **Large Language Models (LLMs):** Used for two primary purposes:
  1. **Information Extraction:** Extracting structured facts from documents as part of the ingestion pipeline.
  2. **Question Answering:** Generating natural language responses to user queries based on retrieved context.
* **Embeddings (Sentence Transformers):** Used to convert text chunks into high-dimensional vector representations, enabling semantic similarity search.
* **Qdrant:** The vector database where document embeddings are stored and queried.

## Core Capabilities

1. **Document Ingestion:** The target pipeline parses uploaded PDFs and produces extracted facts plus indexable content.
2. **Structured Fact Storage:** Extracted facts are intended to be stored in PostgreSQL before any indexing begins.
3. **Semantic Search:** Uses vector embeddings to find the most relevant sections of a document based on a user's question.
4. **Contextual Answering:** Provides answers to questions using *only* the retrieved context, minimizing hallucinations. It includes specific logic for summarizing supplier information if requested.
5. **Tenant Isolation:** Ensures users can only query information from documents they own or have access to, enforced via payload filtering in Qdrant.
