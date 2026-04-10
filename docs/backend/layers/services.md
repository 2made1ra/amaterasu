# Services Layer (`app/services`)

## Purpose
The Services layer contains the core business logic of the application. It acts as an orchestrator for complex operations that involve multiple domains, external APIs, or specialized processing, keeping the API layer thin and focused solely on HTTP concerns.

## Internal Structure
- **`llm.py`**: Handles integration with Large Language Models (e.g., OpenAI). Contains logic for prompting, parsing responses, and extracting metadata from text.
- **`rag.py`**: Implements the Retrieval-Augmented Generation (RAG) pipeline. This involves taking a user query, searching the vector database (Qdrant) for relevant document chunks, and using an LLM to generate a summarized, coherent response based on those chunks.

## Interactions
- **Consumes from `crud`**: May read or update database records as part of a complex workflow.
- **Consumes from `core`**: Uses configuration for API keys and external service URLs.
- **Used by `api`**: API endpoints call service functions to execute complex tasks (e.g., processing an uploaded document or asking a question to the RAG agent).
