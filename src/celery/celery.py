from celery import Celery
from src.celery.config import celery_settings

celery_app = Celery(
    "audio_processor",
    broker=celery_settings.CELERY_BROKER_URL,
    backend=celery_settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.audio"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_queues=celery_settings.CELERY_TASK_QUEUES,
    task_routes=celery_settings.CELERY_TASK_ROUTES,
)
