from __future__ import annotations

import pytest

from copilot.config import Settings
from copilot.llm.providers.factory import _build


def test_azure_requires_credentials():
    settings = Settings(llm_provider="azure", azure_openai_endpoint="", azure_openai_api_key="")
    with pytest.raises(ValueError, match="Azure OpenAI"):
        _build(settings)


def test_anthropic_requires_api_key():
    settings = Settings(llm_provider="anthropic", anthropic_api_key="")
    with pytest.raises(ValueError, match="Anthropic"):
        _build(settings)


def test_azure_foundry_requires_credentials():
    settings = Settings(
        llm_provider="azure_foundry",
        azure_foundry_endpoint="",
        azure_foundry_api_key="",
    )
    with pytest.raises(ValueError, match="Azure AI Foundry"):
        _build(settings)


def test_ollama_builds_without_credentials():
    settings = Settings(llm_provider="ollama", ollama_model="llama3.1")
    provider = _build(settings)
    assert provider.name == "ollama"
    assert provider.model == "llama3.1"
