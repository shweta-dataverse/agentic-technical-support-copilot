"""
Queue publishing behind a protocol. Uses Service Bus when configured, otherwise logs the
message for local dev.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from copilot.config import get_settings
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class QueuePublisher(Protocol):
    def publish(
        self, queue: str, payload: dict[str, Any], *, correlation_id: str
    ) -> None: ...


class LoggingPublisher:
    """Local stand-in: logs the message instead of sending it."""

    def publish(
        self, queue: str, payload: dict[str, Any], *, correlation_id: str
    ) -> None:
        logger.info(
            "publish (log-only) queue=%s correlation_id=%s payload=%s",
            queue,
            correlation_id,
            json.dumps(payload)[:500],
        )


def get_publisher() -> QueuePublisher:
    settings = get_settings()
    if not settings.servicebus_namespace:
        return LoggingPublisher()
    from copilot.messaging.servicebus import ServiceBusPublisher

    return ServiceBusPublisher(settings.servicebus_namespace)
