"""Pure PDF manipulation helpers.

Two operations live here:

- :func:`extract_first_n_pages` — pulls out the first N pages of a PDF
  into a fresh document. Used to build the free demo PDF (default: 10
  pages) that lives in the public ``demos`` bucket.
- :func:`apply_watermark` — overlays a diagonal text watermark on every
  page. Phase 4 uses this to stamp the buyer's email + purchase date
  onto their personal copy of a book before serving it.

Both functions are sync and side-effect free; the Celery tasks in
``app.tasks.pdf_tasks`` wrap them with MinIO + DB I/O.
"""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def extract_first_n_pages(raw: bytes, n: int = 10) -> bytes:
    """Return a new PDF containing only the first ``n`` pages of ``raw``.

    If the source has fewer pages, the result mirrors what's there. We
    never raise on a short PDF — that's the caller's job to gate on
    upload time.
    """
    reader = PdfReader(BytesIO(raw))
    writer = PdfWriter()
    page_count = min(n, len(reader.pages))
    for i in range(page_count):
        writer.add_page(reader.pages[i])
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _build_watermark_overlay(text: str, page_width: float, page_height: float) -> bytes:
    """Single-page PDF that we'll merge over every page of the original."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    c.saveState()
    # ~30% opacity grey, diagonal across the page.
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.25)
    c.setFont("Helvetica", 40)
    c.translate(page_width / 2, page_height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()
    return buf.getvalue()


def apply_watermark(raw: bytes, text: str) -> bytes:
    """Stamp ``text`` diagonally across every page of ``raw``.

    The overlay is built once per output page size — fast for the common
    case of a fixed-layout monograph.
    """
    reader = PdfReader(BytesIO(raw))
    writer = PdfWriter()

    cache: dict[tuple[float, float], bytes] = {}
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        key = (round(width, 2), round(height, 2))
        if key not in cache:
            cache[key] = _build_watermark_overlay(text, width, height)
        overlay_page = PdfReader(BytesIO(cache[key])).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


__all__ = ["A4", "apply_watermark", "extract_first_n_pages"]
