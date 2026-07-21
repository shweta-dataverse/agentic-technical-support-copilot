# provider-agnostic LLM interface.
# every concrete backend (azure openai, anthropic, ollama) implements this,
# so agents depend on the abstraction and never on a specific vendor SDK.

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class LLMResponse:
    """Normalized generation result across providers."""

    text: str
    model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal surface the agents rely on."""

    name: str
    model: str

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """Generate a completion for `prompt`, optionally steered by `system`."""
        ...
