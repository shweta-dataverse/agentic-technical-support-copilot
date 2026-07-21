"""Consumer idempotency ledger backed by the processed_messages table."""

from __future__ import annotations

from sqlalchemy.orm import Session

from copilot.db.models import ProcessedMessage


def already_processed(session: Session, message_id: str) -> bool:
    return session.get(ProcessedMessage, message_id) is not None


def mark_processed(session: Session, message_id: str, queue_name: str) -> None:
    session.add(ProcessedMessage(message_id=message_id, queue_name=queue_name))
    session.commit()
