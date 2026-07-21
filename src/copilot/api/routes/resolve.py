"""Synchronous resolution endpoint.

Runs the full agent graph in-request and persists the result. This is the
demo/console path; production traffic uses the async
`POST /v1/tickets/{id}/resolve` → job → worker flow.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from copilot.agents.state import CopilotState
from copilot.api.deps import DbDep, get_resolution_graph, require_api_key
from copilot.api.schemas import CitationOut, ResolutionResponse, TicketRequest
from copilot.db.repository import save_resolution, upsert_ticket

router = APIRouter(prefix="/v1", tags=["resolve"], dependencies=[Depends(require_api_key)])


@router.post("/resolve", response_model=ResolutionResponse)
def resolve(
    ticket: TicketRequest,
    session: DbDep,
    graph: Annotated[Any, Depends(get_resolution_graph)],
) -> ResolutionResponse:
    ticket_id = f"LOCAL-{uuid.uuid4().hex[:8].upper()}"
    raw = graph.invoke(
        CopilotState(
            ticket_id=ticket_id, title=ticket.title, description=ticket.description
        )
    )
    state = CopilotState.model_validate(raw)
    assert state.triage is not None and state.synthesis is not None

    upsert_ticket(
        session,
        ticket_id=ticket_id,
        summary=ticket.title,
        description=ticket.description,
        source="api",
        category=state.triage.category,
        severity=state.triage.severity,
    )
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
