"""
Service Bus publisher. Authenticates with Managed Identity in Azure and az login locally, no
connection strings.
"""

from __future__ import annotations

import json
from typing import Any

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

from copilot.exceptions import DownstreamUnavailableError
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceBusPublisher:
    def __init__(self, namespace: str) -> None:
        self._client = ServiceBusClient(
            fully_qualified_namespace=f"{namespace}.servicebus.windows.net",
            credential=DefaultAzureCredential(),
        )

    def publish(
        self, queue: str, payload: dict[str, Any], *, correlation_id: str
    ) -> None:
        message = ServiceBusMessage(
            body=json.dumps(payload),
            correlation_id=correlation_id,
            content_type="application/json",
        )
        try:
            with self._client.get_queue_sender(queue) as sender:
                sender.send_messages(message)
        except AzureError as exc:
            raise DownstreamUnavailableError(
                f"service bus publish failed: {type(exc).__name__}",
                correlation_id=correlation_id,
            ) from exc
        logger.info("published queue=%s correlation_id=%s", queue, correlation_id)
