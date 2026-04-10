# AI Agent Overview

The AI Agent in this project is built using the **Retrieval-Augmented Generation (RAG)** architecture. It allows users to ask questions about the contents of documents they have uploaded (e.g., contracts) and receive accurate, context-aware answers.

## Technologies Used

* **LangChain:** The core framework used to orchestrate the RAG pipeline. It handles document loading, text splitting, prompt management, and chains.
* **Large Language Models (LLMs):** Used for two primary purposes:
  1. **Information Extraction:** Extracting metadata (like contract deadlines) from documents during the upload phase.
  2. **Question Answering:** Generating natural language responses to user queries based on retrieved context.
* **Embeddings (Sentence Transformers):** Used to convert text chunks into high-dimensional vector representations, enabling semantic similarity search.
* **Qdrant:** The vector database where document embeddings are stored and queried.

## Core Capabilities

1. **Document Ingestion:** Parses uploaded PDF documents and splits them into manageable chunks.
2. **Metadata Extraction:** Automatically extracts key metadata (e.g., dates) from the text upon upload.
3. **Semantic Search:** Uses vector embeddings to find the most relevant sections of a document based on a user's question.
4. **Contextual Answering:** Provides answers to questions using *only* the retrieved context, minimizing hallucinations. It includes specific logic for summarizing supplier information if requested.
5. **Tenant Isolation:** Ensures users can only query information from documents they own or have access to, enforced via payload filtering in Qdrant.
