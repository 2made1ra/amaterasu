# Project Glossary / Глоссарий проекта

This document provides a comprehensive list of technical terms and business concepts used in the Amaterasu project.
Этот документ содержит полный список технических терминов и бизнес-концепций, используемых в проекте Amaterasu.

---

## 🏗️ Architecture / Архитектура

### SPA (Single Page Application)
*   **EN:** A web application or website that interacts with the user by dynamically rewriting the current web page with new data from the web server, instead of the default method of a browser loading entire new pages.
*   **RU:** Веб-приложение или веб-сайт, который взаимодействует с пользователем путем динамической перезаписи текущей веб-страницы новыми данными с веб-сервера вместо стандартного метода загрузки браузером целых новых страниц.
*   *See:* [Architecture Overview](architecture/overview.md)

### REST API (Representational State Transfer API)
*   **EN:** An architectural style for an application program interface (API) that uses HTTP requests to access and use data.
*   **RU:** Архитектурный стиль для интерфейса прикладного программирования (API), который использует HTTP-запросы для доступа к данным и их использования.
*   *See:* [API Endpoints Overview](api/endpoints.md)

### Decoupled Architecture / Разделенная архитектура
*   **EN:** An architectural approach where the frontend and backend are developed and deployed independently, communicating via an API.
*   **RU:** Архитектурный подход, при котором фронтенд и бэкенд разрабатываются и развертываются независимо, взаимодействуя через API.
*   *See:* [Architecture Overview](architecture/overview.md)

---

## 🎨 Frontend / Фронтенд

### Svelte
*   **EN:** A modern JavaScript framework that compiles components into highly efficient vanilla JavaScript at build time, instead of using a virtual DOM.
*   **RU:** Современный JavaScript-фреймворк, который компилирует компоненты в высокоэффективный чистый JavaScript на этапе сборки, вместо использования виртуального DOM.
*   *See:* [Frontend Overview](frontend/overview.md)

### Vite
*   **EN:** A fast build tool and development server that provides an extremely quick development experience.
*   **RU:** Быстрый инструмент сборки и сервер разработки, обеспечивающий чрезвычайно высокую скорость работы при разработке.
*   *See:* [Frontend Overview](frontend/overview.md)

### Tailwind CSS
*   **EN:** A utility-first CSS framework for rapidly building custom user interfaces directly in the markup.
*   **RU:** CSS-фреймворк с подходом "utility-first" для быстрой разработки пользовательских интерфейсов непосредственно в разметке.
*   *See:* [Frontend Overview](frontend/overview.md)

### Axios
*   **EN:** A promise-based HTTP client for the browser and node.js, used in this project to communicate with the FastAPI backend.
*   **RU:** HTTP-клиент на основе промисов для браузера и node.js, используемый в данном проекте для взаимодействия с FastAPI бэкендом.
*   *See:* [API Integration](frontend/api-integration.md)

### HMR (Hot Module Replacement)
*   **EN:** A feature that updates modules in a running application without a full reload, significantly speeding up development.
*   **RU:** Функция, которая обновляет модули в работающем приложении без полной перезагрузки, что значительно ускоряет разработку.
*   *See:* [Frontend Overview](frontend/overview.md)

---

## ⚙️ Backend / Бэкенд

### FastAPI
*   **EN:** A modern, high-performance web framework for building APIs with Python, based on standard Python type hints.
*   **RU:** Современный высокопроизводительный веб-фреймворк для создания API на Python, основанный на стандартных подсказках типов Python.
*   *See:* [Backend Overview](backend/overview.md)

### SQLAlchemy
*   **EN:** A powerful SQL toolkit and Object-Relational Mapper (ORM) for Python.
*   **RU:** Мощный набор инструментов SQL и объектно-реляционное отображение (ORM) для Python.
*   *See:* [Backend Overview](backend/overview.md)

### ORM (Object-Relational Mapping)
*   **EN:** A programming technique for converting data between incompatible type systems using object-oriented programming languages.
*   **RU:** Технология программирования, которая связывает базы данных с концепциями объектно-ориентированных языков программирования, создавая «виртуальную объектную базу данных».
*   *See:* [Backend Architecture & Foundations](learning_guide/backend.md)

### Alembic
*   **EN:** A lightweight database migration tool for use with SQLAlchemy to manage schema changes.
*   **RU:** Легкий инструмент миграции баз данных для использования с SQLAlchemy для управления изменениями схемы.
*   *See:* [Backend Overview](backend/overview.md)

### PostgreSQL
*   **EN:** A powerful, open-source object-relational database system used for storing structured data.
*   **RU:** Мощная объектно-реляционная система баз данных с открытым исходным кодом, используемая для хранения структурированных данных.
*   *See:* [Backend Overview](backend/overview.md)

### JWT (JSON Web Token)
*   **EN:** A compact, URL-safe means of representing claims to be transferred between two parties, used here for authentication.
*   **RU:** Компактный, URL-безопасный способ представления утверждений, передаваемых между двумя сторонами, используемый здесь для аутентификации.
*   *See:* [Authentication Flow](backend/processes/authentication.md)

### Pydantic
*   **EN:** A library for data validation and settings management using Python type annotations.
*   **RU:** Библиотека для валидации данных и управления настройками с использованием аннотаций типов Python.
*   *See:* [Backend Overview](backend/overview.md)

### CRUD (Create, Read, Update, Delete)
*   **EN:** The four basic functions of persistent storage.
*   **RU:** Четыре базовые функции работы с данными: создание, чтение, обновление, удаление.
*   *See:* [Backend Overview](backend/overview.md)

### Celery
*   **EN:** A distributed task queue used here to run the document pipeline outside HTTP requests: PDF parsing, LLM fact extraction, and Qdrant indexing, with separate queues for interactive uploads and bulk traffic.
*   **RU:** Распределённая очередь задач; в проекте выполняет пайплайн документов вне HTTP: разбор PDF, извлечение фактов через LLM и индексация в Qdrant, с раздельными очередями для интерактивных загрузок и массового импорта.
*   *See:* [Tasks Layer](backend/layers/tasks.md), [Backend Setup](backend/setup.md)

### uv
*   **EN:** A fast Python package and project manager used to sync dependencies (`uv sync`), run the API (`uv run uvicorn`), workers, Alembic, and tests.
*   **RU:** Быстрый менеджер пакетов и проектов Python; в репозитории используется для установки зависимостей (`uv sync`), запуска API, воркеров, Alembic и тестов.
*   *See:* [Backend Setup](backend/setup.md)

---

## 📄 Document pipeline & workspace / Пайплайн документов и рабочее пространство

### Extraction run / Прогон извлечения
*   **EN:** A database record for one attempt to parse a document and extract structured facts, including status, version, timestamps, and error details when processing fails.
*   **RU:** Запись в БД об одной попытке разобрать документ и извлечь структурированные факты: статус, версия, метки времени и детали ошибки при сбое.
*   *See:* [Models Layer](backend/layers/models.md), [Document Upload](backend/processes/document_upload.md)

### Contract facts / Факты договора
*   **EN:** Structured JSON extracted from contract PDFs (per document and extraction version), validated after LLM output; forms the basis for review, approval, SQL reporting, and indexing into Qdrant.
*   **RU:** Структурированный JSON, извлечённый из PDF договоров (на документ и версию извлечения), с валидацией после ответа LLM; основа для ревью, утверждения, SQL-отчётов и индексации в Qdrant.
*   *See:* [Document Upload](backend/processes/document_upload.md), [Services Layer](backend/layers/services.md)

### Bulk ingestion (controlled) / Массовый импорт (контролируемый)
*   **EN:** A CLI-driven flow that uploads many PDFs via the same `POST /documents/upload` contract, assigns `batch_id` metadata, uses the bulk queue, and can mark imports as trusted for auto-approval when policy allows.
*   **RU:** Сценарий через CLI: загрузка множества PDF тем же контрактом `POST /documents/upload`, с метаданными `batch_id`, очередью bulk и опцией доверенного импорта для автоутверждения при допустимых правилах.
*   *See:* [Backend Setup](backend/setup.md), [API Endpoints](api/endpoints.md)

### Ingestion batch / Партия импорта
*   **EN:** A logical grouping of uploads sharing a `batch_id`, used to track aggregate progress (processing, review, indexing) via `GET /batches/{batch_id}`.
*   **RU:** Логическая группа загрузок с общим `batch_id` для отслеживания агрегированного прогресса (обработка, ревью, индексация) через `GET /batches/{batch_id}`.
*   *See:* [API Endpoints](api/endpoints.md)

### Trusted import / Доверенный импорт
*   **EN:** A flag on upload indicating that, after successful fact validation, the pipeline may auto-approve and enqueue indexing without manual confirmation (typically for controlled bulk sources).
*   **RU:** Флаг загрузки: при успешной валидации фактов пайплайн может автоматически утвердить документ и поставить индексацию в очередь без ручного подтверждения (обычно для контролируемых массовых источников).
*   *See:* [Document Upload](backend/processes/document_upload.md)

### Main workspace chat (chat session) / Чат основного рабочего пространства
*   **EN:** Persistent multi-turn chat tied to `chat_sessions` and `chat_messages`, including an explorer snapshot (result tree, selection, view mode) saved in PostgreSQL; distinct from temporary contract-modal chat.
*   **RU:** Персистентный многоходовой чат, привязанный к `chat_sessions` и `chat_messages`, со снимком проводника (дерево результатов, выбор, режим просмотра) в PostgreSQL; отличается от временного чата в модалке договора.
*   *See:* [Backend Overview](backend/overview.md), [API Endpoints](api/endpoints.md)

### Contract-scoped chat / Чат в контексте договора
*   **EN:** A temporary query flow under `POST /documents/{id}/chat` inside the contract UI; not stored in session history and constrained to the selected document context.
*   **RU:** Временный запрос через `POST /documents/{id}/chat` в UI договора; не сохраняется в истории сессий и ограничен контекстом выбранного документа.
*   *See:* [API Endpoints](api/endpoints.md), [Query Orchestration](backend/processes/rag_chat.md)

---

## 🤖 AI & RAG / ИИ и RAG

### RAG (Retrieval-Augmented Generation)
*   **EN:** An architecture that enhances the capabilities of LLMs by retrieving relevant information from an external knowledge base before generating a response.
*   **RU:** Архитектура, которая расширяет возможности LLM путем извлечения соответствующей информации из внешней базы знаний перед генерацией ответа.
*   *See:* [Agent Overview](agent/overview.md)

### LangChain
*   **EN:** A framework designed to simplify the creation of applications using large language models (LLMs).
*   **RU:** Фреймворк, предназначенный для упрощения создания приложений с использованием больших языковых моделей (LLM).
*   *See:* [Agent Overview](agent/overview.md)

### Vector Database / Векторная база данных
*   **EN:** A specialized database that stores data as high-dimensional vectors, allowing for efficient similarity searches.
*   **RU:** Специализированная база данных, которая хранит данные в виде многомерных векторов, что позволяет эффективно выполнять поиск по сходству.
*   *See:* [Agent Overview](agent/overview.md)

### Qdrant
*   **EN:** A high-performance vector similarity search engine used here with separate collections for document-level summaries and smaller text chunks, with idempotent delete-before-upsert indexing after approval.
*   **RU:** Высокопроизводительный движок векторного поиска; в проекте используются отдельные коллекции для сводок по документу и для фрагментов текста, с идемпотентной индексацией (удаление перед upsert) после утверждения.
*   *See:* [Architecture Overview](architecture/overview.md), [Agent Overview](agent/overview.md)

### Embeddings / Эмбеддинги (Векторные представления)
*   **EN:** Mathematical representations of text in a high-dimensional space, where semantically similar items are located close to each other.
*   **RU:** Математические представления текста в многомерном пространстве, где семантически похожие элементы расположены близко друг к другу.
*   *See:* [AI & RAG Mechanics](learning_guide/agent_rag.md)

### LLM (Large Language Model)
*   **EN:** An AI model trained on vast amounts of text data, capable of generating human-like text and understanding context.
*   **RU:** Модель ИИ, обученная на огромных объемах текстовых данных, способная генерировать текст, похожий на человеческий, и понимать контекст.
*   *See:* [Agent Overview](agent/overview.md)

### Token / Токен
*   **EN:** The basic unit of text that an LLM processes (can be a word, part of a word, or punctuation).
*   **RU:** Базовая единица текста, которую обрабатывает LLM (может быть словом, частью слова или знаком препинания).
*   *See:* [AI & RAG Mechanics](learning_guide/agent_rag.md)

### Context Window / Окно контекста
*   **EN:** The maximum amount of information (tokens) an LLM can process in a single request.
*   **RU:** Максимальный объем информации (токенов), который LLM может обработать за один запрос.
*   *See:* [The RAG Pipeline Flow](agent/rag_flow.md)

### Semantic Search / Семантический поиск
*   **EN:** A search technique that seeks to understand the intent and contextual meaning of the search query, rather than just matching keywords.
*   **RU:** Метод поиска, который стремится понять намерение и контекстуальное значение поискового запроса, а не просто сопоставлять ключевые слова.
*   *See:* [Agent Overview](agent/overview.md)

### Query orchestration / Оркестрация запросов
*   **EN:** The layer that classifies a user question, routes it to SQL over `contract_facts`, summary-first or chunk vector search in Qdrant, or hybrid paths, then assembles the assistant response (used by `/chat` and workspace messaging).
*   **RU:** Слой, который классифицирует вопрос пользователя, направляет запрос в SQL по `contract_facts`, в векторный поиск сводок или чанков в Qdrant, либо в гибридные сценарии, затем собирает ответ ассистента (используется в `/chat` и сообщениях рабочего пространства).
*   *See:* [Query Orchestration Process](backend/processes/rag_chat.md), [RAG Flow](agent/rag_flow.md)

### LM Studio
*   **EN:** A local app that serves OpenAI-compatible HTTP APIs; the backend can point `LLM_PROVIDER` / `EMBEDDINGS_PROVIDER` to `lmstudio` and use `LMSTUDIO_API_BASE` for chat and embeddings instead of local Hugging Face pipelines.
*   **RU:** Локальное приложение с OpenAI-совместимым HTTP API; бэкенд может выставить `LLM_PROVIDER` / `EMBEDDINGS_PROVIDER` в `lmstudio` и использовать `LMSTUDIO_API_BASE` для чата и эмбеддингов вместо локальных пайплайнов Hugging Face.
*   *See:* [Agent — LM Studio integration](agent/lm_studio.md), [Agent Setup](agent/setup.md), [Learning guide — LM Studio](learning_guide/lmstudio_setup.md)

### PromptTemplate / Шаблон промпта
*   **EN:** A reproducible way to generate prompts for LLMs, often containing instructions and placeholders for context.
*   **RU:** Воспроизводимый способ генерации подсказок (промптов) для LLM, часто содержащий инструкции и заполнители для контекста.
*   *See:* [The RAG Pipeline Flow](agent/rag_flow.md)

---

## 🐳 Infrastructure / Инфраструктура

### Docker
*   **EN:** A platform for developing, shipping, and running applications in isolated containers.
*   **RU:** Платформа для разработки, доставки и запуска приложений в изолированных контейнерах.
*   *See:* [Architecture Overview](architecture/overview.md)

### Docker Compose
*   **EN:** A tool for defining and running multi-container Docker applications.
*   **RU:** Инструмент для определения и запуска многоконтейнерных приложений Docker.
*   *See:* [Infrastructure & Orchestration](learning_guide/infrastructure.md)

### Redis
*   **EN:** In-memory data store used here as the Celery broker and result backend so background tasks (parsing, extraction, indexing) are decoupled from the FastAPI process.
*   **RU:** In-memory хранилище; в проекте — брокер и бэкенд результатов Celery, чтобы фоновые задачи (парсинг, извлечение, индексация) не выполнялись в процессе FastAPI.
*   *See:* [Backend Setup](backend/setup.md)

### Containerization / Контейнеризация
*   **EN:** The process of packaging an application and its dependencies into a single container image.
*   **RU:** Процесс упаковки приложения и его зависимостей в один образ контейнера.
*   *See:* [Infrastructure & Orchestration](learning_guide/infrastructure.md)

---

## 💼 Business Processes & Concepts / Бизнес-процессы и концепции

### Human-in-the-Loop (HitL)
*   **EN:** A process where the system prepares a draft state for a document and requires human validation or confirmation before the document can be treated as approved.
*   **RU:** Процесс, при котором система подготавливает черновое состояние документа и требует подтверждения человеком, прежде чем документ будет считаться утвержденным.
*   *See:* [Document Upload & Processing](backend/processes/document_upload.md)

### Tenant Isolation / Изоляция тенантов (арендаторов)
*   **EN:** A security measure ensuring that users can only access and query their own documents, even if they are stored in the same database.
*   **RU:** Мера безопасности, гарантирующая, что пользователи могут получать доступ и запрашивать только свои собственные документы, даже если они хранятся в одной базе данных.
*   *See:* [The RAG Pipeline Flow](agent/rag_flow.md)

### Metadata Extraction / Извлечение метаданных
*   **EN:** The automatic process of identifying and saving structured information from a document (for example dates, names, or amounts), typically into a dedicated facts store.
*   **RU:** Автоматический процесс идентификации и сохранения структурированной информации из документа (например, дат, имен или сумм), обычно в отдельное хранилище фактов.
*   *See:* [Document Upload & Processing](backend/processes/document_upload.md)

### Document Ingestion / Поглощение документов
*   **EN:** The end-to-end process of importing a document, persisting it, extracting structured facts, and optionally indexing it for search.
*   **RU:** Сквозной процесс импорта документа, его сохранения, извлечения структурированных фактов и, при необходимости, индексации для поиска.
*   *See:* [The RAG Pipeline Flow](agent/rag_flow.md)

### Hallucination / Галлюцинация
*   **EN:** A phenomenon where an LLM generates information that is factually incorrect or not present in the provided context.
*   **RU:** Феномен, при котором LLM генерирует информацию, которая фактически неверна или отсутствует в предоставленном контексте.
*   *See:* [Agent Overview](agent/overview.md)
