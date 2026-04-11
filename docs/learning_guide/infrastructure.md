# Infrastructure & Orchestration

For a complex application to run reliably on any machine, we need a way to package the software and its dependencies so that it behaves exactly the same on a developer's laptop as it does on a production server.

## 1. Containerization (Docker)
**Theory:** Before containers, installing software meant configuring the host operating system, installing specific versions of Python, Node.js, system libraries, and databases. If versions mismatched, the application broke ("It works on my machine!").
Docker solves this via containers. A container is a lightweight, standalone, executable package that includes everything needed to run a piece of software: the code, runtime, system tools, and libraries.

**Project Application:** The Amaterasu backend is packaged into a Docker container. We define a `Dockerfile` that says exactly what Python version to use and which dependencies (`requirements.txt`) to install. Because it runs in Docker, it doesn't matter if your laptop runs Windows, Mac, or Linux; the backend environment is perfectly isolated and consistent.

## 2. Multi-Container Orchestration (Docker Compose)
**Theory:** A modern full-stack application isn't just one piece of software. Amaterasu consists of:
1.  The FastAPI backend application.
2.  A PostgreSQL relational database.
3.  A Qdrant vector database.

While you could run three separate Docker commands manually, it's inefficient. **Docker Compose** is a tool for defining and running multi-container Docker applications. You use a single YAML file (`docker-compose.yml`) to configure all your application's services, how they communicate via networks, and where they store persistent data via volumes.

**Project Application:** Amaterasu uses a `docker-compose.yml` file located at the root of the project.
*   **Services:** It defines a `db` service for PostgreSQL, a `qdrant` service for the vector DB, and an `api` service for the FastAPI backend.
*   **Networking:** Docker Compose automatically creates an internal network. The FastAPI backend can talk to the PostgreSQL database simply by using the hostname `db`, instead of needing a complex IP address.
*   **Volumes:** Databases need to save data permanently. If a container restarts, all data inside it is lost. Docker Compose defines "volumes" that map a folder inside the container to a permanent folder on your hard drive, ensuring your uploaded documents and user accounts survive container restarts.

By running `docker-compose up`, the entire infrastructure required for the backend and databases spins up simultaneously, cleanly connected and ready to use.