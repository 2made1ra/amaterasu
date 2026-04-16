# Query Orchestration

This document describes the current search orchestration used by the chat endpoints.

## Description
The backend no longer sends every query through a single vector-search path. Instead, `app/services/query_router.py` classifies each request into one of five route types:

* `SQL_ONLY`
* `SUMMARY_ONLY`
* `SUMMARY_THEN_CHUNKS`
* `CHUNKS_ONLY`
* `HYBRID_SQL_AND_CHUNKS`

The router also extracts structured filters such as `year`, `supplier`, and ISO date ranges. The selected route then drives either PostgreSQL fact search, summary-first Qdrant search, chunk-scoped retrieval, or a hybrid SQL-plus-chunk answer.

The current `/api/v1/chat` and workspace chat flows both call the orchestration layer in `app/services/search_orchestration.py`. The legacy `rag.py` module still exists for backwards compatibility and reference, but it is no longer the primary chat path.

## Routing Summary

* `SQL_ONLY`: used for list, report, and structured reporting queries.
* `SUMMARY_ONLY`: used for discovery and broad topic-search queries.
* `SUMMARY_THEN_CHUNKS`: used for explanation-style questions that need document discovery first and evidence second.
* `CHUNKS_ONLY`: used for contract-scoped or exact-passage queries.
* `HYBRID_SQL_AND_CHUNKS`: used when a query mixes structured constraints with explanatory intent.

## Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant API as Chat API
    participant Router as Query Router
    participant SQL as SQL Search
    participant Vector as Qdrant Search
    participant DB as PostgreSQL

    User->>API: POST /api/v1/chat
    API->>Router: Classify query + extract filters
    alt SQL_ONLY
        Router->>SQL: Search contract_facts with filters
        SQL->>DB: Read approved document facts
        DB-->>SQL: Matching rows
        SQL-->>API: Structured answer
    else SUMMARY_ONLY
        Router->>Vector: Search contract_summaries
        Vector-->>API: Ranked document summaries
    else SUMMARY_THEN_CHUNKS
        Router->>Vector: Search contract_summaries
        Vector-->>API: Top documents
        API->>Vector: Search contract_chunks with top-3 document filter
        Vector-->>API: Evidence snippets
    else CHUNKS_ONLY
        Router->>Vector: Search contract_chunks with document filter
        Vector-->>API: Evidence snippets
    else HYBRID_SQL_AND_CHUNKS
        Router->>SQL: Search contract_facts with filters
        SQL->>DB: Read structured matches
        DB-->>SQL: Matching rows
        API->>Vector: Search contract_chunks within matched documents
        Vector-->>API: Evidence snippets
    end
    API-->>User: Answer JSON
```
