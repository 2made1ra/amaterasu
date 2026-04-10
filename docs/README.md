# Project Documentation

Welcome to the documentation for the AI RAG Assistant project. This application allows users to upload documents and query an AI agent to extract information, summarize data, and answer questions based strictly on the uploaded content.

## Navigation

Explore the documentation by module:

### 1. 🏗️ Architecture
* [Architecture Overview](architecture/overview.md) - Learn about the system design, tech stack (Svelte, FastAPI, LangChain, Qdrant), and the rationale behind these choices.

### 2. 🎨 Frontend
* [Frontend Overview](frontend/overview.md) - Details on the Svelte SPA.
* [Frontend Setup Guide](frontend/setup.md) - Instructions on how to run and build the frontend locally.

### 3. ⚙️ Backend
* [Backend Overview](backend/overview.md) - Details on the FastAPI and PostgreSQL backend structure.
* [Backend Setup Guide](backend/setup.md) - Instructions on running the backend and required databases via Docker Compose.

### 4. 🤖 AI Agent (RAG)
* [Agent Overview](agent/overview.md) - Learn what the Retrieval-Augmented Generation agent does.
* [Agent Setup & Environment](agent/setup.md) - Guide for configuring LLM providers and Qdrant.
* [The RAG Pipeline Flow](agent/rag_flow.md) - A step-by-step deep dive into document ingestion, embedding, tenant isolation, and querying.

### 5. 🔌 API Reference
* [API Endpoints Overview](api/endpoints.md) - A conceptual overview of the REST API (Auth, Documents, Chat). For full interactive documentation, run the backend and visit `/docs`.
