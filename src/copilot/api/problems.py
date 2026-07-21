"""Turns our typed errors into RFC 7807 problem+json responses. Clients never see a stack trace."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from copilot.api.middleware import get_correlation_id
from copilot.exceptions import (
    CopilotError,
    DownstreamUnavailableError,
    GenerationValidationError,
    GuardrailViolationError,
    IngestionValidationError,
    LLMBudgetExceededError,
    LLMTimeoutError,
    RetrievalError,
    TicketNotFoundError,
)
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

_STATUS_BY_TYPE: dict[type[CopilotError], int] = {
    TicketNotFoundError: 404,
    IngestionValidationError: 422,
    GuardrailViolationError: 422,
    GenerationValidationError: 502,
    LLMBudgetExceededError: 429,
    LLMTimeoutError: 504,
    RetrievalError: 503,
    DownstreamUnavailableError: 503,
}


def problem_response(
    *, status: int, title: str, detail: str, error_type: str
) -> JSONResponse:
    headers = {}
    if status in (429, 503):
        headers["Retry-After"] = "30"
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
        content={
            "type": f"urn:copilot:error:{error_type}",
            "title": title,
            "status": status,
            "detail": detail,
            "correlation_id": get_correlation_id(),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CopilotError)
    async def copilot_error_handler(_req: Request, exc: CopilotError) -> JSONResponse:
        status = _STATUS_BY_TYPE.get(type(exc), 500)
        return problem_response(
            status=status,
            title=type(exc).__name__,
            detail=exc.message,
            error_type=type(exc).__name__.removesuffix("Error").lower(),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_req: Request, exc: Exception) -> JSONResponse:
        # log the class only, messages may carry internals or PII
        logger.error("unhandled exception: %s", type(exc).__name__, exc_info=True)
        return problem_response(
            status=500,
            title="InternalServerError",
            detail="an unexpected error occurred",
            error_type="internal",
        )
