# Document Upload & Processing

This document outlines the process of uploading a document, extracting metadata, and the Human-in-the-Loop (HitL) validation step.

## Description
When a document is uploaded, it is saved, and its content is extracted. An AI service attempts to automatically extract relevant metadata. Because AI extraction is not perfect, the metadata is saved with a "Pending Review" status. A human user must review and potentially edit the metadata before approving it. The original document remains immutable throughout this process.

## C4 Sequence Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Sequence.puml

title Document Upload and Human-in-the-Loop Flow

Person(user, "User", "Admin or Authorized User")
System_Boundary(backend, "Backend Application") {
    Component(api, "Documents API", "FastAPI", "/api/v1/documents")
    Component(services, "AI Extraction Service", "LangChain/LLM", "Extracts Metadata")
    Component(crud, "Document CRUD", "Python", "Database Operations")
    ContainerDb(db, "PostgreSQL", "Database", "Stores Metadata & Status")
    ContainerDb(vector_db, "Qdrant", "Vector DB", "Stores Document Embeddings")
}

== Upload & Extraction ==
Rel(user, api, "1. POST /upload (file)")
Rel(api, crud, "2. Save initial record")
Rel(api, services, "3. Process file & Extract Metadata")
Rel(services, api, "4. Return Extracted Metadata")
Rel(api, crud, "5. Update record (Status: PENDING_REVIEW)")
Rel(crud, db, "6. Save metadata")
Rel(api, user, "7. Return Upload Success & Pending Metadata")

== Human-in-the-Loop (HitL) Review ==
Rel(user, api, "8. GET /documents/{id}/review")
Rel(api, user, "9. Return extracted metadata for review")
Rel(user, api, "10. PUT /documents/{id}/approve (Updated Metadata)")
Rel(api, crud, "11. Save finalized metadata (Status: APPROVED)")
Rel(crud, db, "12. Update Database")
Rel(api, services, "13. Generate Embeddings & Index")
Rel(services, vector_db, "14. Store Embeddings")
Rel(api, user, "15. Approval Success")

@enduml
```
