# The RAG Pipeline Flow

This document details the step-by-step process of how the Retrieval-Augmented Generation (RAG) agent works, from document ingestion to answering user queries. The core logic resides in `backend/app/services/rag.py`.

## 1. Document Ingestion Phase

When a user uploads a document (e.g., a PDF), the following sequence occurs:

1. **Loading:** The `PyPDFLoader` from LangChain reads the PDF file and converts it into raw text documents.
2. **Splitting:** The `RecursiveCharacterTextSplitter` breaks the large document down into smaller chunks (e.g., chunks of 1000 characters with an overlap of 200 characters). This ensures that context isn't lost at the boundaries of chunks and that chunks fit within the LLM's context window.
3. **Metadata Extraction:** The `extract_metadata_from_text` function sends a sample of the text to the LLM to proactively extract metadata. For example, it prompts the LLM to find and return a "deadline date" formatted as `YYYY-MM-DD`. This metadata is then presented to the user for review (Human-in-the-Loop) before the document is finalized.
4. **Vectorization & Storage:**
   - The `save_to_vectorstore` function takes the text chunks.
   - It injects critical metadata into every chunk: `document_id` and `owner_id`. This is vital for **Tenant Isolation**.
   - The chunks are converted into vector embeddings.
   - The embeddings and their associated metadata payloads are stored in the **Qdrant** vector database in the `contracts` collection.

## 2. Querying Phase

When a user asks a question in the chat interface:

1. **Filtering (Tenant Isolation):** The `query_rag` function receives the query, the `owner_id`, and an optional `document_id`. It constructs a `models.Filter` for Qdrant.
   - It *must* match the `metadata.owner_id` (ensuring the user only searches their own documents).
   - It *may* match a specific `metadata.document_id` if the user is querying a single document.
2. **Retrieval:** The user's query is converted into a vector embedding. Qdrant performs a similarity search against the database, applying the filter, and retrieves the most semantically relevant text chunks.
3. **Prompt Construction:** The retrieved chunks (the "Context") and the user's question are injected into a LangChain `PromptTemplate`.
   - **Special Instruction:** The prompt explicitly instructs the LLM: *"If searching for suppliers/contractors, provide a summary of the found suppliers based on the context."* This ensures the agent returns synthesized information rather than just raw chunks.
4. **Generation:** The `RetrievalQA` chain sends the constructed prompt to the LLM.
5. **Response:** The LLM generates an answer based *only* on the provided context, and the backend returns this string to the user.
