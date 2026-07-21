"""Runs the golden set, scores it, logs to MLflow, and fails if a metric is below threshold."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

import mlflow
import yaml

from copilot.agents.state import CopilotState
from copilot.evaluation.judge import Judge
from copilot.evaluation.metrics import (
    escalation_correct,
    fabricated_citation_rate,
    precision_recall_at_k,
)
from copilot.evaluation.schema import CaseResult, EvalReport, GoldenCase
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

GOLDEN_PATH = Path("eval/golden/manuals_golden.json")
THRESHOLDS_PATH = Path("eval/thresholds.yaml")
RESULTS_PATH = Path("eval/results/latest_report.json")


class Graph(Protocol):
    def invoke(self, state: Any, config: Any = None) -> dict[str, Any]: ...


def load_golden(path: Path = GOLDEN_PATH) -> list[GoldenCase]:
    return [GoldenCase.model_validate(c) for c in json.loads(path.read_text())]


def evaluate_case(case: GoldenCase, graph: Graph, judge: Judge | None) -> CaseResult:
    raw = graph.invoke(
        CopilotState(ticket_id=case.id, title=case.title, description=case.description)
    )
    state = CopilotState.model_validate(raw)
    assert state.synthesis is not None and state.guardrails is not None

    retrieved_pages = [h.page for h in state.manual_hits]
    cited_pages = [c.page for c in state.synthesis.citations]
    precision, recall = precision_recall_at_k(retrieved_pages, case.expected_pages)

    faithfulness = relevancy = judge_cost = 0.0
    if judge is not None and state.synthesis.resolution_steps:
        context = "\n".join(f"[page {h.page}] {h.content}" for h in state.manual_hits)
        answer = " ".join(state.synthesis.resolution_steps)
        faithfulness, relevancy, judge_cost = judge.score(
            ticket=f"{case.title}. {case.description}", context=context, answer=answer
        )

    return CaseResult(
        case_id=case.id,
        retrieved_pages=retrieved_pages,
        cited_pages=cited_pages,
        confidence=state.synthesis.confidence,
        escalated=state.guardrails.escalate,
        answer_text=" ".join(state.synthesis.resolution_steps),
        precision_at_k=precision,
        recall_at_k=recall,
        fabricated_citation_rate=fabricated_citation_rate(cited_pages, retrieved_pages),
        escalation_correct=escalation_correct(state.guardrails.escalate, case.expect_escalate),
        faithfulness=faithfulness,
        answer_relevancy=relevancy,
        cost_eur=state.total_cost_eur + judge_cost,
    )


def aggregate(results: list[CaseResult], cases: list[GoldenCase]) -> EvalReport:
    n = len(results)
    grounded = [
        r for r, c in zip(results, cases, strict=True) if not c.expect_escalate
    ]
    judged = [r for r in results if r.faithfulness > 0 or r.answer_relevancy > 0]

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    return EvalReport(
        n_cases=n,
        retrieval_precision_at_k=mean([r.precision_at_k for r in grounded]),
        retrieval_recall_at_k=mean([r.recall_at_k for r in grounded]),
        fabricated_citation_rate=mean([r.fabricated_citation_rate for r in results]),
        escalation_accuracy=mean([1.0 if r.escalation_correct else 0.0 for r in results]),
        mean_confidence_covered=mean([r.confidence for r in grounded]),
        faithfulness=mean([r.faithfulness for r in judged]),
        answer_relevancy=mean([r.answer_relevancy for r in judged]),
        total_cost_eur=sum(r.cost_eur for r in results),
        per_case=results,
    )


def check_thresholds(report: EvalReport, path: Path = THRESHOLDS_PATH) -> list[str]:
    """Return a list of threshold violations (empty = pass)."""
    t = yaml.safe_load(path.read_text())
    failures: list[str] = []

    def below(name: str, value: float, floor: float) -> None:
        if value < floor:
            failures.append(f"{name} {value:.3f} < floor {floor}")

    below("retrieval_precision", report.retrieval_precision_at_k, t["retrieval_precision_at_k"])
    below("retrieval_recall_at_k", report.retrieval_recall_at_k, t["retrieval_recall_at_k"])
    below("escalation_accuracy", report.escalation_accuracy, t["escalation_accuracy"])
    below("faithfulness", report.faithfulness, t["faithfulness"])
    below("answer_relevancy", report.answer_relevancy, t["answer_relevancy"])
    below("mean_confidence_covered", report.mean_confidence_covered, t["mean_confidence_covered"])
    if report.fabricated_citation_rate > t["fabricated_citation_rate_max"]:
        failures.append(
            f"fabricated_citation_rate {report.fabricated_citation_rate:.3f} "
            f"> max {t['fabricated_citation_rate_max']}"
        )
    return failures


def log_to_mlflow(report: EvalReport, prompt_versions: dict[str, str]) -> None:
    mlflow.set_experiment("copilot-eval")
    with mlflow.start_run():
        mlflow.log_params({f"prompt_{k}": v for k, v in prompt_versions.items()})
        mlflow.log_metrics(
            {
                "retrieval_precision_at_k": report.retrieval_precision_at_k,
                "retrieval_recall_at_k": report.retrieval_recall_at_k,
                "fabricated_citation_rate": report.fabricated_citation_rate,
                "escalation_accuracy": report.escalation_accuracy,
                "mean_confidence_covered": report.mean_confidence_covered,
                "faithfulness": report.faithfulness,
                "answer_relevancy": report.answer_relevancy,
                "total_cost_eur": report.total_cost_eur,
            }
        )
