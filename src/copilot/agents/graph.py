"""LangGraph workflow wiring.

Triage → Jira (ticket search) → [conditional] Knowledge (manual search)
→ Synthesis → Guardrails. The knowledge step is skipped when triage deems
ticket history sufficient.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from copilot.agents.nodes import AgentNodes
from copilot.agents.state import CopilotState


def route_after_tickets(state: CopilotState) -> str:
    if state.triage is not None and state.triage.knowledge_source == "tickets":
        return "synthesis"
    return "search_manuals"


def build_graph(nodes: AgentNodes) -> Any:
    graph: StateGraph[CopilotState] = StateGraph(CopilotState)
    graph.add_node("triage", nodes.triage)
    graph.add_node("search_tickets", nodes.search_tickets)
    graph.add_node("search_manuals", nodes.search_manuals)
    graph.add_node("synthesis", nodes.synthesis)
    graph.add_node("guardrails", nodes.guardrails)

    graph.add_edge(START, "triage")
    graph.add_edge("triage", "search_tickets")
    graph.add_conditional_edges(
        "search_tickets", route_after_tickets, ["search_manuals", "synthesis"]
    )
    graph.add_edge("search_manuals", "synthesis")
    graph.add_edge("synthesis", "guardrails")
    graph.add_edge("guardrails", END)
    return graph.compile()
