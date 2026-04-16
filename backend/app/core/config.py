import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI RAG Assistant"
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/app_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_HIGH_PRIORITY_QUEUE: str = os.getenv("CELERY_HIGH_PRIORITY_QUEUE", "document-high-priority")
    CELERY_BULK_QUEUE: str = os.getenv("CELERY_BULK_QUEUE", "document-bulk")
    CELERY_EXTRACTION_RATE_LIMIT: str = os.getenv("CELERY_EXTRACTION_RATE_LIMIT", "10/m")
    BULK_IMPORT_BATCH_SIZE: int = int(os.getenv("BULK_IMPORT_BATCH_SIZE", "50"))

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "huggingface")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    EMBEDDINGS_PROVIDER: str = os.getenv("EMBEDDINGS_PROVIDER", "huggingface")
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    LMSTUDIO_API_BASE: str = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    LMSTUDIO_API_KEY: str = os.getenv("LMSTUDIO_API_KEY", "not-needed")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))
    PARSED_MARKDOWN_DIR: str = os.getenv("PARSED_MARKDOWN_DIR", str(BACKEND_DIR / "artifacts" / "markdown"))
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(20 * 1024 * 1024)))

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
