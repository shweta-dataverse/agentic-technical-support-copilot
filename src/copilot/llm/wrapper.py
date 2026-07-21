"""
The single place every LLM call goes through. Adds timeouts, retries, a circuit breaker, a cost
budget, and cost tracking.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from copilot.config import get_settings
from copilot.exceptions import (
    DownstreamUnavailableError,
    LLMBudgetExceededError,
    LLMTimeoutError,
)
from copilot.llm.providers.base import LLMProvider
from copilot.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResult:
    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_eur: float
    latency_ms: int
    prompt_id: str
    prompt_version: str


class CircuitBreaker:
    """Open after N consecutive failures; probe again after a cooldown."""

    def __init__(self, failure_threshold: int, reset_seconds: float) -> None:
        self._threshold = failure_threshold
        self._reset_seconds = reset_seconds
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self._reset_seconds:
            return False  # half-open: allow a probe
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = time.monotonic()


def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status == 429 or int(status) >= 500
    name = type(exc).__name__.lower()
    return "timeout" in name or "connection" in name


def _is_timeout(exc: Exception) -> bool:
    return "timeout" in type(exc).__name__.lower()


class LLMClient:
    def __init__(self, provider: LLMProvider, breaker: CircuitBreaker | None = None) -> None:
        settings = get_settings()
        self._provider = provider
        self._breaker = breaker or CircuitBreaker(
            settings.llm_breaker_failure_threshold, settings.llm_breaker_reset_seconds
        )

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        prompt_id: str,
        prompt_version: str,
        max_tokens: int | None = None,
    ) -> LLMResult:
        settings = get_settings()
        if self._breaker.is_open:
            raise DownstreamUnavailableError("llm circuit breaker open")

        self._enforce_budget(prompt, system, max_tokens)

        last_exc: Exception | None = None
        for attempt in range(settings.llm_max_retries + 1):
            start = time.monotonic()
            try:
                response = self._provider.generate(
                    prompt, system=system, max_tokens=max_tokens
                )
            except Exception as exc:  # noqa: BLE001  (classified below, never swallowed)
                last_exc = exc
                self._breaker.record_failure()
                if not _is_retryable(exc) or attempt == settings.llm_max_retries:
                    break
                delay = settings.llm_retry_base_seconds * (2**attempt) + random.uniform(0, 0.5)
                logger.warning(
                    "llm call failed (%s), retry %d/%d in %.1fs",
                    type(exc).__name__,
                    attempt + 1,
                    settings.llm_max_retries,
                    delay,
                )
                time.sleep(delay)
                continue

            self._breaker.record_success()
            latency_ms = int((time.monotonic() - start) * 1000)
            input_tokens = response.input_tokens or 0
            output_tokens = response.output_tokens or 0
            cost = (
                input_tokens * settings.llm_price_input_per_1m_eur
                + output_tokens * settings.llm_price_output_per_1m_eur
            ) / 1_000_000
            logger.info(
                "llm ok prompt=%s v%s model=%s tokens=%d/%d cost_eur=%.6f latency_ms=%d",
                prompt_id,
                prompt_version,
                response.model,
                input_tokens,
                output_tokens,
                cost,
                latency_ms,
            )
            return LLMResult(
                text=response.text,
                model=response.model,
                provider=response.provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_eur=cost,
                latency_ms=latency_ms,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        assert last_exc is not None
        if _is_timeout(last_exc):
            raise LLMTimeoutError(f"llm call timed out after retries: {prompt_id}") from last_exc
        raise DownstreamUnavailableError(
            f"llm call failed after retries: {type(last_exc).__name__}"
        ) from last_exc

    def _enforce_budget(
        self, prompt: str, system: str | None, max_tokens: int | None
    ) -> None:
        settings = get_settings()
        est_input = (len(prompt) + len(system or "")) / 4  # ~4 chars per token
        est_output = max_tokens or settings.llm_max_tokens
        est_cost = (
            est_input * settings.llm_price_input_per_1m_eur
            + est_output * settings.llm_price_output_per_1m_eur
        ) / 1_000_000
        if est_cost > settings.llm_max_cost_eur_per_request:
            raise LLMBudgetExceededError(
                f"estimated cost {est_cost:.4f} EUR exceeds per-request budget "
                f"{settings.llm_max_cost_eur_per_request} EUR"
            )
