# liveness/readiness endpoint. unauthenticated so orchestrators can probe it.

from __future__ import annotations

from fastapi import APIRouter

from copilot.api.deps import SettingsDep
from copilot.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        llm_provider=settings.llm_provider,
    )
