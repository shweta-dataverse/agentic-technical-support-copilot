"""Manual ingestion pipeline: the hot-path single-document entry point.

Order matters and is deliberate:
  load → chunk → MASK → quality-check → embed → upsert → registry

Masking precedes embedding/indexing because PII baked into a vector index
cannot be selectively removed. The registry check makes whole-document
ingestion idempotent (content hash), and deterministic chunk IDs make the
index upsert idempotent (re-runs overwrite).

Dependencies are injected as protocols so the pipeline is testable without
Azure or Postgres.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from copilot.config import get_settings
from copilot.db.models import DocumentRegistryEntry
from copilot.exceptions import IngestionValidationError
from copilot.ingestion.chunking import Chunk, chunk_pages
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class Masker(Protocol):
    def mask(self, text: str) -> str: ...


class Indexer(Protocol):
    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> int: ...


class RejectedChunk(BaseModel):
    chunk_id: str
    page: int
    reason: str


class IngestReport(BaseModel):
    doc_id: str
    skipped_unchanged: bool = False
    pages: int = 0
    chunks_total: int = 0
    chunks_indexed: int = 0
    rejected: list[RejectedChunk] = []

    @property
    def reject_rate(self) -> float:
        return len(self.rejected) / self.chunks_total if self.chunks_total else 0.0


def _quality_reason(content: str, min_chars: int) -> str | None:
    stripped = content.strip()
    if len(stripped) < min_chars:
        return f"too short ({len(stripped)} chars)"
    alpha = sum(c.isalnum() for c in stripped) / len(stripped)
    if alpha < 0.3:
        return f"low text ratio ({alpha:.2f})"
    return None


class ManualIngestionPipeline:
    def __init__(
        self, *, masker: Masker, embedder: Embedder, indexer: Indexer, session: Session
    ) -> None:
        self._masker = masker
        self._embedder = embedder
        self._indexer = indexer
        self._session = session

    def ingest(self, path: Path, pages: list[str]) -> IngestReport:
        settings = get_settings()
        doc_id = path.stem
        content_hash = hashlib.sha256("\n".join(pages).encode()).hexdigest()

        registry_entry = self._session.get(DocumentRegistryEntry, doc_id)
        if registry_entry is not None and registry_entry.content_hash == content_hash:
            logger.info("document %s unchanged, skipping", doc_id)
            return IngestReport(doc_id=doc_id, skipped_unchanged=True)

        report = IngestReport(doc_id=doc_id, pages=len(pages))
        chunks = chunk_pages(doc_id, path.name, pages)
        report.chunks_total = len(chunks)

        accepted: list[Chunk] = []
        for chunk in chunks:
            masked = self._masker.mask(chunk.content)
            reason = _quality_reason(masked, settings.chunk_min_chars)
            if reason is not None:
                report.rejected.append(
                    RejectedChunk(chunk_id=chunk.chunk_id, page=chunk.page, reason=reason)
                )
                continue
            accepted.append(chunk.model_copy(update={"content": masked}))

        if report.reject_rate > settings.ingest_max_reject_rate:
            raise IngestionValidationError(
                f"reject rate {report.reject_rate:.0%} exceeds "
                f"{settings.ingest_max_reject_rate:.0%} for {doc_id}"
            )

        vectors = self._embedder.embed([c.content for c in accepted])
        report.chunks_indexed = self._indexer.upsert(accepted, vectors)

        self._upsert_registry(doc_id, path, content_hash, len(pages), len(accepted))
        self._session.commit()
        logger.info(
            "ingested %s: %d/%d chunks indexed, %d rejected",
            doc_id,
            report.chunks_indexed,
            report.chunks_total,
            len(report.rejected),
        )
        return report

    def _upsert_registry(
        self, doc_id: str, path: Path, content_hash: str, pages: int, chunks: int
    ) -> None:
        entry = self._session.execute(
            select(DocumentRegistryEntry).where(DocumentRegistryEntry.doc_id == doc_id)
        ).scalar_one_or_none()
        if entry is None:
            entry = DocumentRegistryEntry(doc_id=doc_id, title=path.name, source_path=str(path))
            self._session.add(entry)
        entry.content_hash = content_hash
        entry.page_count = pages
        entry.chunk_count = chunks
        entry.status = "indexed"
