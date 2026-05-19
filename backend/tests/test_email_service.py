"""Email rendering + delivery tests.

The render tests are pure — they don't hit SMTP. The delivery test sends a
real message to the MailHog container running in the dev stack and queries
its HTTP API to confirm arrival, so it doubles as an end-to-end smoke test
of the SMTP path.

MailHog's URL is hard-coded to its in-network hostname (`mailhog:8025`)
because these tests are designed to be run inside the backend container.
"""

from __future__ import annotations

import time

import httpx
import pytest

from app.services.email_service import (
    SUBJECTS,
    SUPPORTED_LOCALES,
    render_and_send,
    render_email,
)

MAILHOG_API = "http://mailhog:8025/api/v2"


# ---------- render ----------


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
@pytest.mark.parametrize("template", list(SUBJECTS.keys()))
def test_render_email_each_template_each_locale(template: str, locale: str):
    subject, html = render_email(
        template,
        locale,
        {
            "full_name": "Test User",
            "email": "test@example.com",
            "verify_url": "http://example.com/verify",
            "reset_url": "http://example.com/reset",
            "expires_in_hours": 24,
        },
    )
    assert subject == SUBJECTS[template][locale]
    assert "<html" in html.lower()
    # All bodies inherit from _layout.html so they should reference the brand.
    assert "Anjumanlar" in html


def test_render_email_falls_back_to_default_locale_when_unknown():
    subject, html = render_email(
        "welcome",
        "fr",  # unsupported
        {"full_name": "Test", "email": "t@e.com"},
    )
    # Default locale is uz — subject must match the uz entry and the body
    # must contain a uz-only phrase from the template.
    assert subject == SUBJECTS["welcome"]["uz"]
    assert "Saytga kirish" in html


def test_render_email_unknown_template_raises():
    with pytest.raises(KeyError):
        render_email("nonexistent", "uz", {})


# ---------- end-to-end: actually send into MailHog ----------


def _clear_mailhog() -> None:
    """Delete any leftover messages so each test sees a clean inbox."""
    httpx.delete(f"{MAILHOG_API.replace('/v2', '/v1')}/messages", timeout=5).raise_for_status()


def _fetch_to(recipient: str, attempts: int = 10) -> dict | None:
    """Poll the MailHog API for a message addressed to ``recipient``."""
    for _ in range(attempts):
        resp = httpx.get(
            f"{MAILHOG_API}/search", params={"kind": "to", "query": recipient}, timeout=5
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            return items[0]
        time.sleep(0.2)
    return None


def test_render_and_send_delivers_to_mailhog():
    _clear_mailhog()
    recipient = "mailhog-test@example.com"
    render_and_send(
        to=recipient,
        template_name="welcome",
        locale="uz",
        context={"full_name": "MailHog Tester", "email": recipient},
    )
    msg = _fetch_to(recipient)
    assert msg is not None, "MailHog never received the email"

    # MailHog stores parsed headers under Content.Headers; the body itself is
    # base64/quoted-printable encoded so we don't try to substring-match it
    # — render_email tests already cover body correctness.
    headers = msg["Content"]["Headers"]
    # Subject may be RFC 2047 encoded (=?utf-8?b?...?=) for non-ASCII strings,
    # so just check it's present and non-empty.
    assert headers["Subject"][0]
    assert recipient in headers["To"][0]
    assert msg["Content"]["Size"] > 0
