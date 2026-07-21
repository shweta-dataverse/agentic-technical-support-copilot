"""
Hybrid search client. Each query runs keyword and vector search together and returns typed hits
with page citations.
"""

from __future__ import annotations

from typing import Any, Protocol

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from pydantic import BaseModel

from copilot.config import get_settings
from copilot.exceptions import RetrievalError
from copilot.ingestion.embedding import AzureEmbedder


class ManualHit(BaseModel):
    chunk_id: str
    content: str
    doc_id: str
    doc_title: str
    page: int
    score: float


class TicketHit(BaseModel):
    ticket_id: str
    summary: str
    description: str
    resolution_text: str
    category: str | None = None
    severity: str | None = None
    status: str | None = None
    score: float


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class Searcher(Protocol):
    """Narrow surface of azure SearchClient used here (injectable for tests)."""

    def search(self, **kwargs: Any) -> Any: ...


class HybridRetriever:
    def __init__(
        self, *, manuals: Searcher, tickets: Searcher, embedder: Embedder
    ) -> None:
        self._manuals = manuals
        self._tickets = tickets
        self._embedder = embedder

    @classmethod
    def from_settings(cls) -> HybridRetriever:
        s = get_settings()
        credential = AzureKeyCredential(s.azure_search_api_key)
        return cls(
            manuals=SearchClient(s.azure_search_endpoint, s.search_index_manuals, credential),
            tickets=SearchClient(s.azure_search_endpoint, s.search_index_tickets, credential),
            embedder=AzureEmbedder(),
        )

    def _hybrid(
        self, client: Searcher, query: str, k: int, filter_expression: str | None
    ) -> list[dict[str, Any]]:
        vector = self._embedder.embed([query])[0]
        try:
            results = client.search(
                search_text=query,
                vector_queries=[
                    VectorizedQuery(vector=vector, k_nearest_neighbors=k, fields="content_vector")
                ],
                filter=filter_expression,
                top=k,
            )
            return [dict(r) for r in results]
        except AzureError as exc:
            raise RetrievalError(f"hybrid search failed: {type(exc).__name__}") from exc

    def search_manuals(
        self, query: str, *, k: int | None = None, filter_expression: str | None = None
    ) -> list[ManualHit]:
        k = k or get_settings().retrieval_k_manuals
        return [
            ManualHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                doc_id=r["doc_id"],
                doc_title=r["doc_title"],
                page=r["page"],
                score=r["@search.score"],
            )
            for r in self._hybrid(self._manuals, query, k, filter_expression)
        ]

    def search_tickets(
        self, query: str, *, k: int | None = None, filter_expression: str | None = None
    ) -> list[TicketHit]:
        k = k or get_settings().retrieval_k_tickets
        return [
            TicketHit(
                ticket_id=r["ticket_id"],
                summary=r["summary"],
                description=r["description"],
                resolution_text=r["resolution_text"],
                category=r.get("category"),
                severity=r.get("severity"),
                status=r.get("status"),
                score=r["@search.score"],
            )
            for r in self._hybrid(self._tickets, query, k, filter_expression)
        ]
