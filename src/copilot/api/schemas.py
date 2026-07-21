"""Request/response models for the public HTTP API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    environment: str
    llm_provider: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


class TicketRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        examples=["S7-1500 CPU goes to STOP after firmware update"],
    )
    description: str = Field(
        ...,
        min_length=1,
        examples=["After updating to firmware V2.9 the CPU enters STOP mode with SF LED on."],
    )


class CitationOut(BaseModel):
    doc: str
    page: int
    quote_span: str = ""


class ResolutionResponse(BaseModel):
    ticket_id: str
    resolution_steps: list[str]
    citations: list[CitationOut]
    confidence: float
    escalate: bool
    reasoning_summary: str
    category: str | None = None
    severity: str | None = None
    model: str | None = None
    cost_eur: float | None = None


class JiraWebhookIssueFields(BaseModel):
    summary: str
    description: str | None = None


class JiraWebhookIssue(BaseModel):
    key: str
    fields: JiraWebhookIssueFields


class JiraWebhookPayload(BaseModel):
    webhookEvent: str  # noqa: N815  (jira's field name)
    issue: JiraWebhookIssue


class AcceptedResponse(BaseModel):
    status: str = "accepted"
    correlation_id: str


class JobAcceptedResponse(BaseModel):
    job_id: uuid.UUID
    status: str = "queued"


class JobResponse(BaseModel):
    id: uuid.UUID
    job_type: str
    status: str
    ticket_id: str | None
    error_class: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    result: dict[str, Any] | None = None


class TicketResponse(BaseModel):
    ticket_id: str
    summary: str
    description: str
    category: str | None
    severity: str | None
    status: str
    source: str
    created_at: datetime


class TicketListItem(BaseModel):
    ticket_id: str
    summary: str
    category: str | None
    severity: str | None
    status: str
    source: str
    created_at: datetime
    resolved: bool


class SeedResponse(BaseModel):
    created: int
    total: int
