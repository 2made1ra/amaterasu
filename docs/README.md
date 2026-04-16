# Project Documentation

Welcome to the documentation for the AI RAG Assistant project. The current backend implementation supports migration-driven PostgreSQL schema management, asynchronous document parsing/fact extraction with Celery + Redis, controlled bulk ingestion with batch tracking, and workspace/chat surfaces around those documents.

## Navigation

Explore the documentation by module:

### 1. 🏗️ Architecture
* [Architecture Overview](architecture/overview.md) - Learn about the system design, tech stack (Svelte, FastAPI, LangChain, Qdrant), and the rationale behind these choices.

### 2. 🎨 Frontend
* [Frontend Overview](frontend/overview.md) - Details on the Svelte SPA.
* [Frontend Setup Guide](frontend/setup.md) - Instructions on how to run and build the frontend locally.

### 3. ⚙️ Backend
* [Backend Overview](backend/overview.md) - Details on the FastAPI and PostgreSQL backend structure.
* [Backend Setup Guide](backend/setup.md) - Instructions on running the backend, workers, and required infrastructure via Docker Compose using `uv`.

### 4. 🤖 AI Agent & Search
* [Agent Overview](agent/overview.md) - Learn how the query router, SQL path, and vector retrieval layer fit together.
* [Agent Setup & Environment](agent/setup.md) - Guide for configuring LLM providers and Qdrant.
* [The Query Orchestration Flow](agent/rag_flow.md) - A step-by-step deep dive into document ingestion, filtering, routing, and retrieval.

### 5. 🔌 API Reference
* [API Endpoints Overview](api/endpoints.md) - A conceptual overview of the REST API (Auth, Documents, Chat). For full interactive documentation, run the backend and visit `/docs`.

### 6. 🗺️ Plans
* [Product Requirements Document](plans/prd.md) - Product goals, business context, and phased delivery expectations.
* [Implementation Plan](plans/implementation_plan.md) - Engineering plan for PostgreSQL, async ingestion, Qdrant indexing, and query routing (phases 1–4 implemented in repo; document retains phase detail and agent rules).

### 📖 Glossary
* [Project Glossary](glossary.md) - A comprehensive list of technical and business terms used throughout the project.
