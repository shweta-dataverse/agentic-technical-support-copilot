"""HTTP middleware: correlation ids, security headers, and a request size limit."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from copilot.config import get_settings

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

CORRELATION_HEADER = "X-Correlation-ID"

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def get_correlation_id() -> str:
    return _correlation_id.get()


async def correlation_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    cid = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
    _correlation_id.set(cid)
    response = await call_next(request)
    response.headers[CORRELATION_HEADER] = cid
    for header, value in _SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


async def request_size_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    length = request.headers.get("content-length")
    if length and int(length) > get_settings().max_request_bytes:
        return JSONResponse(
            status_code=413,
            media_type="application/problem+json",
            content={
                "type": "urn:copilot:error:payloadtoolarge",
                "title": "PayloadTooLarge",
                "status": 413,
                "detail": "request body exceeds the configured limit",
                "correlation_id": get_correlation_id(),
            },
        )
    return await call_next(request)
