# Azure AI Foundry backend — serverless "Models-as-a-Service" models
# (Grok, Mistral, Llama, ...) served through the Azure AI Inference endpoint.
# Uses the vendor-neutral azure-ai-inference SDK, so the same provider works
# for any Foundry chat model.

from __future__ import annotations

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from copilot.config import Settings
from copilot.llm.providers.base import LLMResponse
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


class AzureFoundryProvider:
    name = "azure_foundry"

    def __init__(self, settings: Settings):
        if not settings.azure_foundry_endpoint or not settings.azure_foundry_api_key:
            raise ValueError(
                "Azure AI Foundry selected but AZURE_FOUNDRY_ENDPOINT / "
                "AZURE_FOUNDRY_API_KEY are not set."
            )

        self.model = settings.azure_foundry_model
        self._default_max_tokens = settings.llm_max_tokens
        self._default_temperature = settings.llm_temperature
        self._client = ChatCompletionsClient(
            endpoint=settings.azure_foundry_endpoint,
            credential=AzureKeyCredential(settings.azure_foundry_api_key),
        )
        logger.info(
            "azure ai foundry provider initialized (model=%s)",
            self.model or "<endpoint-default>",
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        messages: list = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(UserMessage(content=prompt))

        kwargs: dict = {
            "messages": messages,
            "max_tokens": max_tokens or self._default_max_tokens,
            "temperature": temperature
            if temperature is not None
            else self._default_temperature,
        }
        # single-model serverless endpoints don't need `model`; multi-model
        # Foundry endpoints do — pass it only when configured.
        if self.model:
            kwargs["model"] = self.model

        completion = self._client.complete(**kwargs)
        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=(choice.message.content or "").strip(),
            model=self.model or getattr(completion, "model", "azure-foundry"),
            provider=self.name,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )
