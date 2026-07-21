"""LLM wrapper failure-mode tests: retries, breaker, budget, cost."""

from __future__ import annotations

import pytest

from copilot.exceptions import DownstreamUnavailableError, LLMBudgetExceededError
from copilot.llm.providers.base import LLMResponse
from copilot.llm.wrapper import CircuitBreaker, LLMClient


class RateLimitError(Exception):
    status_code = 429


class ServerError(Exception):
    status_code = 503


class AuthError(Exception):
    status_code = 401


class FlakyProvider:
    """Fails `failures` times with `exc_cls`, -> succeeds."""

    name = "fake"
    model = "fake-1"

    def __init__(self, failures: int = 0, exc_cls: type[Exception] = RateLimitError) -> None:
        self.failures = failures
        self.exc_cls = exc_cls
        self.calls = 0

    def generate(self, prompt, *, system=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc_cls("boom")
        return LLMResponse(
            text='{"ok": true}', model=self.model, provider=self.name,
            input_tokens=100, output_tokens=50,
        )


@pytest.fixture(autouse=True)
def fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("copilot.llm.wrapper.time.sleep", lambda _s: None)


def test_retries_transient_429_then_succeeds() -> None:
    provider = FlakyProvider(failures=2)
    result = LLMClient(provider).complete("hi", prompt_id="t", prompt_version="1")
    assert provider.calls == 3
    assert result.cost_eur > 0


def test_non_retryable_error_fails_fast() -> None:
    provider = FlakyProvider(failures=99, exc_cls=AuthError)
    with pytest.raises(DownstreamUnavailableError):
        LLMClient(provider).complete("hi", prompt_id="t", prompt_version="1")
    assert provider.calls == 1


def test_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=999)
    provider = FlakyProvider(failures=99, exc_cls=ServerError)
    client = LLMClient(provider, breaker=breaker)
    with pytest.raises(DownstreamUnavailableError):
        client.complete("hi", prompt_id="t", prompt_version="1")
    # breaker is now open: next call rejected without touching the provider
    calls_before = provider.calls
    with pytest.raises(DownstreamUnavailableError, match="breaker open"):
        client.complete("hi", prompt_id="t", prompt_version="1")
    assert provider.calls == calls_before


def test_budget_guard_rejects_oversized_request() -> None:
    provider = FlakyProvider()
    huge_prompt = "x" * 5_000_000
    with pytest.raises(LLMBudgetExceededError):
        LLMClient(provider).complete(huge_prompt, prompt_id="t", prompt_version="1")
    assert provider.calls == 0  # rejected before any spend


def test_cost_accounting_uses_configured_prices() -> None:
    provider = FlakyProvider()
    result = LLMClient(provider).complete("hi", prompt_id="t", prompt_version="1")
    # 100 input + 50 output tokens at configured EUR prices
    from copilot.config import get_settings

    s = get_settings()
    expected = (100 * s.llm_price_input_per_1m_eur + 50 * s.llm_price_output_per_1m_eur) / 1e6
    assert result.cost_eur == pytest.approx(expected)
