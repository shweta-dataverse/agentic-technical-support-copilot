# Anthropic (Claude) backend — the config-switchable secondary provider.
# Demonstrates that the agent layer is genuinely vendor-agnostic.

from __future__ import annotations

import anthropic

from copilot.config import Settings
from copilot.llm.providers.base import LLMResponse
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ValueError(
                "Anthropic selected but ANTHROPIC_API_KEY is not set."
            )

        self.model = settings.anthropic_model
        self._default_max_tokens = settings.llm_max_tokens
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        logger.info("anthropic provider initialized (model=%s)", self.model)

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        # note: temperature is intentionally ignored — the current Claude models
        # (Opus 4.x / Sonnet 5) reject sampling params; behaviour is steered via
        # the prompt instead.
        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self._default_max_tokens,
            system=system if system is not None else anthropic.omit,
            messages=[{"role": "user", "content": prompt}],
        )

        text = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()

        return LLMResponse(
            text=text,
            model=self.model,
            provider=self.name,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
