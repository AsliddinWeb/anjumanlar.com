"""Unit tests for ``pdf_service`` — pure-function PDF manipulation.

End-to-end demo generation via Celery is covered in test_book_uploads.py
(marked ``@integration``).
"""

from __future__ import annotations

import io

import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services import pdf_service


def _make_pdf(pages: int = 15) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for i in range(pages):
        c.drawString(72, 800, f"Source page {i + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


# ---------- extract_first_n_pages ----------


def test_extract_returns_first_n_pages():
    src = _make_pdf(pages=15)
    out = pdf_service.extract_first_n_pages(src, n=10)
    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 10


def test_extract_caps_at_source_length():
    src = _make_pdf(pages=3)
    out = pdf_service.extract_first_n_pages(src, n=10)
    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 3


def test_extract_one_page():
    src = _make_pdf(pages=5)
    out = pdf_service.extract_first_n_pages(src, n=1)
    assert len(PdfReader(io.BytesIO(out)).pages) == 1


def test_extract_result_is_smaller_than_source():
    src = _make_pdf(pages=20)
    out = pdf_service.extract_first_n_pages(src, n=5)
    # 5 pages should always be lighter than 20 — sanity check that we're
    # not just copying the whole file.
    assert len(out) < len(src)


# ---------- apply_watermark ----------


def test_watermark_preserves_page_count():
    src = _make_pdf(pages=7)
    out = pdf_service.apply_watermark(src, "BUYER@example.com · 2026-05-21")
    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 7


def test_watermark_changes_bytes():
    """Two PDFs with the same content but different watermarks should
    differ — proves we're actually stamping something."""
    src = _make_pdf(pages=3)
    a = pdf_service.apply_watermark(src, "alice@example.com")
    b = pdf_service.apply_watermark(src, "bob@example.com")
    assert a != b
    assert a != src


@pytest.mark.parametrize("page_count", [1, 5, 25])
def test_watermark_works_across_page_counts(page_count: int):
    src = _make_pdf(pages=page_count)
    out = pdf_service.apply_watermark(src, "demo")
    assert len(PdfReader(io.BytesIO(out)).pages) == page_count
