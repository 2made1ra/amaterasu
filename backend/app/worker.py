from app.celery_app import celery_app
from app.tasks import documents  # noqa: F401

__all__ = ["celery_app"]
