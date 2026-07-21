"""API surface tests: auth, rate limiting, problem+json, webhook HMAC,
job lifecycle, correlation IDs."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from copilot.db.models import Job, Ticket
from copilot.security.hmac_verify import compute_signature
from tests.conftest import TEST_API_KEY, TEST_WEBHOOK_SECRET, FakeDb, RecordingPublisher

AUTH = {"X-API-Key": TEST_API_KEY}


def make_ticket(ticket_id: str = "SUP-1") -> Ticket:
    ticket = Ticket(
        ticket_id=ticket_id,
        summary="CPU STOP",
        description="SF LED on",
        status="open",
        source="webhook",
    )
    ticket.created_at = datetime.now(UTC)
    ticket.updated_at = datetime.now(UTC)
    return ticket


# -- health / auth ----------------------------------------------------------


def test_health_is_public(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_missing_api_key_is_401(client: TestClient) -> None:
    assert client.post("/v1/resolve", json={"title": "t", "description": "d"}).status_code == 401


def test_rate_limit_returns_429_with_retry_after(
    make_client: Callable[..., TestClient], fake_db: FakeDb
) -> None:
    client = make_client(RATE_LIMIT_PER_MINUTE="2")
    fake_db.objects[(Ticket, "SUP-1")] = make_ticket()
    for _ in range(2):
        assert client.get("/v1/tickets/SUP-1", headers=AUTH).status_code == 200
    resp = client.get("/v1/tickets/SUP-1", headers=AUTH)
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


# -- problem+json -----------------------------------------------------------


def test_unknown_ticket_is_problem_json_404(client: TestClient) -> None:
    resp = client.get("/v1/tickets/NOPE", headers=AUTH)
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["type"] == "urn:copilot:error:ticketnotfound"
    assert body["correlation_id"]


def test_correlation_id_round_trip(client: TestClient) -> None:
    resp = client.get("/health", headers={"X-Correlation-ID": "corr-123"})
    assert resp.headers["X-Correlation-ID"] == "corr-123"


def test_oversized_request_is_413(client: TestClient) -> None:
    resp = client.post(
        "/v1/resolve",
        headers={**AUTH, "Content-Length": "99999999"},
        json={"title": "t", "description": "d"},
    )
    assert resp.status_code == 413


def test_security_headers_present(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


# -- webhook ----------------------------------------------------------------

WEBHOOK_BODY = (
    b'{"webhookEvent": "jira:issue_created", "issue": {"key": "SUP-9",'
    b' "fields": {"summary": "CPU STOP", "description": "SF LED on"}}}'
)


def test_webhook_valid_signature_publishes_and_202(
    client: TestClient, publisher: RecordingPublisher
) -> None:
    resp = client.post(
        "/webhooks/jira",
        content=WEBHOOK_BODY,
        headers={"X-Hub-Signature": compute_signature(TEST_WEBHOOK_SECRET, WEBHOOK_BODY)},
    )
    assert resp.status_code == 202
    queue, payload, correlation_id = publisher.messages[0]
    assert queue == "ticket-ingest"
    assert payload["ticket_id"] == "SUP-9"
    assert correlation_id == resp.json()["correlation_id"]


def test_webhook_bad_signature_is_401(
    client: TestClient, publisher: RecordingPublisher
) -> None:
    resp = client.post(
        "/webhooks/jira", content=WEBHOOK_BODY, headers={"X-Hub-Signature": "sha256=wrong"}
    )
    assert resp.status_code == 401
    assert not publisher.messages


def test_webhook_invalid_payload_is_422(client: TestClient) -> None:
    body = b'{"not": "a jira payload"}'
    resp = client.post(
        "/webhooks/jira",
        content=body,
        headers={"X-Hub-Signature": compute_signature(TEST_WEBHOOK_SECRET, body)},
    )
    assert resp.status_code == 422


# -- async job flow ---------------------------------------------------------


def test_enqueue_resolution_creates_job_and_publishes(
    client: TestClient, fake_db: FakeDb, publisher: RecordingPublisher
) -> None:
    fake_db.objects[(Ticket, "SUP-1")] = make_ticket()
    resp = client.post("/v1/tickets/SUP-1/resolve", headers=AUTH)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert fake_db.committed
    queue, payload, _ = publisher.messages[0]
    assert queue == "ticket-resolve"
    assert payload == {"job_id": job_id, "ticket_id": "SUP-1"}


def test_job_status_endpoint(client: TestClient, fake_db: FakeDb) -> None:
    job = Job(job_type="resolve", status="queued", ticket_id="SUP-1")
    job.id = uuid.uuid4()
    job.created_at = datetime.now(UTC)
    fake_db.objects[(Job, job.id)] = job
    resp = client.get(f"/v1/jobs/{job.id}", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


# -- sync resolve -----------------------------------------------------------


def test_sync_resolve_returns_resolution_and_persists(
    client: TestClient, fake_db: FakeDb
) -> None:
    resp = client.post(
        "/v1/resolve", headers=AUTH, json={"title": "CPU STOP", "description": "SF LED"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["resolution_steps"]
    assert body["citations"][0]["page"] == 338
    assert body["confidence"] == 0.9
    assert fake_db.committed
    assert len(fake_db.added) == 2  # ticket + resolution


def test_sync_resolve_validates_empty_ticket(client: TestClient) -> None:
    resp = client.post("/v1/resolve", headers=AUTH, json={"title": "", "description": ""})
    assert resp.status_code == 422
