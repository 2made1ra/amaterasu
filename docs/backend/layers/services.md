# Services Layer (`app/services`)

## Purpose
The Services layer contains the core business logic of the application. It acts as an orchestrator for complex operations that involve multiple domains, external APIs, or specialized processing, keeping the API layer thin and focused solely on HTTP concerns.

## Internal Structure
- **`llm.py`**: Handles integration with Large Language Models (e.g., OpenAI). Contains logic for prompting, parsing responses, and extracting metadata from text.
- **`query_router.py`**: Classifies user questions into explicit route types and extracts structured filters for SQL-backed search.
- **`sql_search.py`**: Runs filtered `contract_facts` queries for reporting-style questions.
- **`vector_search.py`**: Performs summary-first and chunk-scoped Qdrant retrieval.
- **`search_orchestration.py`**: Chooses the route and assembles the response used by chat and workspace flows.
- **`rag.py`**: Legacy RAG implementation kept for backwards compatibility and reference, but no longer the primary chat path.
- **`workspace.py`**: Shapes assistant responses and result explorer payloads for the main workspace UI.
- **`document_parser.py`**: Parses uploaded PDFs into Markdown artifacts for worker-side extraction.
- **`fact_extraction.py`**: Builds extraction prompts, validates LLM JSON with Pydantic, and returns structured fact payloads.
- **`document_indexing.py`**: Builds summaries and chunk splits used by the approved-document indexing task.
- **`qdrant_index.py`**: Manages Qdrant collection setup and idempotent delete-before-upsert indexing.
- **`bulk_ingestion.py`**: Controlled bulk-import CLI/service logic that splits inputs into batches and uploads files one-by-one through the API contract.

## Interactions
- **Consumes from `crud`**: May read or update database records as part of a complex workflow.
- **Consumes from `core`**: Uses configuration for API keys and external service URLs.
- **Used by `api`**: API endpoints call service functions for workspace, contract chat, query routing, SQL reporting, and vector retrieval behavior.
- **Used by `tasks`**: Celery tasks call parser/extraction services to process documents asynchronously.
