"""Database engine and sessions. The URL always comes from settings, never hardcoded."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from copilot.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Process-wide engine with pre-ping so stale pool connections are recycled."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that always closes."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
