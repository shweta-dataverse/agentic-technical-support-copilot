"""LLM-as-judge scoring for faithfulness and answer relevancy, using the shared LLM wrapper."""

from __future__ import annotations

import json

from copilot.llm.wrapper import LLMClient
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

_JUDGE_SYSTEM = (
    "You are a strict evaluation judge for technical-support answers. "
    "You always reply with a single JSON object and nothing else."
)

_JUDGE_TEMPLATE = """Score the answer against the retrieved context and the ticket.

Ticket: {ticket}

Retrieved context:
{context}

Answer under evaluation:
{answer}

Return exactly:
{{"faithfulness": <0.0-1.0, fraction of answer claims supported by the context>,
"answer_relevancy": <0.0-1.0, how directly the answer addresses the ticket>}}
"""


class Judge:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def score(self, *, ticket: str, context: str, answer: str) -> tuple[float, float, float]:
        """Returns (faithfulness, answer_relevancy, cost_eur)."""
        rendered = _JUDGE_TEMPLATE.format(
            ticket=ticket, context=context[:8000], answer=answer[:4000]
        )
        result = self._llm.complete(
            rendered, system=_JUDGE_SYSTEM, prompt_id="judge", prompt_version="1.0"
        )
        try:
            data = json.loads(result.text.strip().strip("`").removeprefix("json"))
            return (
                float(data["faithfulness"]),
                float(data["answer_relevancy"]),
                result.cost_eur,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("judge output unparseable: %s", exc)
            return 0.0, 0.0, result.cost_eur
