"""
The agent nodes. Invalid model output is re-prompted once, then downgraded to an escalation,
never a crash.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from copilot.agents.state import (
    Citation,
    CopilotState,
    GuardrailResult,
    SynthesisResult,
    TriageResult,
)
from copilot.config import get_settings
from copilot.llm.prompt_store import load_prompt
from copilot.llm.wrapper import LLMClient, LLMResult
from copilot.retrieval.client import ManualHit, TicketHit
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class Retriever(Protocol):
    def search_manuals(
        self, query: str, *, k: int | None = None, filter_expression: str | None = None
    ) -> list[ManualHit]: ...

    def search_tickets(
        self, query: str, *, k: int | None = None, filter_expression: str | None = None
    ) -> list[TicketHit]: ...


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    result = json.loads(cleaned)
    if not isinstance(result, dict):
        raise json.JSONDecodeError("expected a JSON object", cleaned, 0)
    return result


class AgentNodes:
    def __init__(self, llm: LLMClient, retriever: Retriever) -> None:
        self._llm = llm
        self._retriever = retriever

    # -- triage ---------------------------------------------------------

    def triage(self, state: CopilotState) -> dict[str, Any]:
        prompt = load_prompt("triage")
        rendered = prompt.render(title=state.title, description=state.description)
        result, cost = self._structured_call(
            rendered, prompt.system, prompt.id, prompt.version, TriageResult
        )
        if result is None:
            # degrade: conservative default keeps the pipeline moving
            result = TriageResult(
                category="other",
                severity="medium",
                knowledge_source="both",
                reasoning="triage generation failed; defaulted",
            )
        return {
            "triage": result,
            "total_cost_eur": state.total_cost_eur + cost,
            "prompt_versions": {**state.prompt_versions, prompt.id: prompt.version},
        }

    # -- retrieval ------------------------------------------------------

    def search_tickets(self, state: CopilotState) -> dict[str, Any]:
        query = f"{state.title} {state.description}"
        filter_expression = None
        if state.triage is not None:
            filter_expression = f"category eq '{state.triage.category}'"
        hits = self._retriever.search_tickets(query, filter_expression=filter_expression)
        if not hits and filter_expression is not None:
            # relax the filter rather than returning nothing
            hits = self._retriever.search_tickets(query)
        return {"ticket_hits": hits}

    def search_manuals(self, state: CopilotState) -> dict[str, Any]:
        query = f"{state.title} {state.description}"
        return {"manual_hits": self._retriever.search_manuals(query)}

    # -- synthesis ------------------------------------------------------

    def synthesis(self, state: CopilotState) -> dict[str, Any]:
        prompt = load_prompt("synthesis")
        manual_context = "\n\n".join(
            f"[doc={h.doc_id} page={h.page}] {h.content}" for h in state.manual_hits
        ) or "(no manual context retrieved)"
        ticket_context = "\n\n".join(
            f"[ticket={h.ticket_id}] {h.summary}: {h.resolution_text}"
            for h in state.ticket_hits
        ) or "(no similar tickets found)"
        rendered = prompt.render(
            title=state.title,
            description=state.description,
            manual_context=manual_context,
            ticket_context=ticket_context,
        )
        result, cost = self._structured_call(
            rendered, prompt.system, prompt.id, prompt.version, SynthesisResult
        )
        if result is None:
            result = SynthesisResult(
                resolution_steps=[],
                citations=[],
                confidence=0.0,
                escalate=True,
                reasoning_summary="generation_failure: output failed validation twice",
            )
        return {
            "synthesis": result,
            "total_cost_eur": state.total_cost_eur + cost,
            "prompt_versions": {**state.prompt_versions, prompt.id: prompt.version},
        }

    # -- guardrails -----------------------------------------------------

    def guardrails(self, state: CopilotState) -> dict[str, Any]:
        """Enforce grounding: drop ungrounded citations so the delivered
        resolution has a fabricated-citation rate of 0 by construction.
        Escalate when nothing grounded remains or confidence is low.
        """
        assert state.synthesis is not None, "guardrails requires synthesis output"
        settings = get_settings()
        synthesis = state.synthesis
        reasons: list[str] = []

        def grounded(citation: Citation) -> bool:
            # +/-1 page tolerance: a procedure may span adjacent pages
            return any(
                citation.doc == h.doc_id and abs(citation.page - h.page) <= 1
                for h in state.manual_hits
            )

        kept = [c for c in synthesis.citations if grounded(c)]
        fabricated = [c for c in synthesis.citations if not grounded(c)]
        # deliver only grounded citations, this is the enforced invariant
        synthesis.citations = kept

        lost_all = bool(synthesis.resolution_steps) and not kept
        if fabricated:
            reasons.append(f"dropped {len(fabricated)} ungrounded citation(s)")
        if lost_all:
            reasons.append("no grounded citations remain after sanitization")
        if synthesis.confidence < settings.escalation_confidence_threshold:
            reasons.append(
                f"confidence {synthesis.confidence:.2f} below "
                f"{settings.escalation_confidence_threshold}"
            )

        escalate = (
            lost_all
            or synthesis.confidence < settings.escalation_confidence_threshold
            or synthesis.escalate
        )
        return {
            "synthesis": synthesis,
            "guardrails": GuardrailResult(
                passed=not lost_all,
                escalate=escalate,
                fabricated_citations=fabricated,
                reasons=reasons,
            ),
        }

    # -- helpers --------------------------------------------------------

    def _structured_call[T: BaseModel](
        self,
        rendered: str,
        system: str,
        prompt_id: str,
        prompt_version: str,
        model_cls: type[T],
    ) -> tuple[T | None, float]:
        """Call the LLM and validate; one corrective re-prompt on failure."""
        cost = 0.0
        attempt_prompt = rendered
        for attempt in range(2):
            response: LLMResult = self._llm.complete(
                attempt_prompt,
                system=system,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )
            cost += response.cost_eur
            try:
                return model_cls.model_validate(_parse_json(response.text)), cost
            except (json.JSONDecodeError, ValidationError) as exc:
                logger.warning(
                    "structured output invalid for %s (attempt %d): %s",
                    prompt_id,
                    attempt + 1,
                    exc,
                )
                attempt_prompt = (
                    f"{rendered}\n\nYour previous response was invalid: {exc}.\n"
                    "Respond again with ONLY the valid JSON object."
                )
        return None, cost


def _citation_key(citation: Citation) -> tuple[str, int]:
    return (citation.doc, citation.page)
