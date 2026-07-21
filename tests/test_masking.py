"""Presidio masking tests, require the spaCy model (installed via make install)."""

from __future__ import annotations

import pytest

from copilot.ingestion.masking import PiiMasker


@pytest.fixture(scope="module")
def masker() -> PiiMasker:
    return PiiMasker()


def test_masks_email_and_phone(masker: PiiMasker) -> None:
    text = "Contact Hans Mueller at hans.mueller@example.com or +49 170 1234567."
    masked = masker.mask(text)
    assert "hans.mueller@example.com" not in masked
    assert "<EMAIL_ADDRESS>" in masked


def test_preserves_technical_content(masker: PiiMasker) -> None:
    text = "CPU 1516-3 reports startup inhibit 0x2521 after firmware V4.4 update."
    masked = masker.mask(text)
    assert "0x2521" in masked
    assert "V4.4" in masked
