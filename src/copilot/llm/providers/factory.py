# provider factory, resolves the configured backend at runtime.
# adding a new vendor means adding one branch here; nothing else changes.

from __future__ import annotations

from functools import lru_cache

from copilot.config import Settings, get_settings
from copilot.llm.providers.base import LLMProvider
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


def _build(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider

    if provider == "azure":
        from copilot.llm.providers.azure_openai import AzureOpenAIProvider

        return AzureOpenAIProvider(settings)

    if provider == "azure_foundry":
        from copilot.llm.providers.azure_foundry import AzureFoundryProvider

        return AzureFoundryProvider(settings)

    if provider == "anthropic":
        from copilot.llm.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings)

    if provider == "ollama":
        from copilot.llm.providers.ollama_provider import OllamaProvider

        return OllamaProvider(settings)

    raise ValueError(f"unknown llm provider: {provider!r}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Cached provider singleton, built from the active settings."""
    settings = get_settings()
    logger.info("resolving llm provider: %s", settings.llm_provider)
    return _build(settings)
