"""Contract tests for the AI Search index schemas — no service required."""

from __future__ import annotations

from copilot.retrieval.indexes import manuals_index, tickets_index

DIM = 1536


def test_manuals_index_shape() -> None:
    idx = manuals_index("manuals", DIM)
    fields = {f.name: f for f in idx.fields}
    assert fields["chunk_id"].key
    assert set(fields) == {
        "chunk_id",
        "content",
        "content_vector",
        "doc_id",
        "doc_title",
        "page",
        "section_title",
        "ingested_at",
    }
    assert fields["content_vector"].vector_search_dimensions == DIM
    assert fields["doc_id"].filterable and fields["page"].filterable


def test_tickets_index_shape() -> None:
    idx = tickets_index("tickets", DIM)
    fields = {f.name: f for f in idx.fields}
    assert fields["ticket_id"].key
    assert fields["content_vector"].vector_search_dimensions == DIM
    # triage labels must be usable as server-side filters
    assert fields["category"].filterable
    assert fields["severity"].filterable
    assert fields["status"].filterable


def test_both_indexes_have_vector_and_semantic_config() -> None:
    for idx in (manuals_index("m", DIM), tickets_index("t", DIM)):
        assert idx.vector_search is not None
        assert idx.vector_search.profiles
        assert idx.semantic_search is not None
