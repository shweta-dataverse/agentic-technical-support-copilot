"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from copilot.api.middleware import correlation_middleware, request_size_middleware
from copilot.api.problems import register_exception_handlers
from copilot.api.routes import health, jobs, resolve, tickets, webhooks
from copilot.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agentic Technical Support Co-Pilot",
        description=(
            "Multi-agent API that drafts grounded, citation-backed resolutions "
            "for technical-support tickets over a hybrid-retrieval knowledge base."
        ),
        version="2.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["X-API-Key", "X-Correlation-ID", "Content-Type"],
    )
    app.middleware("http")(request_size_middleware)
    app.middleware("http")(correlation_middleware)
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(resolve.router)
    app.include_router(tickets.router)
    app.include_router(jobs.router)
    app.include_router(webhooks.router)

    app.state.settings = settings
    return app


app = create_app()
