"""Persistence operations shared by the API (sync path) and the worker."""

from __future__ import annotations

from sqlalchemy.orm import Session

from copilot.agents.state import CopilotState
from copilot.db.models import Resolution, Ticket


def upsert_ticket(
    session: Session,
    *,
    ticket_id: str,
    summary: str,
    description: str,
    source: str,
    category: str | None = None,
    severity: str | None = None,
) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        ticket = Ticket(
            ticket_id=ticket_id,
            summary=summary,
            description=description,
            source=source,
        )
        session.add(ticket)
    else:
        ticket.summary = summary
        ticket.description = description
    if category is not None:
        ticket.category = category
    if severity is not None:
        ticket.severity = severity
    # flush so the ticket row exists before dependent rows (resolutions FK)
    session.flush()
    return ticket


def save_resolution(session: Session, state: CopilotState) -> Resolution:
    assert state.synthesis is not None and state.guardrails is not None
    synthesis = state.synthesis
    resolution = Resolution(
        ticket_id=state.ticket_id,
        resolution_steps=list(synthesis.resolution_steps),
        citations=[c.model_dump() for c in synthesis.citations],
        confidence=synthesis.confidence,
        escalate=state.guardrails.escalate,
        escalation_reason="; ".join(state.guardrails.reasons)[:64] or None,
        reasoning_summary=synthesis.reasoning_summary,
        model="",  # filled from prompt_versions/model info below when present
        prompt_version=state.prompt_versions.get("synthesis", ""),
        cost_eur=state.total_cost_eur,
    )
    session.add(resolution)
    return resolution
