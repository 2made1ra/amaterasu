from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI RAG Assistant"
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/app_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123") # Will use env var if available
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

    # LLM & Embeddings Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "huggingface")  # huggingface or lmstudio
    LLM_MODEL: str = os.getenv("LLM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    EMBEDDINGS_PROVIDER: str = os.getenv("EMBEDDINGS_PROVIDER", "huggingface")  # huggingface or lmstudio
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    LMSTUDIO_API_BASE: str = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    LMSTUDIO_API_KEY: str = os.getenv("LMSTUDIO_API_KEY", "not-needed")

    class Config:
        case_sensitive = True

settings = Settings()
