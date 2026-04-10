# Agent Setup & Environment

This guide covers the setup and configuration of the AI Agent components.

## Environment Variables

The agent relies heavily on environment variables configured in the backend's `.env` file or environment.

### 1. LLM Provider Configuration
You must configure the LLM you intend to use. The project utilizes LangChain, which supports numerous providers (OpenAI, Anthropic, HuggingFace, etc.).

If using OpenAI, for example:
```env
OPENAI_API_KEY=your_openai_api_key_here
```
*(Ensure `app/services/llm.py` is configured to initialize the specific LLM based on these keys).*

### 2. Qdrant Configuration
The vector database needs to be accessible by the backend. The default values match the `docker-compose.yml` setup.

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Infrastructure: Qdrant Vector Database

Qdrant is run via Docker Compose. Ensure it is running:
```bash
docker-compose up -d qdrant
```

Qdrant exposes two ports:
* `6333`: REST API
* `6334`: gRPC API

The backend communicates with Qdrant via the `qdrant-client` python package.

## Embedding Model Setup

The project uses embeddings to convert text to vectors. This is managed in `app/services/llm.py`. Depending on the implementation, this might use OpenAI's embedding models (requiring `OPENAI_API_KEY`) or local, open-source models via `sentence-transformers`. If using local models, they will be downloaded automatically the first time they are invoked.
