# Authentication Process

This document outlines the authentication process using JWT (JSON Web Tokens).

## Description
The system uses stateless authentication. A user logs in with their credentials, and the server returns a JWT. The client must include this token in the `Authorization` header (`Bearer <token>`) for subsequent requests to protected endpoints.

## C4 Sequence Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Sequence.puml

title Authentication Flow

Person(client, "Client App", "Frontend or API Consumer")
System_Boundary(backend, "Backend Application") {
    Component(api, "Auth API Endpoint", "FastAPI", "/api/v1/login")
    Component(security, "Security Core", "Python", "Password Verification & JWT Generation")
    Component(crud, "User CRUD", "Python", "Database Operations")
    ContainerDb(db, "PostgreSQL", "Database", "Stores User Credentials")
}

Rel(client, api, "1. POST /login (email, password)")
Rel(api, crud, "2. Get user by email")
Rel(crud, db, "3. Query user")
Rel(db, crud, "4. Return user record (including hashed password)")
Rel(crud, api, "5. Return user object")
Rel(api, security, "6. Verify password")
Rel(security, api, "7. Password matches")
Rel(api, security, "8. Generate JWT token")
Rel(security, api, "9. Return token")
Rel(api, client, "10. Return JSON {access_token: '...', token_type: 'bearer'}")

@enduml
```
