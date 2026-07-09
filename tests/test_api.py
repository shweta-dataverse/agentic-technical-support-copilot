from __future__ import annotations


def test_health_is_public_and_reports_provider(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "anthropic"


def test_resolve_requires_api_key(client):
    resp = client.post(
        "/v1/resolve",
        json={"title": "CPU STOP", "description": "SF LED on after update"},
    )
    assert resp.status_code == 401


def test_resolve_returns_draft_with_valid_key(client):
    resp = client.post(
        "/v1/resolve",
        headers={"X-API-Key": "test-key"},
        json={"title": "CPU STOP", "description": "SF LED on after firmware update"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["resolution"].startswith("resolution for:")
    assert body["provider"] == "fake"
    assert body["output_tokens"] == 20


def test_resolve_validates_empty_ticket(client):
    resp = client.post(
        "/v1/resolve",
        headers={"X-API-Key": "test-key"},
        json={"title": "", "description": ""},
    )
    assert resp.status_code == 422
