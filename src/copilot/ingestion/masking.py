"""PII masking with Microsoft Presidio.

Masking happens BEFORE embedding, indexing, logging, or any persistence —
once PII reaches a vector index it cannot be selectively removed, so the
only safe point to strip it is the pipeline entrance.
"""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# entities relevant to support tickets and manual excerpts
_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IP_ADDRESS",
    "IBAN_CODE",
    "CREDIT_CARD",
]


class PiiMasker:
    """Detects PII spans and replaces them with <ENTITY_TYPE> placeholders."""

    def __init__(self) -> None:
        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()  # type: ignore[no-untyped-call]

    def mask(self, text: str) -> str:
        results = self._analyzer.analyze(text=text, entities=_ENTITIES, language="en")
        if not results:
            return text
        anonymized = self._anonymizer.anonymize(
            text=text,
            analyzer_results=results,  # type: ignore[arg-type]  # same shape, two packages
        )
        return str(anonymized.text)
