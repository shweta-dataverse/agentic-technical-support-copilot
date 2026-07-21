from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from copilot.api.main import create_app
from copilot.config import Settings, get_settings
from copilot.llm.providers import get_llm_provider
from copilot.llm.providers.base import LLMResponse


class FakeProvider:
    """Deterministic in-memory provider so tests need no real API keys."""

    name = "fake"
    model = "fake-model-1"

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            text=f"resolution for: {prompt[:40]}",
            model=self.model,
            provider=self.name,
            input_tokens=10,
            output_tokens=20,
        )


@pytest.fixture
def test_settings() -> Settings:
    return Settings(api_key="test-key", environment="local", llm_provider="anthropic")


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_llm_provider] = FakeProvider
    yield TestClient(app)
    app.dependency_overrides.clear()
