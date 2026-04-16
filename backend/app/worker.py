import app.db.base  # noqa: F401  # Preload ORM models for SQLAlchemy relationship resolution in Celery
from app.celery_app import celery_app
from app.tasks import documents  # noqa: F401

__all__ = ["celery_app"]
