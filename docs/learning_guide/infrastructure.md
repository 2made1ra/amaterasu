# Infrastructure & Orchestration

Reliable local development and deployment depend on **repeatable environments**. Amaterasu splits “data plane” services (containers) from the **API and workers** (usually run on the host with `uv`).

## 1. Containerization (Docker)

**Theory:** A **container** packages an app with its runtime and dependencies so behavior is consistent across machines (“works on my machine” is less of a problem when images are versioned).

**In this project:** A **`backend/Dockerfile`** exists for packaging the Python app when you want a containerized API. Day-to-day development in the docs typically runs **FastAPI and Celery with `uv`** on the host while databases run in Compose—see [Backend Setup](../backend/setup.md).

## 2. Docker Compose (data services)

**Theory:** **Docker Compose** describes multiple services, ports, networks, and **volumes** in one YAML file so you can start PostgreSQL, Redis, Qdrant, etc. with one command.

**In this project:** The root **`docker-compose.yml`** defines the data services directly, and also includes optional `api` / Celery services behind the `app` profile:

| Service | Purpose |
|---------|---------|
| **`db`** | PostgreSQL 15 (`user` / `password`, database `app_db`), port `5432`. |
| **`qdrant`** | Vector store, ports `6333` (HTTP/API) and `6334`. |
| **`redis`** | Broker/backend for Celery, port `6379`. |
| **`api`**, **`celery-worker-high`**, **`celery-worker-bulk`** | Optional containerized backend services, started only with `--profile app`. |

For the default host-based dev flow, run:

```bash
docker compose up -d
```

(On older installs, `docker-compose up -d` is equivalent.)

**Volumes** (`postgres_data`, `qdrant_data`) persist database files across container restarts.

If you want the backend and workers in Docker too, run:

```bash
docker compose --profile app up -d --build
```

## 3. Networking and configuration

**Theory:** Apps connect to services by **host name** on Docker networks; on the host machine you usually use `localhost` and published ports.

**In this project:** With Compose running, `DATABASE_URL` defaults align with `postgresql://user:password@localhost/app_db`. Redis defaults to `redis://localhost:6379/0`. Qdrant defaults to `localhost:6333`. Adjust via environment variables if you use remote services.

## 4. What runs where (mental model)

- **In Compose:** PostgreSQL, Qdrant, Redis.
- **On the developer machine (typical):** `uv run uvicorn app.main:app`, and one or two Celery workers consuming `document-high-priority` and `document-bulk` queues.

That separation keeps iteration fast (reload API) while still matching production-like data dependencies.
