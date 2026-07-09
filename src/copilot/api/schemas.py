# request/response models for the public HTTP API.

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    environment: str
    llm_provider: str


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


class ResolutionResponse(BaseModel):
    resolution: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
