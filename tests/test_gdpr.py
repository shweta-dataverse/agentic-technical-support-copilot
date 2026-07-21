"""GDPR right-to-be-forgotten tests: erase from every store, audit, ordering."""

from __future__ import annotations

from typing import Any

import pytest

from copilot.db.models import AuditLogEntry, Job, Ticket
from copilot.exceptions import RetrievalError, TicketNotFoundError
from copilot.gdpr import forget_ticket
from tests.conftest import FakeDb


class FakeDeleter:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.deleted: list[str] = []

    def delete_ticket(self, ticket_id: str) -> None:
        if self.fail:
            raise RetrievalError("index unavailable")
        self.deleted.append(ticket_id)


class RtbfDb(FakeDb):
    """FakeDb plus the query surface forget_ticket needs."""

    def __init__(self) -> None:
        super().__init__()
        self.deleted: list[Any] = []
        self.resolution_count = 0
        self.jobs: list[Job] = []

    def execute(self, stmt: Any) -> Any:
        text = str(stmt).lower()
        parent = self

        class _Result:
            def scalar_one(self) -> int:
                return parent.resolution_count

            def scalars(self) -> list[Job]:
                return parent.jobs

        return _Result() if "count" in text or "job" in text else super().execute(stmt)

    def delete(self, obj: Any) -> None:
        self.deleted.append(obj)


def make_db(ticket_id: str = "SUP-1", resolutions: int = 2) -> RtbfDb:
    db = RtbfDb()
    db.objects[(Ticket, ticket_id)] = Ticket(
        ticket_id=ticket_id, summary="s", description="d", status="open", source="webhook"
    )
    db.resolution_count = resolutions
    return db


def test_forget_erases_from_index_and_postgres_and_audits() -> None:
    db = make_db(resolutions=2)
    deleter = FakeDeleter()
    result = forget_ticket(db.as_session(), deleter, ticket_id="SUP-1", actor="api-key:x")

    assert deleter.deleted == ["SUP-1"]  # removed from search index
    assert any(isinstance(o, Ticket) for o in db.deleted)  # removed from postgres
    assert result.resolutions_deleted == 2
    assert result.index_deleted and result.ticket_deleted and result.audit_logged
    assert db.committed
    assert any(isinstance(o, AuditLogEntry) for o in db.added)  # audit trail written


def test_forget_scrubs_job_payloads() -> None:
    db = make_db()
    job = Job(job_type="resolve", status="done", ticket_id="SUP-1")
    job.payload = {"summary": "personal text"}
    db.jobs = [job]
    forget_ticket(db.as_session(), FakeDeleter(), ticket_id="SUP-1", actor="x")
    assert job.payload is None


def test_forget_unknown_ticket_raises() -> None:
    db = RtbfDb()
    with pytest.raises(TicketNotFoundError):
        forget_ticket(db.as_session(), FakeDeleter(), ticket_id="NOPE", actor="x")


def test_forget_aborts_postgres_when_index_delete_fails() -> None:
    """Index first: if it fails, Postgres is untouched and the op is retryable."""
    db = make_db()
    with pytest.raises(RetrievalError):
        forget_ticket(db.as_session(), FakeDeleter(fail=True), ticket_id="SUP-1", actor="x")
    assert not db.deleted  # nothing deleted from postgres
    assert not db.committed
