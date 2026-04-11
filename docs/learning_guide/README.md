# Building Amaterasu: The Learning Guide

Welcome to the Amaterasu Learning Guide! This guide is designed to help you understand the theoretical foundations and practical applications required to build a full-stack AI RAG (Retrieval-Augmented Generation) project from scratch, without the assistance of an AI agent.

To recreate a project like Amaterasu, you need a solid understanding of modern web application architecture, broken down into several key layers. Rather than overwhelming you with endless documentation, this guide applies the Pareto principle (80/20 rule), focusing on the core concepts that drive the majority of the application's functionality.

## Core Concepts to Understand

Building this project requires integrating four major components:

1. **The Backend (API & Business Logic):** How to create a robust server that handles requests, manages a database, and secures user data.
2. **The Frontend (User Interface):** How to build a responsive Single Page Application (SPA) that interacts seamlessly with your backend API.
3. **The AI Agent & RAG Pipeline:** How to process documents, convert them into a machine-readable format, and use an LLM to answer questions based on that specific context.
4. **The Infrastructure:** How to package all these separate moving parts into isolated containers that can easily communicate and run consistently on any machine.

## Guide Contents

We have broken down the learning material into focused sub-documents. Each document covers the essential theory, followed by concrete examples of how that theory is applied in the Amaterasu project.

*   [**Backend Architecture & Foundations**](backend.md)
    *   REST APIs, FastAPI, ORMs (SQLAlchemy), and JWT Authentication.
*   [**Frontend SPA Foundations**](frontend.md)
    *   Single Page Applications, Svelte, Component state, and Client-Side Routing.
*   [**AI & RAG Mechanics**](agent_rag.md)
    *   Retrieval-Augmented Generation (RAG), Vector Embeddings, Qdrant, and LangChain orchestration.
*   [**Infrastructure & Orchestration**](infrastructure.md)
    *   Containerization with Docker and multi-container setups with Docker Compose.

By progressing through these guides step by step, you will build the mental model required to architect and implement your own full-stack AI assistant from the ground up.
