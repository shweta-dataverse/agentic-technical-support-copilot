"""The typed errors used across the app. Handlers branch on the type, never on the message text."""


class CopilotError(Exception):
    """Base class for all domain errors raised by this service."""

    def __init__(self, message: str, *, correlation_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.correlation_id = correlation_id


class RetrievalError(CopilotError):
    """A search-index query failed after retries."""


class LLMTimeoutError(CopilotError):
    """An LLM call exceeded its deadline."""


class LLMBudgetExceededError(CopilotError):
    """A request would exceed its token or cost budget."""


class GenerationValidationError(CopilotError):
    """LLM output failed structured-output validation after re-prompting."""


class GuardrailViolationError(CopilotError):
    """A generated resolution violated a guardrail (e.g. fabricated citation)."""


class IngestionValidationError(CopilotError):
    """An inbound document or ticket failed validation; record goes to quarantine."""


class TicketNotFoundError(CopilotError):
    """The requested ticket does not exist in the system of record."""


class DownstreamUnavailableError(CopilotError):
    """A dependency is unavailable (circuit open or connection refused)."""
