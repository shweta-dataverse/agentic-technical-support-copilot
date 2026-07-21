"""Langfuse integration, no-op when keys are not configured."""

from __future__ import annotations

from typing import Any

from copilot.config import get_settings
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


def get_langfuse_callback() -> Any | None:
    """Return a LangChain callback handler streaming traces to Langfuse EU,
    or None when Langfuse is not configured (local dev without keys)."""
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler

    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    logger.info("langfuse tracing enabled (host=%s)", settings.langfuse_host)
    return CallbackHandler()
