"""Run the evaluation suite against the live system and gate on thresholds.

Usage: python scripts/run_eval.py [--no-judge]
Exit code 1 on any threshold violation (CI eval gate).
"""

from __future__ import annotations

import argparse
import sys

from copilot.agents.graph import build_graph
from copilot.agents.nodes import AgentNodes
from copilot.evaluation.judge import Judge
from copilot.evaluation.runner import (
    RESULTS_PATH,
    aggregate,
    check_thresholds,
    evaluate_case,
    load_golden,
    log_to_mlflow,
)
from copilot.llm.prompt_store import load_prompt
from copilot.llm.providers import get_llm_provider
from copilot.llm.wrapper import LLMClient
from copilot.retrieval.client import HybridRetriever


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the golden-dataset eval")
    parser.add_argument("--no-judge", action="store_true", help="skip LLM-judge metrics")
    args = parser.parse_args()

    llm = LLMClient(get_llm_provider())
    graph = build_graph(AgentNodes(llm=llm, retriever=HybridRetriever.from_settings()))
    judge = None if args.no_judge else Judge(LLMClient(get_llm_provider()))

    cases = load_golden()
    print(f"running {len(cases)} golden cases...")
    results = []
    for case in cases:
        result = evaluate_case(case, graph, judge)
        results.append(result)
        flag = "ESCALATE" if result.escalated else "resolve "
        print(
            f"  {case.id:<32} p@k={result.precision_at_k:.2f} r@k={result.recall_at_k:.2f} "
            f"conf={result.confidence:.2f} {flag} "
            f"faith={result.faithfulness:.2f}"
        )

    report = aggregate(results, cases)
    prompt_versions = {
        "triage": load_prompt("triage").version,
        "synthesis": load_prompt("synthesis").version,
    }
    log_to_mlflow(report, prompt_versions)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(report.model_dump_json(indent=2))

    print("\n=== aggregate ===")
    print(f"retrieval precision@k : {report.retrieval_precision_at_k:.3f}")
    print(f"retrieval recall@k    : {report.retrieval_recall_at_k:.3f}")
    print(f"fabricated citations  : {report.fabricated_citation_rate:.3f}")
    print(f"escalation accuracy   : {report.escalation_accuracy:.3f}")
    print(f"mean conf (covered)   : {report.mean_confidence_covered:.3f}")
    print(f"faithfulness          : {report.faithfulness:.3f}")
    print(f"answer relevancy      : {report.answer_relevancy:.3f}")
    print(f"total cost            : EUR {report.total_cost_eur:.4f}")

    failures = check_thresholds(report)
    if failures:
        print("\nEVAL GATE FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nEVAL GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
