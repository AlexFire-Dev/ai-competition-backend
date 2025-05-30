import os
from celery import Celery
from celery.schedules import crontab


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")
broker_url = f"redis://{redis_host}:{redis_port}/0"

celery_app = Celery(
    "coursebackend",
    broker=broker_url,
    backend=broker_url,
)

celery_app.conf.beat_schedule = {
    "expire-old-lobbies-every-minute": {
        "task": "app.tasks.expire_old_lobbies",
        "schedule": crontab(minute="*"),
    },
}
celery_app.conf.timezone = "UTC"

celery_app.autodiscover_tasks(["app.services.tasks"])
