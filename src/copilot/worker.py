"""Async worker: consumes the hot-path queues and does the real work.

Handlers are pure functions over (session, payload) with injected
dependencies, so every path is unit-testable without a live bus.

Failure semantics (Section 9): a handler exception propagates to the
consumer loop, which abandons the message → Service Bus redelivers →
after max_delivery_count the message dead-letters. Handlers must therefore
be idempotent — redelivery is not an error, it is the retry mechanism.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy.orm import Session

from copilot.agents.state import CopilotState
from copilot.db.models import Job, Ticket
from copilot.db.repository import save_resolution, upsert_ticket
from copilot.exceptions import TicketNotFoundError
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class Masker(Protocol):
    def mask(self, text: str) -> str: ...


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class TicketIndexer(Protocol):
    def upsert_ticket(
        self,
        *,
        ticket_id: str,
        summary: str,
        description: str,
        vector: list[float],
        resolution_text: str = "",
        category: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> None: ...


class Graph(Protocol):
    def invoke(self, state: Any, config: Any = None) -> dict[str, Any]: ...


def handle_ticket_ingest(
    session: Session,
    payload: dict[str, Any],
    *,
    masker: Masker,
    embedder: Embedder,
    indexer: TicketIndexer,
) -> None:
    """PII-mask → Postgres (system of record) → embed → incremental index.

    Ordering is the saga invariant: the record is durable in Postgres BEFORE
    it reaches the index — a crash can leave stored-but-not-yet-indexed
    (redelivery or the nightly reconciliation catches up), never
    indexed-but-not-stored.
    """
    summary = masker.mask(payload["summary"])
    description = masker.mask(payload["description"])

    ticket = upsert_ticket(
        session,
        ticket_id=payload["ticket_id"],
        summary=summary,
        description=description,
        source="webhook",
    )
    session.commit()

    vector = embedder.embed([f"{summary}\n{description}"])[0]
    indexer.upsert_ticket(
        ticket_id=ticket.ticket_id,
        summary=summary,
        description=description,
        vector=vector,
        category=ticket.category,
        severity=ticket.severity,
        status=ticket.status,
    )
    logger.info("ingested ticket %s (stored + indexed)", ticket.ticket_id)


def handle_ticket_resolve(
    session: Session, payload: dict[str, Any], *, graph: Graph
) -> None:
    """Run the agent graph for a queued job; persist result and job state."""
    job = session.get(Job, uuid.UUID(payload["job_id"]))
    if job is None:
        raise TicketNotFoundError(f"job {payload['job_id']} not found")
    ticket = session.get(Ticket, payload["ticket_id"])
    if ticket is None:
        raise TicketNotFoundError(f"ticket {payload['ticket_id']} not found")

    job.status = "running"
    job.started_at = datetime.now(UTC)
    session.commit()

    try:
        raw = graph.invoke(
            CopilotState(
                ticket_id=ticket.ticket_id,
                title=ticket.summary,
                description=ticket.description,
            )
        )
        state = CopilotState.model_validate(raw)
        assert state.triage is not None
        ticket.category = state.triage.category
        ticket.severity = state.triage.severity
        save_resolution(session, state)
        job.status = "done"
        job.finished_at = datetime.now(UTC)
        session.commit()
        logger.info("job %s done for ticket %s", job.id, ticket.ticket_id)
    except Exception as exc:
        session.rollback()
        job.status = "failed"
        # class name only — messages may carry PII
        job.error_class = type(exc).__name__
        job.finished_at = datetime.now(UTC)
        session.commit()
        raise


def main() -> int:
    """Wire real dependencies and run the consumer loop."""
    from copilot.agents.graph import build_graph
    from copilot.agents.nodes import AgentNodes
    from copilot.config import get_settings
    from copilot.db.connection import get_session_factory
    from copilot.ingestion.embedding import AzureEmbedder
    from copilot.ingestion.indexer import TicketsIndexer
    from copilot.ingestion.masking import PiiMasker
    from copilot.llm.providers import get_llm_provider
    from copilot.llm.wrapper import LLMClient
    from copilot.messaging.consumer import run_consumer_loop
    from copilot.retrieval.client import HybridRetriever

    settings = get_settings()
    masker = PiiMasker()
    embedder = AzureEmbedder()
    indexer = TicketsIndexer()
    graph = build_graph(
        AgentNodes(
            llm=LLMClient(get_llm_provider()),
            retriever=HybridRetriever.from_settings(),
        )
    )
    session_factory = get_session_factory()

    def ingest(payload: dict[str, Any]) -> None:
        with session_factory() as session:
            handle_ticket_ingest(
                session, payload, masker=masker, embedder=embedder, indexer=indexer
            )

    def resolve(payload: dict[str, Any]) -> None:
        with session_factory() as session:
            handle_ticket_resolve(session, payload, graph=graph)

    run_consumer_loop(
        {
            settings.queue_ticket_ingest: ingest,
            settings.queue_ticket_resolve: resolve,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
