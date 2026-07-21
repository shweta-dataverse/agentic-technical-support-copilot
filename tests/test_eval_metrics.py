"""Deterministic evaluation-metric tests."""

from __future__ import annotations

import json
from pathlib import Path

from copilot.evaluation.metrics import (
    escalation_correct,
    fabricated_citation_rate,
    precision_recall_at_k,
)
from copilot.evaluation.schema import GoldenCase


def test_precision_recall_exact_match() -> None:
    p, r = precision_recall_at_k([388, 389], [388, 389])
    assert p == 1.0
    assert r == 1.0


def test_precision_recall_page_tolerance() -> None:
    # page 389 counts for expected 388 (procedure spans pages)
    p, r = precision_recall_at_k([389], [388])
    assert p == 1.0
    assert r == 1.0


def test_precision_penalises_irrelevant_pages() -> None:
    p, r = precision_recall_at_k([388, 12, 500, 999], [388])
    assert p == 0.25  # 1 of 4 retrieved relevant
    assert r == 1.0  # the one expected page was found


def test_recall_partial() -> None:
    _p, r = precision_recall_at_k([338], [338, 340, 342])
    assert r == 1 / 3


def test_empty_expected_returns_zero() -> None:
    assert precision_recall_at_k([1, 2], []) == (0.0, 0.0)


def test_fabricated_citation_rate() -> None:
    # cite pages 388 (retrieved) and 999 (never retrieved) -> 50% fabricated
    assert fabricated_citation_rate([388, 999], [388, 389]) == 0.5
    assert fabricated_citation_rate([388], [388, 389]) == 0.0
    assert fabricated_citation_rate([], [388]) == 0.0


def test_escalation_correct() -> None:
    assert escalation_correct(True, True)
    assert escalation_correct(False, False)
    assert not escalation_correct(True, False)


def test_golden_dataset_loads_and_is_wellformed() -> None:
    path = Path("eval/golden/manuals_golden.json")
    cases = [GoldenCase.model_validate(c) for c in json.loads(path.read_text())]
    assert len(cases) >= 10
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids)), "case ids must be unique"
    # grounded cases must name expected pages; escalate cases must not
    for c in cases:
        if c.expect_escalate:
            assert not c.expected_pages
        else:
            assert c.expected_pages, f"{c.id} needs expected_pages"
    assert sum(c.expect_escalate for c in cases) >= 2  # calibration needs both classes
