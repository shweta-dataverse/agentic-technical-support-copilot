# FastAPI application factory.

from __future__ import annotations

from fastapi import FastAPI

from copilot.api.routes import health, resolve
from copilot.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agentic Technical Support Co-Pilot",
        description=(
            "Provider-agnostic multi-agent API that drafts resolutions for "
            "technical-support tickets over a hybrid-retrieval knowledge base."
        ),
        version="2.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.include_router(health.router)
    app.include_router(resolve.router)

    app.state.settings = settings
    return app


app = create_app()
