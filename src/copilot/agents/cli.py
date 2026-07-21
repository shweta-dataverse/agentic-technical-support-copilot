"""Run one end-to-end resolution from the terminal.

Usage: python -m copilot.agents.cli "<title>" "<description>"
"""

from __future__ import annotations

import argparse
import sys

from copilot.agents.graph import build_graph
from copilot.agents.nodes import AgentNodes
from copilot.agents.state import CopilotState
from copilot.llm.providers import get_llm_provider
from copilot.llm.wrapper import LLMClient
from copilot.retrieval.client import HybridRetriever
from copilot.telemetry.langfuse import get_langfuse_callback


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a ticket end-to-end")
    parser.add_argument("title")
    parser.add_argument("description")
    args = parser.parse_args()

    nodes = AgentNodes(
        llm=LLMClient(get_llm_provider()),
        retriever=HybridRetriever.from_settings(),
    )
    graph = build_graph(nodes)

    callback = get_langfuse_callback()
    config = {"callbacks": [callback]} if callback else {}
    raw = graph.invoke(
        CopilotState(title=args.title, description=args.description), config=config
    )
    state = CopilotState.model_validate(raw)

    assert state.triage and state.synthesis and state.guardrails
    print(f"\ntriage:     {state.triage.category}/{state.triage.severity} "
          f"→ {state.triage.knowledge_source}")
    print(f"retrieved:  {len(state.manual_hits)} manual chunks, "
          f"{len(state.ticket_hits)} tickets")
    print(f"confidence: {state.synthesis.confidence:.2f}   "
          f"escalate: {state.guardrails.escalate}   "
          f"guardrails: {'PASS' if state.guardrails.passed else 'FAIL'}")
    if state.guardrails.reasons:
        print(f"reasons:    {'; '.join(state.guardrails.reasons)}")
    print(f"cost:       {state.total_cost_eur:.4f} EUR\n")
    print("resolution steps:")
    for i, step in enumerate(state.synthesis.resolution_steps, 1):
        print(f"  {i}. {step}")
    print("\ncitations:")
    for c in state.synthesis.citations:
        print(f"  - {c.doc} p.{c.page}: \"{c.quote_span[:70]}\"")
    print(f"\nreasoning: {state.synthesis.reasoning_summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
