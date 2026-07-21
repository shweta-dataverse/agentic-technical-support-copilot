"""GDPR right-to-be-forgotten: erase a ticket from every serving store.

Order is deliberate: the external store (AI Search) is cleared first, then the
transactional store (Postgres) in one committed transaction. If the index
delete fails, nothing in Postgres has changed yet and the whole operation can
be retried. Every erase is recorded in the audit log. Manual content is not
personal data, so only the tickets index is touched.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from copilot.db.models import AuditLogEntry, Job, Resolution, Ticket
from copilot.exceptions import TicketNotFoundError
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class TicketIndexDeleter(Protocol):
    def delete_ticket(self, ticket_id: str) -> None: ...


class RtbfResult(BaseModel):
    ticket_id: str
    index_deleted: bool
    resolutions_deleted: int
    jobs_scrubbed: int
    ticket_deleted: bool
    audit_logged: bool


def forget_ticket(
    session: Session, deleter: TicketIndexDeleter, *, ticket_id: str, actor: str
) -> RtbfResult:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(f"ticket {ticket_id} not found")

    # 1. external store first (retryable if it fails before any DB change)
    deleter.delete_ticket(ticket_id)

    # 2. Postgres, in one transaction
    resolutions = session.execute(
        select(func.count()).select_from(Resolution).where(Resolution.ticket_id == ticket_id)
    ).scalar_one()

    jobs = list(
        session.execute(select(Job).where(Job.ticket_id == ticket_id)).scalars()
    )
    for job in jobs:
        job.payload = None  # queue payloads can carry ticket text

    session.delete(ticket)  # resolutions cascade-delete via the FK

    session.add(
        AuditLogEntry(
            actor=actor,
            action="rtbf_delete",
            entity_type="ticket",
            entity_id=ticket_id,
            detail={
                "index_deleted": True,
                "resolutions_deleted": int(resolutions),
                "jobs_scrubbed": len(jobs),
            },
        )
    )
    session.commit()
    logger.info(
        "rtbf erase ticket=%s resolutions=%d jobs=%d actor=%s",
        ticket_id,
        resolutions,
        len(jobs),
        actor,
    )
    return RtbfResult(
        ticket_id=ticket_id,
        index_deleted=True,
        resolutions_deleted=int(resolutions),
        jobs_scrubbed=len(jobs),
        ticket_deleted=True,
        audit_logged=True,
    )
