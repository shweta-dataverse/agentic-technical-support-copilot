"""Worker handler tests: saga ordering, masking, job transitions, failure paths."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from copilot.db.models import Job, Ticket
from copilot.exceptions import RetrievalError, TicketNotFoundError
from copilot.worker import handle_ticket_ingest, handle_ticket_resolve
from tests.conftest import TEST_SYNTHESIS, FakeDb, FakeGraph


class FakeMasker:
    def mask(self, text: str) -> str:
        return text.replace("mail@example.com", "<EMAIL_ADDRESS>")


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 4 for _ in texts]


class FakeTicketIndexer:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.upserts: list[str] = []

    def upsert_ticket(self, *, ticket_id: str, **_kwargs: Any) -> None:
        if self.fail:
            raise RetrievalError("index down")
        self.upserts.append(ticket_id)


INGEST_PAYLOAD = {
    "ticket_id": "SUP-100",
    "summary": "CPU STOP, contact mail@example.com",
    "description": "SF LED on",
    "event": "jira:issue_created",
}


def test_ingest_masks_stores_and_indexes() -> None:
    session = FakeDb()
    indexer = FakeTicketIndexer()
    handle_ticket_ingest(
        session.as_session(),
        INGEST_PAYLOAD,
        masker=FakeMasker(),
        embedder=FakeEmbedder(),
        indexer=indexer,
    )
    ticket = session.added[0]
    assert isinstance(ticket, Ticket)
    assert "<EMAIL_ADDRESS>" in ticket.summary
    assert "mail@example.com" not in ticket.summary
    assert session.committed
    assert indexer.upserts == ["SUP-100"]


def test_ingest_index_failure_leaves_ticket_stored() -> None:
    """Saga invariant: stored-but-not-indexed is legal, the reverse is not."""
    session = FakeDb()
    with pytest.raises(RetrievalError):
        handle_ticket_ingest(
            session.as_session(),
            INGEST_PAYLOAD,
            masker=FakeMasker(),
            embedder=FakeEmbedder(),
            indexer=FakeTicketIndexer(fail=True),
        )
    assert session.committed  # postgres write survived; redelivery re-indexes


def make_job_and_ticket(session: FakeDb) -> Job:
    job = Job(job_type="resolve", status="queued", ticket_id="SUP-1")
    job.id = uuid.uuid4()
    session.objects[(Job, job.id)] = job
    ticket = Ticket(
        ticket_id="SUP-1", summary="CPU STOP", description="SF LED", status="open",
        source="webhook",
    )
    session.objects[(Ticket, "SUP-1")] = ticket
    return job


def test_resolve_success_persists_and_completes_job() -> None:
    session = FakeDb()
    job = make_job_and_ticket(session)
    handle_ticket_resolve(
        session.as_session(), {"job_id": str(job.id), "ticket_id": "SUP-1"}, graph=FakeGraph()
    )
    assert job.status == "done"
    assert job.started_at is not None and job.finished_at is not None
    resolution = session.added[-1]
    assert resolution.confidence == TEST_SYNTHESIS["confidence"]
    ticket = session.objects[(Ticket, "SUP-1")]
    assert ticket.category == "configuration"  # triage labels written back


class ExplodingGraph:
    def invoke(self, state: Any, config: Any = None) -> dict[str, Any]:
        raise RetrievalError("search down")


def test_resolve_failure_marks_job_failed_and_reraises() -> None:
    session = FakeDb()
    job = make_job_and_ticket(session)
    with pytest.raises(RetrievalError):
        handle_ticket_resolve(
            session.as_session(),
            {"job_id": str(job.id), "ticket_id": "SUP-1"},
            graph=ExplodingGraph(),
        )
    assert job.status == "failed"
    assert job.error_class == "RetrievalError"  # class only, never the message


def test_resolve_unknown_job_raises() -> None:
    session = FakeDb()
    with pytest.raises(TicketNotFoundError):
        handle_ticket_resolve(
            session.as_session(),
            {"job_id": str(uuid.uuid4()), "ticket_id": "SUP-1"},
            graph=FakeGraph(),
        )
