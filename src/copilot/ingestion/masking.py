"""
Masks PII with Presidio. Runs before embedding or indexing, since a vector cannot be un-masked
later.
"""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
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

# pin the spaCy model we install; Presidio otherwise defaults to
# en_core_web_lg, which is not in the image (works locally, fails in prod).
# The medium model has good name detection without over-flagging technical
# codes (the small model tags things like "0x2521" as a PERSON).
_NLP_CONFIG = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_md"}],
}


class PiiMasker:
    """Detects PII spans and replaces them with <ENTITY_TYPE> placeholders."""

    def __init__(self) -> None:
        nlp_engine = NlpEngineProvider(nlp_configuration=_NLP_CONFIG).create_engine()
        self._analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
        self._anonymizer = AnonymizerEngine()  # type: ignore[no-untyped-call]

    def mask(self, text: str) -> str:
        results = self._analyzer.analyze(text=text, entities=_ENTITIES, language="en")
        if not results:
            return text
        anonymized = self._anonymizer.anonymize(
            text=text,
            analyzer_results=results, # type: ignore[arg-type]  # same shape, two packages
        )
        return str(anonymized.text)
