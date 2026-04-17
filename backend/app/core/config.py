import os
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI RAG Assistant"
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="postgresql://user:password@localhost/app_db",
        validation_alias=AliasChoices("SQLALCHEMY_DATABASE_URI", "DATABASE_URL"),
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_SUMMARY_COLLECTION: str = os.getenv("QDRANT_SUMMARY_COLLECTION", "contract_summaries")
    QDRANT_CHUNK_COLLECTION: str = os.getenv("QDRANT_CHUNK_COLLECTION", "contract_chunks")
    QDRANT_VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
    QDRANT_AUTO_DETECT_VECTOR_SIZE: bool = os.getenv("QDRANT_AUTO_DETECT_VECTOR_SIZE", "false").lower() == "true"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_HIGH_PRIORITY_QUEUE: str = os.getenv("CELERY_HIGH_PRIORITY_QUEUE", "document-high-priority")
    CELERY_BULK_QUEUE: str = os.getenv("CELERY_BULK_QUEUE", "document-bulk")
    CELERY_EXTRACTION_RATE_LIMIT: str = os.getenv("CELERY_EXTRACTION_RATE_LIMIT", "10/m")
    BULK_IMPORT_BATCH_SIZE: int = int(os.getenv("BULK_IMPORT_BATCH_SIZE", "50"))

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "huggingface")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    FACT_EXTRACTION_MODEL: str = os.getenv("FACT_EXTRACTION_MODEL", os.getenv("LLM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"))
    SUMMARIZATION_MODEL: str = os.getenv("SUMMARIZATION_MODEL", os.getenv("LLM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"))
    EMBEDDINGS_PROVIDER: str = os.getenv("EMBEDDINGS_PROVIDER", "huggingface")
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    LLM_CONTEXT_WINDOW: int = int(os.getenv("LLM_CONTEXT_WINDOW", "8192"))
    LLM_RESERVED_OUTPUT_TOKENS: int = Field(default=2048)
    LLM_MAX_OUTPUT_TOKENS: int = Field(default=2048)
    LLM_PROMPT_OVERHEAD_TOKENS: int = int(os.getenv("LLM_PROMPT_OVERHEAD_TOKENS", "1024"))
    LLM_APPROX_CHARS_PER_TOKEN: float = float(os.getenv("LLM_APPROX_CHARS_PER_TOKEN", "3.2"))
    LLM_CHUNK_OVERLAP_CHARS: int = int(os.getenv("LLM_CHUNK_OVERLAP_CHARS", "400"))

    LMSTUDIO_API_BASE: str = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    LMSTUDIO_API_KEY: str = os.getenv("LMSTUDIO_API_KEY", "not-needed")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "vault" / "uploads"))
    PARSED_MARKDOWN_DIR: str = os.getenv(
        "PARSED_MARKDOWN_DIR", str(PROJECT_ROOT / "vault" / "artifacts" / "markdown")
    )
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(20 * 1024 * 1024)))
    INDEXING_CHUNK_SIZE: int = int(os.getenv("INDEXING_CHUNK_SIZE", "1000"))
    INDEXING_CHUNK_OVERLAP: int = int(os.getenv("INDEXING_CHUNK_OVERLAP", "200"))
    OCR_RENDER_SCALE: float = float(os.getenv("OCR_RENDER_SCALE", "2.0"))
    PARSER_MIN_PAGE_TEXT_CHARS: int = int(os.getenv("PARSER_MIN_PAGE_TEXT_CHARS", "80"))
    PARSER_MIN_PAGE_QUALITY_SCORE: float = float(os.getenv("PARSER_MIN_PAGE_QUALITY_SCORE", "0.32"))
    PARSER_MIN_DOCUMENT_TEXT_CHARS: int = int(os.getenv("PARSER_MIN_DOCUMENT_TEXT_CHARS", "300"))
    PARSER_MIN_DOCUMENT_QUALITY_SCORE: float = float(os.getenv("PARSER_MIN_DOCUMENT_QUALITY_SCORE", "0.35"))

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("LLM_RESERVED_OUTPUT_TOKENS", mode="before")
    @classmethod
    def _coerce_empty_reserved_output_tokens(cls, v: object) -> object:
        if v == "" or v is None:
            return 2048
        return v

    @field_validator("LLM_MAX_OUTPUT_TOKENS", mode="before")
    @classmethod
    def _coerce_empty_max_output_tokens(cls, v: object) -> object:
        if v == "" or v is None:
            raw = os.environ.get("LLM_RESERVED_OUTPUT_TOKENS", "")
            if raw == "" or raw is None:
                return 2048
            return int(raw)
        return v


settings = Settings()
