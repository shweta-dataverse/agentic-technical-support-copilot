"""Job status polling."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select

from copilot.api.deps import DbDep, require_api_key
from copilot.api.schemas import JobResponse
from copilot.db.models import Job, Resolution
from copilot.exceptions import TicketNotFoundError

router = APIRouter(
    prefix="/v1/jobs", tags=["jobs"], dependencies=[Depends(require_api_key)]
)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID, session: DbDep) -> JobResponse:
    job = session.get(Job, job_id)
    if job is None:
        raise TicketNotFoundError(f"job {job_id} not found")

    result = None
    if job.status == "done" and job.ticket_id is not None:
        resolution = session.execute(
            select(Resolution)
            .where(Resolution.ticket_id == job.ticket_id)
            .order_by(Resolution.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if resolution is not None:
            result = {
                "resolution_steps": resolution.resolution_steps,
                "citations": resolution.citations,
                "confidence": resolution.confidence,
                "escalate": resolution.escalate,
            }

    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        ticket_id=job.ticket_id,
        error_class=job.error_class,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        result=result,
    )
