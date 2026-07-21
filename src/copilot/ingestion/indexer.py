"""Upsert chunk documents into the AI Search manuals index."""

from __future__ import annotations

from datetime import UTC, datetime

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from copilot.config import get_settings
from copilot.exceptions import RetrievalError
from copilot.ingestion.chunking import Chunk


class ManualsIndexer:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.search_index_manuals,
            credential=AzureKeyCredential(settings.azure_search_api_key),
        )

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> int:
        """merge_or_upload keyed on chunk_id, re-runs overwrite, never duplicate."""
        now = datetime.now(UTC).isoformat()
        documents = [
            {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "content_vector": vector,
                "doc_id": chunk.doc_id,
                "doc_title": chunk.doc_title,
                "page": chunk.page,
                "section_title": "",
                "ingested_at": now,
            }
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        results = self._client.merge_or_upload_documents(documents)
        failed = [r.key for r in results if not r.succeeded]
        if failed:
            raise RetrievalError(f"index upsert failed for {len(failed)} chunks")
        return len(documents)

    def count_documents(self) -> int:
        return int(self._client.get_document_count())


class TicketsIndexer:
    """Incremental single-ticket upserts into the tickets index (hot path)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.search_index_tickets,
            credential=AzureKeyCredential(settings.azure_search_api_key),
        )

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
    ) -> None:
        document = {
            "ticket_id": ticket_id,
            "summary": summary,
            "description": description,
            "resolution_text": resolution_text,
            "content_vector": vector,
            "category": category,
            "severity": severity,
            "status": status,
            "created_at": datetime.now(UTC).isoformat(),
        }
        results = self._client.merge_or_upload_documents([document])
        if not results[0].succeeded:
            raise RetrievalError(f"ticket index upsert failed for {ticket_id}")
