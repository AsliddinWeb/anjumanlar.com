"""Transactional email rendering + sending.

Subjects are kept in a Python dict (one entry per template × locale) — short
strings without much logic. Bodies are Jinja2 HTML templates living under
``app/locale/emails/<locale>/<template>.html``. If a body file is missing
for the requested locale we fall back to ``uz``.

SMTP sending is synchronous (``smtplib``) so it composes cleanly with
Celery's sync worker model; from FastAPI we never call this directly — the
endpoint enqueues a Celery task instead.
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import jinja2

from app.config import settings

# ----- Subjects -----

DEFAULT_LOCALE = "uz"
SUPPORTED_LOCALES = ("uz", "ru", "en")

SUBJECTS: dict[str, dict[str, str]] = {
    "welcome": {
        "uz": "Monografiya'ga xush kelibsiz",
        "ru": "Добро пожаловать в Monografiya",
        "en": "Welcome to Monografiya",
    },
    "verify_email": {
        "uz": "Email manzilingizni tasdiqlang",
        "ru": "Подтвердите ваш email",
        "en": "Verify your email address",
    },
    "password_reset": {
        "uz": "Parolni tiklash",
        "ru": "Сброс пароля",
        "en": "Password reset",
    },
    "library_grant": {
        "uz": "Sotib olingan kitob kutubxonangizga qo'shildi",
        "ru": "Купленная книга добавлена в библиотеку",
        "en": "Your book is in your library",
    },
    "order_paid": {
        "uz": "To'lov muvaffaqiyatli amalga oshdi",
        "ru": "Оплата прошла успешно",
        "en": "Payment received",
    },
    "book_approved": {
        "uz": "Kitobingiz tasdiqlandi",
        "ru": "Книга одобрена",
        "en": "Your book has been approved",
    },
    "book_rejected": {
        "uz": "Kitobingiz rad etildi",
        "ru": "Книга отклонена",
        "en": "Your book was rejected",
    },
    "withdrawal_requested": {
        "uz": "Pul yechish so'rovi qabul qilindi",
        "ru": "Заявка на выплату принята",
        "en": "Withdrawal request received",
    },
    "withdrawal_completed": {
        "uz": "Pul yechish yakunlandi",
        "ru": "Выплата завершена",
        "en": "Withdrawal completed",
    },
    "withdrawal_rejected": {
        "uz": "Pul yechish so'rovi rad etildi",
        "ru": "Заявка на выплату отклонена",
        "en": "Withdrawal request rejected",
    },
    "review_reminder": {
        "uz": "Sotib olgan kitobingiz haqida sharh qoldiring",
        "ru": "Оставьте отзыв о купленной книге",
        "en": "Share your thoughts on the book you bought",
    },
}


# ----- Jinja2 environment -----

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "locale" / "emails"

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=jinja2.select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _resolve_locale(locale: str | None) -> str:
    """Coerce to a supported locale, falling back to the default."""
    if locale and locale in SUPPORTED_LOCALES:
        return locale
    return DEFAULT_LOCALE


def render_email(
    template_name: str,
    locale: str | None,
    context: dict[str, Any],
) -> tuple[str, str]:
    """Return ``(subject, html_body)`` for the given template + locale.

    Raises :class:`KeyError` if the template isn't registered in SUBJECTS.
    Raises :class:`jinja2.TemplateNotFound` if neither the locale-specific
    nor the default-locale body file exists.
    """
    resolved = _resolve_locale(locale)

    if template_name not in SUBJECTS:
        raise KeyError(f"Unknown email template: {template_name!r}")
    subject_map = SUBJECTS[template_name]
    subject = subject_map.get(resolved) or subject_map[DEFAULT_LOCALE]

    try:
        body = _env.get_template(f"{resolved}/{template_name}.html")
    except jinja2.TemplateNotFound:
        body = _env.get_template(f"{DEFAULT_LOCALE}/{template_name}.html")

    full_context = {
        "site_name": settings.EMAIL_FROM_NAME,
        "site_url": settings.FRONTEND_URL,
        **context,
    }
    return subject, body.render(**full_context)


# ----- SMTP -----


def send_email(to: str, subject: str, html: str) -> None:
    """Synchronously deliver an HTML email via SMTP.

    No retry logic here — that's the Celery task's job.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_TLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


def render_and_send(
    to: str,
    template_name: str,
    locale: str | None,
    context: dict[str, Any],
) -> None:
    subject, html = render_email(template_name, locale, context)
    send_email(to, subject, html)
