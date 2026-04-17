# Building Amaterasu: The Learning Guide

Welcome to the Amaterasu Learning Guide. It explains the ideas behind a full-stack AI assistant with document ingestion, human review, and query-routed search—aligned with how the repository is structured today.

The guide follows the Pareto principle (80/20): enough theory to understand the system, plus pointers to where behavior is implemented in code and in the main `docs/` tree.

## Core pillars

Building this project means wiring four areas together:

1. **Backend (API & persistence):** FastAPI, PostgreSQL, JWT, Alembic migrations, and an asynchronous document pipeline (Celery + Redis) for parsing, fact extraction, and vector indexing.
2. **Frontend (SPA):** A Svelte + Vite + Tailwind SPA that talks to `/api/v1`, keeps auth tokens, and uses a small client-side router built on the History API.
3. **AI & retrieval:** Not only classic “chunk RAG”: structured facts in PostgreSQL, dual Qdrant collections (summaries and chunks), and **query orchestration** that routes questions to SQL reporting, vector search, or hybrid paths before the LLM answers.
4. **Infrastructure:** Docker Compose for PostgreSQL, Qdrant, and Redis; the API and workers usually run on the host via `uv` (see [Backend Setup](../backend/setup.md)).

## Guide contents

| Guide | Topics |
|--------|--------|
| [**Backend Architecture & Foundations**](backend.md) | REST, FastAPI layers, JWT, Alembic, Celery/Redis pipeline, project layout under `backend/app/`. |
| [**Frontend SPA Foundations**](frontend.md) | SPA model, Svelte 5, Vite, Tailwind, Axios + JWT, client-side routing. |
| [**AI & RAG Mechanics**](agent_rag.md) | RAG concept, ingestion vs chat paths, Qdrant collections, query orchestration, where LangChain appears today. |
| [**Infrastructure & Orchestration**](infrastructure.md) | Docker, Compose services (`db`, `qdrant`, `redis`), volumes, how that fits local development. |
| [**LM Studio**](lmstudio_setup.md) | Short tutorial: start server, minimal `.env`, same env for Celery; points to the full [Agent LM Studio reference](../agent/lm_studio.md). |

For operational steps (env vars, workers, migrations), prefer [Backend Setup](../backend/setup.md), [Project SETUP](../SETUP.md), and [Agent Setup](../agent/setup.md).
