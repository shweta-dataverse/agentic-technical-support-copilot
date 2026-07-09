# Azure OpenAI backend — the primary/live-demo provider.
# German enterprises favour Azure OpenAI for GDPR / EU data-residency reasons,
# so this is the default backend.

from __future__ import annotations

from openai import AzureOpenAI

from copilot.config import Settings
from copilot.llm.providers.base import LLMResponse
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class AzureOpenAIProvider:
    name = "azure"

    def __init__(self, settings: Settings):
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise ValueError(
                "Azure OpenAI selected but AZURE_OPENAI_ENDPOINT / "
                "AZURE_OPENAI_API_KEY are not set."
            )

        self.model = settings.azure_openai_deployment
        self._default_max_tokens = settings.llm_max_tokens
        self._default_temperature = settings.llm_temperature
        self._client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        logger.info("azure openai provider initialized (deployment=%s)", self.model)

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens or self._default_max_tokens,
            temperature=temperature if temperature is not None else self._default_temperature,
        )

        usage = completion.usage
        return LLMResponse(
            text=(completion.choices[0].message.content or "").strip(),
            model=self.model,
            provider=self.name,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )
