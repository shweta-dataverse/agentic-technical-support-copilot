"""Typed state flowing through the LangGraph workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from copilot.retrieval.client import ManualHit, TicketHit


class Citation(BaseModel):
    doc: str
    page: int
    quote_span: str = ""


class TriageResult(BaseModel):
    category: Literal[
        "hardware", "firmware", "configuration", "communication", "software", "other"
    ]
    severity: Literal["low", "medium", "high", "critical"]
    knowledge_source: Literal["manuals", "tickets", "both"]
    reasoning: str = ""


class SynthesisResult(BaseModel):
    resolution_steps: list[str]
    citations: list[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    escalate: bool = False
    reasoning_summary: str = ""


class GuardrailResult(BaseModel):
    passed: bool
    escalate: bool
    fabricated_citations: list[Citation] = []
    reasons: list[str] = []


class CopilotState(BaseModel):
    ticket_id: str = ""
    title: str
    description: str
    triage: TriageResult | None = None
    manual_hits: list[ManualHit] = []
    ticket_hits: list[TicketHit] = []
    synthesis: SynthesisResult | None = None
    guardrails: GuardrailResult | None = None
    total_cost_eur: float = 0.0
    prompt_versions: dict[str, str] = {}
