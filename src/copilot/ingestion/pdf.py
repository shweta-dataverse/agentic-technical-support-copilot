"""PDF page extraction (typed successor of the v1 pdf_loader)."""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from copilot.exceptions import IngestionValidationError


def load_pdf_pages(path: Path) -> list[str]:
    """Return the extracted text of every page, empty string for image-only pages."""
    if not path.exists():
        raise IngestionValidationError(f"pdf not found: {path}")
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    if not any(pages):
        raise IngestionValidationError(f"no extractable text in {path.name}")
    return pages
