# AI & RAG Mechanics

The core value of Amaterasu is its ability to "read" user-uploaded documents and answer questions about them. This is achieved through a pattern called Retrieval-Augmented Generation (RAG).

## 1. Large Language Models (LLMs) & Their Limits
**Theory:** LLMs (like GPT-4) are powerful autocomplete engines trained on vast amounts of public internet data. However, they have two major flaws for enterprise use:
1.  **Knowledge Cutoff:** They don't know anything that happened after their training date.
2.  **Private Data:** They do not know about *your* specific, private company documents.

If you ask an LLM about your company's internal HR policy, it will either hallucinate (make up an answer) or say it doesn't know.

## 2. Retrieval-Augmented Generation (RAG)
**Theory:** RAG solves the LLM knowledge problem. Instead of relying on the LLM's internal memory, we provide it with an external brain (your documents). The flow works like this:
1.  **Retrieve:** When a user asks a question, the system searches the uploaded documents for relevant text snippets.
2.  **Augment:** The system takes the user's question AND the relevant text snippets and combines them into a single prompt.
3.  **Generate:** The prompt is sent to the LLM. The LLM reads the snippets and *generates* an answer based strictly on that provided context.

**Project Application:** When a user asks "What is our supplier policy?" in Amaterasu, the backend doesn't just ask the LLM. It searches the database, finds the document paragraphs about supplier policy, and sends a prompt to the LLM: *"Based on these paragraphs [Paragraphs], answer the question: What is our supplier policy?"* Furthermore, Amaterasu is instructed to *summarize* these findings rather than just returning raw document chunks.

## 3. Vector Embeddings and Vector Databases
**Theory:** How do we search documents for "relevant text snippets"? Traditional keyword search fails if the user asks about "vacation" but the document uses the word "PTO".
*   **Embeddings:** We use a special AI model to convert text into arrays of numbers (vectors). Text with similar *meaning* will have vectors that are mathematically close together in space.
*   **Vector Database:** A specialized database designed to store and quickly search these vectors. You provide a question, it converts the question to a vector, and finds the document vectors that are mathematically closest to it.

**Project Application:**
*   Amaterasu uses **Qdrant** as its vector database.
*   When a document is uploaded, it is split into chunks. Each chunk is passed through an embedding model (managed via **LangChain**) to create a vector. These vectors are saved in Qdrant.
*   When a user asks a question, the question is embedded, Qdrant searches for similar vectors, and returns the original text chunks for the Augment step of RAG.

## 4. Orchestration with LangChain
**Theory:** Building a RAG pipeline requires gluing together many parts: loading documents, splitting text, calling embedding APIs, querying vector databases, constructing prompts, and calling LLM APIs. LangChain is a framework that provides pre-built tools and abstractions for all these steps.

**Project Application:** The Amaterasu backend relies heavily on LangChain. It uses LangChain's document loaders to parse PDFs/Text, text splitters to chunk the data, integration with Qdrant for vector storage, and chain abstractions to seamlessly pass the retrieved context into the final LLM prompt.