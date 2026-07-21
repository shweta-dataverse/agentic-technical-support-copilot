"""API key auth. Keys are stored hashed (SHA256 of pepper plus key), never in plaintext."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from copilot.config import get_settings
from copilot.db.models import ApiKey


def hash_key(key: str) -> str:
    settings = get_settings()
    return hashlib.sha256(f"{settings.api_key_pepper}{key}".encode()).hexdigest()


def authenticate(session: Session, presented_key: str | None) -> str | None:
    """Return a stable key identity when valid, else None."""
    if not presented_key:
        return None
    settings = get_settings()
    if settings.api_key and presented_key == settings.api_key:
        return "bootstrap"
    entry = session.execute(
        select(ApiKey).where(ApiKey.key_hash == hash_key(presented_key), ApiKey.active)
    ).scalar_one_or_none()
    if entry is None:
        return None
    entry.last_used_at = datetime.now(UTC)
    session.commit()
    return str(entry.id)
