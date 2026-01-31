from kombu import Queue

from src.core.config import settings


class CelerySettings:
    """
    Define all settings for Celery.

    Attributes:
        CELERY_BROKER_URL (str): The URL of the message broker used by Celery. Loaded from `settings.REDIS_URL`.
        CELERY_RESULT_BACKEND (str): The backend URL for storing task results. Loaded from `settings.REDIS_URL`.
        CELERY_TASK_QUEUES (tuple[Queue, ...]): A tuple of queues configured for Celery tasks.
            Includes a queue named "audio_processing" with its exchange and routing key.
        CELERY_TASK_ROUTES (dict[str, dict[str, str]]): A dictionary mapping task names to specific queues.
            Ensures tasks under "src.tasks.audio.*" are routed to the "audio_processing" queue.
    """

    CELERY_BROKER_URL: str = settings.REDIS_URL
    CELERY_RESULT_BACKEND: str = settings.REDIS_URL

    CELERY_TASK_QUEUES: tuple[Queue, ...] = (
        Queue(
            "audio_processing",
            exchange="audio_processing",
            routing_key="audio_processing",
        ),
    )

    CELERY_TASK_ROUTES: dict[str, dict[str, str]] = {
        "src.tasks.audio.*": {"queue": "audio_processing"},
    }


celery_settings = CelerySettings()
