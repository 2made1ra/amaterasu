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
*   **EN:** A high-performance vector similarity search engine and database used in this project.
*   **RU:** Высокопроизводительный движок поиска векторного сходства и база данных, используемые в данном проекте.
*   *See:* [Architecture Overview](architecture/overview.md)

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
