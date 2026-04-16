from celery import Celery
from kombu import Queue

from app.core.config import settings


celery_app = Celery(
    "amaterasu",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_default_queue=settings.CELERY_HIGH_PRIORITY_QUEUE,
    task_queues=(
        Queue(settings.CELERY_HIGH_PRIORITY_QUEUE),
        Queue(settings.CELERY_BULK_QUEUE),
    ),
    task_ignore_result=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

celery_app.autodiscover_tasks(["app.tasks"])
