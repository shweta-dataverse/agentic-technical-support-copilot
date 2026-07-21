"""Golden dataset and evaluation result schemas."""

from __future__ import annotations

from pydantic import BaseModel


class GoldenCase(BaseModel):
    """One curated ticket with manual-grounded ground truth.

    expected_pages: manual pages that actually contain the relevant procedure
    (a fact about the PDF, judged from its content, never from what the
    system retrieved). expect_escalate: True when the manual genuinely lacks
    coverage, so a well-calibrated system should escalate.
    """

    id: str
    title: str
    description: str
    category: str
    expected_pages: list[int] = []
    expected_answer_points: list[str] = []
    expect_escalate: bool = False


class CaseResult(BaseModel):
    """System output plus per-case scores for one golden case."""

    case_id: str
    retrieved_pages: list[int]
    cited_pages: list[int]
    confidence: float
    escalated: bool
    answer_text: str
    # deterministic metrics
    precision_at_k: float
    recall_at_k: float
    fabricated_citation_rate: float
    escalation_correct: bool
    # llm-judge metrics (0.0 when not scored)
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    cost_eur: float = 0.0


class EvalReport(BaseModel):
    """Aggregate metrics across all cases, compared against thresholds."""

    n_cases: int
    retrieval_precision_at_k: float
    retrieval_recall_at_k: float
    fabricated_citation_rate: float
    escalation_accuracy: float
    mean_confidence_covered: float  # calibration signal on well-covered cases
    faithfulness: float
    answer_relevancy: float
    total_cost_eur: float
    per_case: list[CaseResult] = []
