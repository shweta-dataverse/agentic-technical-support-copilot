"""Ticket read models and async resolution enqueueing."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select

from copilot.agents.state import CopilotState
from copilot.api.deps import (
    DbDep,
    PublisherDep,
    SettingsDep,
    get_resolution_graph,
    get_tickets_indexer,
    require_api_key,
)
from copilot.api.middleware import get_correlation_id
from copilot.api.schemas import (
    CitationOut,
    JobAcceptedResponse,
    ResolutionResponse,
    SeedResponse,
    TicketListItem,
    TicketResponse,
)
from copilot.db.models import Job, Resolution, Ticket
from copilot.db.repository import save_resolution
from copilot.exceptions import TicketNotFoundError
from copilot.gdpr import RtbfResult, forget_ticket

router = APIRouter(
    prefix="/v1/tickets", tags=["tickets"], dependencies=[Depends(require_api_key)]
)

# realistic S7-1500 tickets used to populate the demo queue
# (id, summary, category, severity, description)
_SAMPLE_TICKETS = [
    (
        "DEMO-1", "CPU goes to STOP after firmware update", "hardware", "high",
        "After updating the CPU firmware to V2.9 the CPU enters STOP with the SF LED on.",
    ),
    (
        "DEMO-2", "ET 200MP modules show red error LEDs after IM firmware update",
        "firmware", "high",
        "Several ET 200MP I/O modules show red error LEDs after the interface module update.",
    ),
    (
        "DEMO-3", "Startup inhibit 0x2521, hardware configuration inconsistent",
        "configuration", "critical",
        "After a module replacement the CPU will not enter RUN and reports startup "
        "inhibit 0x2521; the physical module revision differs from the project.",
    ),
    (
        "DEMO-4", "Power supply SF LED flashing, modules to the right switched off",
        "hardware", "medium",
        "The system power supply SF LED is flashing and modules to its right are off.",
    ),
    (
        "DEMO-5", "Replacing a digital input module and its front connector coding",
        "hardware", "medium",
        "How do we handle the mechanical coding element and the existing front connector?",
    ),
    (
        "DEMO-6", "How to perform a CPU memory reset with the mode selector",
        "configuration", "low",
        "We need to perform a memory reset on the CPU using the mode selector.",
    ),
]


def _get_ticket(session: DbDep, ticket_id: str) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(f"ticket {ticket_id} not found")
    return ticket


@router.get("", response_model=list[TicketListItem])
def list_tickets(
    session: DbDep, status_filter: str | None = None, limit: int = 50
) -> list[TicketListItem]:
    query = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    tickets = list(session.execute(query).scalars().all())
    resolved_ids = {
        row for row in session.execute(select(Resolution.ticket_id)).scalars().all()
    }
    return [
        TicketListItem(
            ticket_id=t.ticket_id,
            summary=t.summary,
            category=t.category,
            severity=t.severity,
            status=t.status,
            source=t.source,
            created_at=t.created_at,
            resolved=t.ticket_id in resolved_ids,
        )
        for t in tickets
    ]


@router.post("/seed", response_model=SeedResponse)
def seed_tickets(session: DbDep) -> SeedResponse:
    """Insert the sample ticket queue (idempotent) for the demo dashboard."""
    created = 0
    for ticket_id, summary, category, severity, description in _SAMPLE_TICKETS:
        if session.get(Ticket, ticket_id) is None:
            session.add(
                Ticket(
                    ticket_id=ticket_id,
                    summary=summary,
                    description=description,
                    category=category,
                    severity=severity,
                    status="open",
                    source="seed",
                )
            )
            created += 1
    session.commit()
    total = int(
        session.execute(select(func.count()).select_from(Ticket)).scalar_one()
    )
    return SeedResponse(created=created, total=total)


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


@router.post("/{ticket_id}/resolve-now", response_model=ResolutionResponse)
def resolve_now(
    ticket_id: str,
    session: DbDep,
    graph: Annotated[Any, Depends(get_resolution_graph)],
) -> ResolutionResponse:
    """Resolve an existing ticket in-request (used by the console)."""
    ticket = _get_ticket(session, ticket_id)
    raw = graph.invoke(
        CopilotState(
            ticket_id=ticket_id, title=ticket.summary, description=ticket.description
        )
    )
    state = CopilotState.model_validate(raw)
    assert state.triage is not None and state.synthesis is not None

    ticket.category = state.triage.category
    ticket.severity = state.triage.severity
    ticket.status = "resolved"
    save_resolution(session, state)
    session.commit()

    return ResolutionResponse(
        ticket_id=ticket_id,
        resolution_steps=state.synthesis.resolution_steps,
        citations=[CitationOut(**c.model_dump()) for c in state.synthesis.citations],
        confidence=state.synthesis.confidence,
        escalate=state.guardrails.escalate if state.guardrails else False,
        reasoning_summary=state.synthesis.reasoning_summary,
        category=state.triage.category,
        severity=state.triage.severity,
        cost_eur=state.total_cost_eur,
    )


@router.delete("/{ticket_id}", response_model=RtbfResult)
def delete_ticket(
    ticket_id: str,
    session: DbDep,
    key_id: Annotated[str, Depends(require_api_key)],
    deleter: Annotated[Any, Depends(get_tickets_indexer)],
) -> RtbfResult:
    """GDPR right-to-be-forgotten: erase the ticket from all serving stores."""
    return forget_ticket(session, deleter, ticket_id=ticket_id, actor=f"api-key:{key_id}")
