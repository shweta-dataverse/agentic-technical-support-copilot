# ticket-resolution endpoint.
#
# Phase 1: builds a single grounded prompt and calls the configured LLM
# provider directly. In Phase 2 the body of `draft_resolution` is replaced by
# the LangGraph multi-agent pipeline (hybrid retrieval -> knowledge -> synthesis)
# without changing this route's contract.

from __future__ import annotations

from fastapi import APIRouter, Depends

from copilot.api.deps import LLMProviderDep, require_api_key
from copilot.api.schemas import ResolutionResponse, TicketRequest
from copilot.llm.providers.base import LLMProvider

router = APIRouter(prefix="/v1", tags=["resolve"], dependencies=[Depends(require_api_key)])

SYSTEM_PROMPT = (
    "You are an expert technical-support engineer for Siemens SIMATIC S7-1500 "
    "industrial automation systems. Draft clear, safe, step-by-step resolutions "
    "for support tickets. If you are unsure, say so explicitly rather than guessing."
)


def draft_resolution(ticket: TicketRequest, llm: LLMProvider) -> ResolutionResponse:
    prompt = (
        f"Ticket title: {ticket.title}\n"
        f"Ticket description: {ticket.description}\n\n"
        "Draft a concise, actionable resolution."
    )
    result = llm.generate(prompt, system=SYSTEM_PROMPT)
    return ResolutionResponse(
        resolution=result.text,
        provider=result.provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )


@router.post("/resolve", response_model=ResolutionResponse)
def resolve(ticket: TicketRequest, llm: LLMProviderDep) -> ResolutionResponse:
    return draft_resolution(ticket, llm)
