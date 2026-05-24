"""Celery application factory.

Celery is wired to Redis: one database for the broker (queue), another for
results. Tasks live in modules listed in `include` — autodiscovery via
`autodiscover_tasks` is not used because we'd rather keep the import graph
explicit and fail fast on a typo.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "monografiya",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.order_tasks",
        "app.tasks.pdf_tasks",
        "app.tasks.search_tasks",
    ],
)

celery_app.conf.update(
    timezone=settings.TZ,
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    task_default_retry_delay=60,
    task_track_started=True,
    beat_schedule={
        "orders.expire_pending": {
            "task": "orders.expire_pending",
            # Every minute — worst-case lag past the 30-min TTL is 60s.
            "schedule": crontab(minute="*"),
        },
    },
)
