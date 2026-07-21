"""Runner aggregation and threshold-gate tests (no live system)."""

from __future__ import annotations

from copilot.evaluation.runner import aggregate, check_thresholds
from copilot.evaluation.schema import CaseResult, GoldenCase


def grounded_case(cid: str) -> GoldenCase:
    return GoldenCase(
        id=cid, title="t", description="d", category="hardware", expected_pages=[10]
    )


def escalate_case(cid: str) -> GoldenCase:
    return GoldenCase(
        id=cid, title="t", description="d", category="other", expect_escalate=True
    )


def good_result(cid: str, **overrides: float) -> CaseResult:
    base = dict(
        case_id=cid,
        retrieved_pages=[10],
        cited_pages=[10],
        confidence=0.8,
        escalated=False,
        answer_text="ok",
        precision_at_k=1.0,
        recall_at_k=1.0,
        fabricated_citation_rate=0.0,
        escalation_correct=True,
        faithfulness=0.9,
        answer_relevancy=0.9,
        cost_eur=0.01,
    )
    base.update(overrides)
    return CaseResult(**base)  # type: ignore[arg-type]


def test_aggregate_confidence_only_over_covered_cases() -> None:
    cases = [grounded_case("a"), escalate_case("b")]
    results = [
        good_result("a", confidence=0.8),
        good_result("b", confidence=0.2, escalated=True),
    ]
    report = aggregate(results, cases)
    # escalate case's low confidence must not drag the covered-case mean
    assert report.mean_confidence_covered == 0.8


def test_gate_passes_healthy_report() -> None:
    cases = [grounded_case("a")]
    report = aggregate([good_result("a")], cases)
    assert check_thresholds(report) == []


def test_gate_fails_on_fabricated_citation() -> None:
    cases = [grounded_case("a")]
    report = aggregate([good_result("a", fabricated_citation_rate=0.5)], cases)
    failures = check_thresholds(report)
    assert any("fabricated" in f for f in failures)


def test_gate_fails_on_low_faithfulness() -> None:
    cases = [grounded_case("a")]
    report = aggregate([good_result("a", faithfulness=0.1)], cases)
    assert any("faithfulness" in f for f in check_thresholds(report))
