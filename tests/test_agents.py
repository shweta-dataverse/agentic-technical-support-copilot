"""Agent node and graph tests with fake LLM and retriever.

Includes the fabricated-citation test: a synthesis output citing a page that
was never retrieved MUST be caught by guardrails and escalated.
"""

from __future__ import annotations

import json
from typing import Any

from copilot.agents.graph import build_graph, route_after_tickets
from copilot.agents.nodes import AgentNodes
from copilot.agents.state import CopilotState, SynthesisResult, TriageResult
from copilot.llm.providers.base import LLMResponse
from copilot.llm.wrapper import LLMClient
from copilot.retrieval.client import ManualHit, TicketHit

MANUAL_HIT = ManualHit(
    chunk_id="c1",
    content="Change the device version in the device configuration.",
    doc_id="s71500",
    doc_title="manual.pdf",
    page=132,
    score=0.03,
)

TRIAGE_JSON = json.dumps(
    {
        "category": "configuration",
        "severity": "high",
        "knowledge_source": "both",
        "reasoning": "hw config mismatch",
    }
)


def synthesis_json(page: int, confidence: float = 0.9) -> str:
    return json.dumps(
        {
            "resolution_steps": ["Update the device version to match the MLFB."],
            "citations": [{"doc": "s71500", "page": page, "quote_span": "device version"}],
            "confidence": confidence,
            "escalate": False,
            "reasoning_summary": "Grounded in manual.",
        }
    )


class ScriptedProvider:
    """Returns queued responses in order."""

    name = "fake"
    model = "fake-1"

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)

    def generate(self, prompt, *, system=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        text = self.responses.pop(0)
        return LLMResponse(
            text=text, model=self.model, provider=self.name,
            input_tokens=100, output_tokens=50,
        )


class FakeRetriever:
    def __init__(self) -> None:
        self.ticket_calls: list[str | None] = []

    def search_manuals(
        self, query: str, *, k: int | None = None, filter_expression: str | None = None
    ) -> list[ManualHit]:
        return [MANUAL_HIT]

    def search_tickets(
        self, query: str, *, k: int | None = None, filter_expression: str | None = None
    ) -> list[TicketHit]:
        self.ticket_calls.append(filter_expression)
        return []


def make_nodes(responses: list[str]) -> AgentNodes:
    return AgentNodes(
        llm=LLMClient(ScriptedProvider(responses)), retriever=FakeRetriever()
    )


def run_graph(responses: list[str]) -> CopilotState:
    graph = build_graph(make_nodes(responses))
    raw: dict[str, Any] = graph.invoke(
        CopilotState(title="CPU STOP", description="startup inhibit 0x2521")
    )
    return CopilotState.model_validate(raw)


def test_full_graph_produces_grounded_resolution() -> None:
    state = run_graph([TRIAGE_JSON, synthesis_json(page=132)])
    assert state.triage is not None and state.triage.category == "configuration"
    assert state.synthesis is not None and state.synthesis.confidence == 0.9
    assert state.guardrails is not None
    assert state.guardrails.passed and not state.guardrails.escalate
    assert state.total_cost_eur > 0
    assert state.prompt_versions == {"triage": "1.0", "synthesis": "1.0"}


def test_fabricated_citation_is_caught_and_escalated() -> None:
    # cites page 999 which was never retrieved
    state = run_graph([TRIAGE_JSON, synthesis_json(page=999)])
    assert state.guardrails is not None
    assert not state.guardrails.passed
    assert state.guardrails.escalate
    assert state.guardrails.fabricated_citations[0].page == 999


def test_low_confidence_escalates_even_with_valid_citations() -> None:
    state = run_graph([TRIAGE_JSON, synthesis_json(page=132, confidence=0.3)])
    assert state.guardrails is not None
    assert state.guardrails.passed  # citations are real
    assert state.guardrails.escalate  # but confidence is below threshold


def test_malformed_synthesis_degrades_to_escalation() -> None:
    # both synthesis attempts return invalid output → degraded result, no crash
    state = run_graph([TRIAGE_JSON, "not json at all", "still not json"])
    assert state.synthesis is not None
    assert state.synthesis.escalate
    assert state.synthesis.confidence == 0.0
    assert "generation_failure" in state.synthesis.reasoning_summary


def test_triage_reprompt_once_on_invalid_output() -> None:
    state = run_graph(["garbage", TRIAGE_JSON, synthesis_json(page=132)])
    assert state.triage is not None
    assert state.triage.category == "configuration"


def test_route_skips_manuals_when_tickets_sufficient() -> None:
    triage = TriageResult(
        category="other", severity="low", knowledge_source="tickets", reasoning=""
    )
    state = CopilotState(title="t", description="d", triage=triage)
    assert route_after_tickets(state) == "synthesis"
    state.triage = TriageResult(
        category="other", severity="low", knowledge_source="both", reasoning=""
    )
    assert route_after_tickets(state) == "search_manuals"


def test_synthesis_result_validates_confidence_bounds() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SynthesisResult(resolution_steps=[], citations=[], confidence=1.5)
