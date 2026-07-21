"""Health and readiness checks. /health is liveness only; /ready pings Postgres and AI Search."""

from __future__ import annotations

from fastapi import APIRouter, Response
from sqlalchemy import text

from copilot.api.deps import SettingsDep
from copilot.api.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        llm_provider=settings.llm_provider,
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(settings: SettingsDep, response: Response) -> ReadyResponse:
    checks: dict[str, str] = {}

    try:
        from copilot.db.connection import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001  (probe reports, never raises)
        checks["postgres"] = f"failed: {type(exc).__name__}"

    if settings.azure_search_endpoint:
        try:
            from copilot.ingestion.indexer import ManualsIndexer

            ManualsIndexer().count_documents()
            checks["ai_search"] = "ok"
        except Exception as exc:  # noqa: BLE001  (probe reports, never raises)
            checks["ai_search"] = f"failed: {type(exc).__name__}"
    else:
        checks["ai_search"] = "not configured"

    all_ok = all(v in ("ok", "not configured") for v in checks.values())
    if not all_ok:
        response.status_code = 503
    return ReadyResponse(status="ready" if all_ok else "degraded", checks=checks)
