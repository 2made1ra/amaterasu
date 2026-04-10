# Architecture Overview

This document outlines the overall architecture of the project, including the technology stack and the rationale behind the chosen components.

## System Architecture

The project follows a modern full-stack application architecture, consisting of a decoupled frontend and backend. The backend also acts as an orchestrator for an AI-powered Retrieval-Augmented Generation (RAG) agent.

The system consists of the following primary components:
1. **Frontend (SPA):** Provides the user interface for interacting with the application, uploading documents, and querying the agent.
2. **Backend (REST API):** Handles business logic, authentication, document management, and communication with the AI Agent and databases.
3. **Database (Relational):** Stores structured application data, such as users and document metadata.
4. **Vector Database:** Stores high-dimensional vector embeddings of processed documents for semantic search.
5. **AI Agent (RAG):** Processes documents, generates embeddings, and answers user queries based on context.

## Technology Stack

### Frontend
* **Svelte (SPA):** A lightweight, component-based framework for building fast web interfaces.
* **Vite:** A fast build tool and development server.
* **Tailwind CSS:** A utility-first CSS framework for rapid UI styling.

### Backend
* **Python & FastAPI:** A high-performance, asynchronous web framework for building REST APIs in Python.
* **SQLAlchemy:** An Object Relational Mapper (ORM) for interacting with the relational database.
* **Alembic:** Database migration tool for SQLAlchemy.
* **PyJWT:** Handles JSON Web Token authentication.

### Data Storage
* **PostgreSQL:** A robust, open-source relational database management system used for storing structured data (users, document metadata).
* **Qdrant:** A high-performance open-source vector search engine used to store document embeddings and perform similarity search for the RAG pipeline.

### AI & Agent
* **LangChain:** A framework for developing applications powered by language models. It orchestrates the RAG workflow, including document loading, splitting, vectorization, and LLM querying.
* **Large Language Models (LLMs):** Used to generate text, extract metadata from documents, and answer user questions. (Provider configurable).
* **Embeddings (Sentence Transformers):** Used to convert document text into vector representations.

### Infrastructure
* **Docker & Docker Compose:** Used to containerize the database services (PostgreSQL and Qdrant) for easy local development and deployment.

## Architectural Rationale

* **Why Svelte + Vite?** Svelte shifts the bulk of the work to compile time, resulting in highly optimized vanilla JavaScript, making it faster and lighter than Virtual DOM-based frameworks like React. Vite provides an exceptionally fast development experience with Hot Module Replacement (HMR).
* **Why FastAPI?** FastAPI is built on Starlette and Pydantic, offering excellent performance, automatic Swagger UI documentation, and native support for asynchronous programming (async/await), which is crucial for handling slow I/O operations like LLM API calls.
* **Why PostgreSQL?** PostgreSQL is a reliable, feature-rich relational database that handles structured data flawlessly and provides ACID compliance.
* **Why Qdrant?** Qdrant is specifically designed for vector similarity search. It offers high performance, easy integration via REST/gRPC, and supports payload filtering (e.g., Tenant Isolation filtering by `owner_id`), which is critical for secure RAG applications.
* **Why LangChain?** LangChain abstracts the complexities of connecting LLMs with external data sources. It provides standard interfaces for document loaders, text splitters, vector stores, and prompt templates, making the RAG implementation modular and maintainable.
