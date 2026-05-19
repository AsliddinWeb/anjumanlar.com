"""Celery tasks that render + dispatch transactional emails.

A FastAPI endpoint should never call ``email_service`` directly. Enqueue
``send_template_email`` instead so the request stays fast and SMTP hiccups
don't fail the user-facing call.
"""

from __future__ import annotations

import logging
from typing import Any

from celery.exceptions import MaxRetriesExceededError

from app.services.email_service import render_and_send
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="email.send_template",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(OSError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
)
def send_template_email(
    self,
    to: str,
    template_name: str,
    locale: str | None,
    context: dict[str, Any],
) -> str:
    """Render the template + ship it. Returns the recipient on success."""
    try:
        render_and_send(to=to, template_name=template_name, locale=locale, context=context)
    except MaxRetriesExceededError:
        logger.exception("email.send_template gave up: to=%s template=%s", to, template_name)
        raise
    logger.info("email.send_template delivered: to=%s template=%s", to, template_name)
    return to
