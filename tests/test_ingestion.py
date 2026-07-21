"""Ingestion unit tests: deterministic chunking, masking, pipeline behavior.

The pipeline runs against fakes — no Azure, no Postgres. The registry uses a
minimal in-memory stand-in for the Session surface the pipeline touches.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from copilot.db.models import DocumentRegistryEntry
from copilot.exceptions import IngestionValidationError
from copilot.ingestion.chunking import Chunk, chunk_pages, make_chunk_id
from copilot.ingestion.pipeline import IngestReport, ManualIngestionPipeline

# ---------------------------------------------------------------------------
# chunking
# ---------------------------------------------------------------------------


def test_chunk_ids_are_deterministic() -> None:
    assert make_chunk_id("doc", 3, 0) == make_chunk_id("doc", 3, 0)
    assert make_chunk_id("doc", 3, 0) != make_chunk_id("doc", 3, 1)


def test_chunking_preserves_page_numbers() -> None:
    pages = ["alpha " * 50, "beta " * 50]
    chunks = chunk_pages("doc", "Doc.pdf", pages)
    assert {c.page for c in chunks} == {1, 2}
    # re-chunking the same input yields identical ids
    again = chunk_pages("doc", "Doc.pdf", pages)
    assert [c.chunk_id for c in chunks] == [c.chunk_id for c in again]


# ---------------------------------------------------------------------------
# pipeline fakes
# ---------------------------------------------------------------------------


class FakeMasker:
    def mask(self, text: str) -> str:
        return text.replace("john@siemens.example", "<EMAIL_ADDRESS>")


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.0] * 4 for _ in texts]


class FakeIndexer:
    def __init__(self) -> None:
        self.upserted: dict[str, str] = {}

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> int:
        for chunk in chunks:
            self.upserted[chunk.chunk_id] = chunk.content
        return len(chunks)


class FakeSession:
    """Implements the narrow Session surface the pipeline uses."""

    def __init__(self) -> None:
        self.entries: dict[str, DocumentRegistryEntry] = {}
        self.committed = False

    def get(self, _model: type, doc_id: str) -> DocumentRegistryEntry | None:
        return self.entries.get(doc_id)

    def execute(self, _stmt: Any) -> Any:
        session = self

        class _Result:
            def scalar_one_or_none(self) -> DocumentRegistryEntry | None:
                return next(iter(session.entries.values()), None)

        return _Result()

    def add(self, entry: DocumentRegistryEntry) -> None:
        self.entries[entry.doc_id] = entry

    def commit(self) -> None:
        self.committed = True


def make_pipeline(
    session: FakeSession | None = None,
) -> tuple[ManualIngestionPipeline, FakeEmbedder, FakeIndexer, FakeSession]:
    session = session or FakeSession()
    embedder = FakeEmbedder()
    indexer = FakeIndexer()
    pipeline = ManualIngestionPipeline(
        masker=FakeMasker(),
        embedder=embedder,
        indexer=indexer,
        session=session,  # type: ignore[arg-type]  # narrow fake of Session
    )
    return pipeline, embedder, indexer, session


PAGES = ["Startup inhibit 0x2521 diagnostics. " * 20, "Contact john@siemens.example now. " * 20]


def test_pipeline_masks_before_embedding_and_indexing() -> None:
    pipeline, embedder, indexer, _ = make_pipeline()
    pipeline.ingest(Path("manual.pdf"), PAGES)
    embedded_text = " ".join(t for batch in embedder.calls for t in batch)
    indexed_text = " ".join(indexer.upserted.values())
    assert "john@siemens.example" not in embedded_text
    assert "john@siemens.example" not in indexed_text
    assert "<EMAIL_ADDRESS>" in indexed_text


def test_pipeline_rerun_is_idempotent() -> None:
    pipeline, _, indexer, session = make_pipeline()
    first = pipeline.ingest(Path("manual.pdf"), PAGES)
    assert first.chunks_indexed > 0
    count_after_first = len(indexer.upserted)

    second = pipeline.ingest(Path("manual.pdf"), PAGES)
    assert second.skipped_unchanged  # registry hash short-circuits
    assert len(indexer.upserted) == count_after_first


def test_pipeline_reindexes_changed_document() -> None:
    pipeline, _, _, session = make_pipeline()
    pipeline.ingest(Path("manual.pdf"), PAGES)
    changed = [PAGES[0], PAGES[1] + " new revision content added here."]
    report = pipeline.ingest(Path("manual.pdf"), changed)
    assert not report.skipped_unchanged
    assert report.chunks_indexed > 0


def test_pipeline_rejects_garbage_chunks() -> None:
    pipeline, _, _, _ = make_pipeline()
    # one garbage page among six keeps the reject rate under the 20% hard gate
    pages = ["Real content about S7-1500 module diagnostics. " * 20] * 5
    pages.append(".... ---- ....  " * 20)
    report = pipeline.ingest(Path("manual.pdf"), pages)
    assert report.rejected
    assert all(r.page == 6 for r in report.rejected)


def test_pipeline_fails_on_excessive_reject_rate() -> None:
    pipeline, _, _, _ = make_pipeline()
    garbage_pages = ["--- ... --- " * 30 for _ in range(5)]
    with pytest.raises(IngestionValidationError):
        pipeline.ingest(Path("manual.pdf"), garbage_pages)


def test_report_reject_rate() -> None:
    report = IngestReport(doc_id="d", chunks_total=10)
    assert report.reject_rate == 0.0
