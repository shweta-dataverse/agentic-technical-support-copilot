"""Service Bus consumer loop with peek-lock semantics and idempotency.

Message lifecycle per receive:
  duplicate (seen message_id)      → complete immediately, skip handler
  handler succeeds                 → mark processed, complete
  handler raises                   → abandon → redelivery → DLQ after
                                     max_delivery_count (Service Bus native)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusReceivedMessage

from copilot.config import get_settings
from copilot.db.connection import get_session_factory
from copilot.messaging.idempotency import already_processed, mark_processed
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

Handler = Callable[[dict[str, Any]], None]


def _handle_message(
    queue: str, message: ServiceBusReceivedMessage, handler: Handler
) -> bool:
    """Returns True when the message should be completed, False to abandon."""
    message_id = str(message.message_id)
    correlation_id = str(message.correlation_id or "")
    session_factory = get_session_factory()

    with session_factory() as session:
        if already_processed(session, message_id):
            logger.info(
                "duplicate message %s on %s skipped (correlation_id=%s)",
                message_id,
                queue,
                correlation_id,
            )
            return True

    payload = json.loads(str(message))
    try:
        handler(payload)
    except Exception as exc:  # noqa: BLE001 — classified: abandon for redelivery
        logger.error(
            "handler failed queue=%s message_id=%s correlation_id=%s error=%s "
            "delivery_count=%s",
            queue,
            message_id,
            correlation_id,
            type(exc).__name__,
            message.delivery_count,
        )
        return False

    with session_factory() as session:
        mark_processed(session, message_id, queue)
    return True


def run_consumer_loop(handlers: dict[str, Handler]) -> None:
    """Poll all queues round-robin until interrupted."""
    settings = get_settings()
    namespace = f"{settings.servicebus_namespace}.servicebus.windows.net"
    client = ServiceBusClient(
        fully_qualified_namespace=namespace, credential=DefaultAzureCredential()
    )
    logger.info("worker consuming %s on %s", list(handlers), namespace)

    with client:
        receivers = {
            queue: client.get_queue_receiver(queue_name=queue, max_wait_time=5)
            for queue in handlers
        }
        try:
            while True:
                for queue, receiver in receivers.items():
                    for message in receiver.receive_messages(
                        max_message_count=1, max_wait_time=2
                    ):
                        if _handle_message(queue, message, handlers[queue]):
                            receiver.complete_message(message)
                        else:
                            receiver.abandon_message(message)
        except KeyboardInterrupt:
            logger.info("worker stopping")
        finally:
            for receiver in receivers.values():
                receiver.close()
