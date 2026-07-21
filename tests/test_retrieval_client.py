"""Hybrid retriever unit tests — fakes for the search SDK and embedder."""

from __future__ import annotations

from typing import Any

import pytest

from copilot.exceptions import RetrievalError
from copilot.retrieval.client import HybridRetriever


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 4 for _ in texts]


class FakeSearcher:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.last_kwargs: dict[str, Any] = {}

    def search(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        return iter(self.rows)


MANUAL_ROW = {
    "chunk_id": "abc",
    "content": "Set the device version to match the MLFB.",
    "doc_id": "s71500",
    "doc_title": "manual.pdf",
    "page": 132,
    "@search.score": 0.031,
}

TICKET_ROW = {
    "ticket_id": "SUP-42",
    "summary": "CPU stop after firmware update",
    "description": "SF LED on",
    "resolution_text": "Downgraded firmware",
    "category": "hardware",
    "severity": "high",
    "status": "resolved",
    "@search.score": 0.05,
}


def make_retriever(
    manual_rows: list[dict[str, Any]] | None = None,
    ticket_rows: list[dict[str, Any]] | None = None,
) -> tuple[HybridRetriever, FakeSearcher, FakeSearcher]:
    manuals = FakeSearcher(manual_rows or [MANUAL_ROW])
    tickets = FakeSearcher(ticket_rows or [TICKET_ROW])
    retriever = HybridRetriever(manuals=manuals, tickets=tickets, embedder=FakeEmbedder())
    return retriever, manuals, tickets


def test_manual_hits_are_typed_with_citation_metadata() -> None:
    retriever, _, _ = make_retriever()
    hits = retriever.search_manuals("device version")
    assert hits[0].page == 132
    assert hits[0].doc_title == "manual.pdf"
    assert hits[0].score == pytest.approx(0.031)


def test_hybrid_query_includes_text_and_vector() -> None:
    retriever, manuals, _ = make_retriever()
    retriever.search_manuals("startup inhibit", k=3)
    kwargs = manuals.last_kwargs
    assert kwargs["search_text"] == "startup inhibit"
    assert kwargs["top"] == 3
    assert kwargs["vector_queries"][0].fields == "content_vector"


def test_default_k_comes_from_settings() -> None:
    retriever, manuals, tickets = make_retriever()
    retriever.search_manuals("q")
    assert manuals.last_kwargs["top"] == 8
    retriever.search_tickets("q")
    assert tickets.last_kwargs["top"] == 5


def test_filter_expression_passes_through() -> None:
    retriever, _, tickets = make_retriever()
    retriever.search_tickets("q", filter_expression="category eq 'hardware'")
    assert tickets.last_kwargs["filter"] == "category eq 'hardware'"


def test_azure_errors_become_retrieval_errors() -> None:
    from azure.core.exceptions import HttpResponseError

    class Failing:
        def search(self, **kwargs: Any) -> Any:
            raise HttpResponseError("boom")

    retriever = HybridRetriever(
        manuals=Failing(), tickets=Failing(), embedder=FakeEmbedder()
    )
    with pytest.raises(RetrievalError):
        retriever.search_manuals("q")
