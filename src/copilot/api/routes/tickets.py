"""Ticket read models and async resolution enqueueing."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from copilot.api.deps import (
    DbDep,
    PublisherDep,
    SettingsDep,
    get_tickets_indexer,
    require_api_key,
)
from copilot.api.middleware import get_correlation_id
from copilot.api.schemas import JobAcceptedResponse, ResolutionResponse, TicketResponse
from copilot.db.models import Job, Resolution, Ticket
from copilot.exceptions import TicketNotFoundError
from copilot.gdpr import RtbfResult, forget_ticket

router = APIRouter(
    prefix="/v1/tickets", tags=["tickets"], dependencies=[Depends(require_api_key)]
)


def _get_ticket(session: DbDep, ticket_id: str) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(f"ticket {ticket_id} not found")
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: str, session: DbDep) -> TicketResponse:
    ticket = _get_ticket(session, ticket_id)
    return TicketResponse(
        ticket_id=ticket.ticket_id,
        summary=ticket.summary,
        description=ticket.description,
        category=ticket.category,
        severity=ticket.severity,
        status=ticket.status,
        source=ticket.source,
        created_at=ticket.created_at,
    )


@router.get("/{ticket_id}/resolution", response_model=ResolutionResponse)
def get_resolution(ticket_id: str, session: DbDep) -> ResolutionResponse:
    _get_ticket(session, ticket_id)
    resolution = session.execute(
        select(Resolution)
        .where(Resolution.ticket_id == ticket_id)
        .order_by(Resolution.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if resolution is None:
        raise TicketNotFoundError(f"no resolution stored for ticket {ticket_id}")
    return ResolutionResponse(
        ticket_id=ticket_id,
        resolution_steps=list(resolution.resolution_steps),
        citations=list(resolution.citations),
        confidence=resolution.confidence,
        escalate=resolution.escalate,
        reasoning_summary=resolution.reasoning_summary or "",
        model=resolution.model,
        cost_eur=float(resolution.cost_eur) if resolution.cost_eur is not None else None,
    )


@router.post(
    "/{ticket_id}/resolve",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobAcceptedResponse,
)
def enqueue_resolution(
    ticket_id: str, session: DbDep, settings: SettingsDep, publisher: PublisherDep
) -> JobAcceptedResponse:
    _get_ticket(session, ticket_id)
    job = Job(job_type="resolve", status="queued", ticket_id=ticket_id)
    session.add(job)
    session.commit()
    publisher.publish(
        settings.queue_ticket_resolve,
        {"job_id": str(job.id), "ticket_id": ticket_id},
        correlation_id=get_correlation_id(),
    )
    return JobAcceptedResponse(job_id=job.id)


@router.delete("/{ticket_id}", response_model=RtbfResult)
def delete_ticket(
    ticket_id: str,
    session: DbDep,
    key_id: Annotated[str, Depends(require_api_key)],
    deleter: Annotated[Any, Depends(get_tickets_indexer)],
) -> RtbfResult:
    """GDPR right-to-be-forgotten: erase the ticket from all serving stores."""
    return forget_ticket(session, deleter, ticket_id=ticket_id, actor=f"api-key:{key_id}")
