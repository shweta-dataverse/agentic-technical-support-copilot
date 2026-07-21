"""Jira webhook intake: HMAC verify → validate → publish → 202."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import ValidationError

from copilot.api.deps import PublisherDep, SettingsDep
from copilot.api.middleware import get_correlation_id
from copilot.api.schemas import AcceptedResponse, JiraWebhookPayload
from copilot.security.hmac_verify import verify_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/jira", status_code=status.HTTP_202_ACCEPTED, response_model=AcceptedResponse
)
async def jira_webhook(
    request: Request,
    settings: SettingsDep,
    publisher: PublisherDep,
    x_hub_signature: Annotated[str | None, Header(alias="X-Hub-Signature")] = None,
) -> AcceptedResponse:
    body = await request.body()
    if not verify_signature(settings.jira_webhook_secret, body, x_hub_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid webhook signature"
        )
    try:
        payload = JiraWebhookPayload.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload does not match the jira webhook schema",
        ) from exc

    correlation_id = get_correlation_id()
    publisher.publish(
        settings.queue_ticket_ingest,
        {
            "ticket_id": payload.issue.key,
            "summary": payload.issue.fields.summary,
            "description": payload.issue.fields.description or "",
            "event": payload.webhookEvent,
        },
        correlation_id=correlation_id,
    )
    return AcceptedResponse(correlation_id=correlation_id)
