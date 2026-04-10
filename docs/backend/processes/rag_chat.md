# RAG Agent Chat

This document describes the Retrieval-Augmented Generation (RAG) process used by the chat agent.

## Description
When a user asks a question, the system uses a RAG approach. It first converts the query into a vector embedding, searches the vector database (Qdrant) for the most relevant document chunks, and then passes those chunks along with the user's query to a Large Language Model (LLM). The agent's goal is to return a summarized, coherent answer based strictly on the retrieved context, rather than just returning raw document chunks.

## C4 Sequence Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Sequence.puml

title RAG Chat and Search Flow

Person(user, "User", "Client querying the agent")
System_Boundary(backend, "Backend Application") {
    Component(api, "Chat API", "FastAPI", "/api/v1/chat")
    Component(rag_service, "RAG Service", "LangChain", "Orchestrates Retrieval & Generation")
    Component(llm_service, "LLM Integration", "Python", "Calls OpenAI/LLM")
    ContainerDb(vector_db, "Qdrant", "Vector DB", "Similarity Search")
}
System_Ext(llm_provider, "LLM Provider", "e.g., OpenAI")

Rel(user, api, "1. POST /chat (User Query)")
Rel(api, rag_service, "2. Handle Query")
Rel(rag_service, llm_service, "3. Embed User Query")
Rel(llm_service, llm_provider, "4. Request Embedding")
Rel(llm_provider, llm_service, "5. Return Vector")
Rel(rag_service, vector_db, "6. Similarity Search (Vector)")
Rel(vector_db, rag_service, "7. Return Relevant Chunks")
Rel(rag_service, llm_service, "8. Generate Summary (Query + Chunks)")
Rel(llm_service, llm_provider, "9. Request Completion (Prompt)")
Rel(llm_provider, llm_service, "10. Return Summarized Answer")
Rel(rag_service, api, "11. Return Final Response")
Rel(api, user, "12. Return Summarized Answer JSON")

@enduml
```
