"""Deterministic evaluation metrics — no LLM, fast, CI-safe.

Page matching uses a +/-1 tolerance: a procedure often spans adjacent pages,
so a chunk from page 389 counts as relevant to expected page 388.
"""

from __future__ import annotations

PAGE_TOLERANCE = 1


def _matches(page: int, expected: set[int]) -> bool:
    return any(abs(page - e) <= PAGE_TOLERANCE for e in expected)


def precision_recall_at_k(
    retrieved_pages: list[int], expected_pages: list[int]
) -> tuple[float, float]:
    """Precision = relevant retrieved / retrieved; recall = expected found / expected."""
    if not expected_pages:
        return 0.0, 0.0
    if not retrieved_pages:
        return 0.0, 0.0
    expected = set(expected_pages)
    hits = [p for p in retrieved_pages if _matches(p, expected)]
    precision = len(hits) / len(retrieved_pages)
    found = {e for e in expected if any(_matches(p, {e}) for p in retrieved_pages)}
    recall = len(found) / len(expected)
    return precision, recall


def fabricated_citation_rate(
    cited_pages: list[int], retrieved_pages: list[int]
) -> float:
    """Fraction of citations whose page was never retrieved. Must be 0."""
    if not cited_pages:
        return 0.0
    retrieved = set(retrieved_pages)
    fabricated = [p for p in cited_pages if not _matches(p, retrieved)]
    return len(fabricated) / len(cited_pages)


def escalation_correct(escalated: bool, expect_escalate: bool) -> bool:
    return escalated == expect_escalate
