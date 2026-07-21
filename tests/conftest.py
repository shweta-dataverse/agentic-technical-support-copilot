"""Shared fixtures: hermetic settings via env vars, fake DB, fake graph.

Settings are a process-wide cached singleton read by many modules directly,
so tests override via environment variables (highest precedence) and clear
the cache, not via FastAPI dependency overrides.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from copilot.agents.state import CopilotState
from copilot.api.deps import get_rate_limiter, get_resolution_graph
from copilot.api.main import create_app
from copilot.config import get_settings
from copilot.db.connection import get_db
from copilot.db.models import Job
from copilot.messaging.publisher import get_publisher

TEST_API_KEY = "test-key"
TEST_WEBHOOK_SECRET = "test-webhook-secret"

TEST_SYNTHESIS = {
    "resolution_steps": ["Match the configured module version to the physical module."],
    "citations": [{"doc": "s71500", "page": 338, "quote_span": "expected configuration"}],
    "confidence": 0.9,
    "escalate": False,
    "reasoning_summary": "Grounded in the manual.",
}


class FakeGraph:
    """Returns a completed state without touching any Azure service."""

    def invoke(self, state: CopilotState, config: Any = None) -> dict[str, Any]:
        data = state.model_dump()
        data.update(
            {
                "triage": {
                    "category": "configuration",
                    "severity": "high",
                    "knowledge_source": "manuals",
                    "reasoning": "test",
                },
                "synthesis": TEST_SYNTHESIS,
                "guardrails": {
                    "passed": True,
                    "escalate": False,
                    "fabricated_citations": [],
                    "reasons": [],
                },
                "total_cost_eur": 0.005,
                "prompt_versions": {"triage": "1.0", "synthesis": "1.0"},
            }
        )
        return data


class FakeResult:
    def __init__(self, value: Any = None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


class FakeDb:
    """Narrow Session stand-in for API unit tests."""

    def __init__(self) -> None:
        self.objects: dict[tuple[type, Any], Any] = {}
        self.added: list[Any] = []
        self.committed = False
        self.query_result: Any = None

    def get(self, model: type, key: Any) -> Any:
        return self.objects.get((model, key))

    def execute(self, _stmt: Any) -> FakeResult:
        return FakeResult(self.query_result)

    def add(self, obj: Any) -> None:
        if isinstance(obj, Job) and obj.id is None:
            obj.id = uuid.uuid4()
        self.added.append(obj)

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass

    def as_session(self) -> Session:
        """Typed view for handlers that annotate sqlalchemy Session."""
        return cast(Session, self)


class RecordingPublisher:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any], str]] = []

    def publish(
        self, queue: str, payload: dict[str, Any], *, correlation_id: str
    ) -> None:
        self.messages.append((queue, payload, correlation_id))


@pytest.fixture
def fake_db() -> FakeDb:
    return FakeDb()


@pytest.fixture
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def make_client(
    monkeypatch: pytest.MonkeyPatch, fake_db: FakeDb, publisher: RecordingPublisher
) -> Generator[Callable[..., TestClient], None, None]:
    """Factory building a TestClient with hermetic env-based settings."""
    created: list[TestClient] = []

    def _make(**env: str) -> TestClient:
        base_env = {
            "API_KEY": TEST_API_KEY,
            "JIRA_WEBHOOK_SECRET": TEST_WEBHOOK_SECRET,
            "RATE_LIMIT_PER_MINUTE": "1000",
            "SERVICEBUS_NAMESPACE": "",
            "ENVIRONMENT": "local",
        }
        base_env.update(env)
        for name, value in base_env.items():
            monkeypatch.setenv(name, value)
        get_settings.cache_clear()
        get_rate_limiter.cache_clear()

        app = create_app()
        app.dependency_overrides[get_db] = lambda: fake_db
        app.dependency_overrides[get_publisher] = lambda: publisher
        app.dependency_overrides[get_resolution_graph] = FakeGraph
        client = TestClient(app, raise_server_exceptions=False)
        created.append(client)
        return client

    yield _make
    get_settings.cache_clear()
    get_rate_limiter.cache_clear()


@pytest.fixture
def client(make_client: Callable[..., TestClient]) -> TestClient:
    return make_client()
