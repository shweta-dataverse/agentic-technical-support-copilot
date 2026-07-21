"""Shared FastAPI dependencies: settings, db session, auth, publisher, graph."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from copilot.config import Settings, get_settings
from copilot.db.connection import get_db
from copilot.messaging.publisher import QueuePublisher, get_publisher
from copilot.security.auth import authenticate
from copilot.security.rate_limit import RateLimiter

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]
PublisherDep = Annotated[QueuePublisher, Depends(get_publisher)]


@lru_cache
def get_rate_limiter() -> RateLimiter:
    return RateLimiter(get_settings().rate_limit_per_minute)


def require_api_key(
    session: DbDep,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    key_id = authenticate(session, x_api_key)
    if key_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
    allowed, retry_after = get_rate_limiter().check(key_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
    return key_id


def get_tickets_indexer() -> Any:
    """AI Search tickets index client (used for GDPR erase)."""
    from copilot.ingestion.indexer import TicketsIndexer

    return TicketsIndexer()


@lru_cache
def get_masker() -> Any:
    """Shared Presidio masker (loads the spaCy model once per process)."""
    from copilot.ingestion.masking import PiiMasker

    return PiiMasker()


@lru_cache
def get_resolution_graph() -> Any:
    """Compiled agent graph with real dependencies (lazy, process-wide)."""
    from copilot.agents.graph import build_graph
    from copilot.agents.nodes import AgentNodes
    from copilot.llm.providers import get_llm_provider
    from copilot.llm.wrapper import LLMClient
    from copilot.retrieval.client import HybridRetriever

    nodes = AgentNodes(
        llm=LLMClient(get_llm_provider()), retriever=HybridRetriever.from_settings()
    )
    return build_graph(nodes)
