"""
Background Jobs and Webhook Router for Jenna AI Assistant.
Manages long-running multimodal inference pipelines, polling, and status tracking.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from backend.models.schemas import JobSubmitRequest, JobStatusResponse
from backend.services.queue_service import TaskQueueManager, get_queue_manager

router = APIRouter(prefix="/api/v1/jobs", tags=["Background Jobs & Webhooks"])


@router.post(
    "",
    response_model=JobStatusResponse,
    summary="Submit async multimodal inference job",
    description="Enqueues long-running tasks (SAM 3.1 segmentation, Muse Spark reasoning, or full pipeline) with optional webhook delivery.",
)
async def submit_job(
    req: JobSubmitRequest,
    queue: TaskQueueManager = Depends(get_queue_manager),
) -> JobStatusResponse:
    try:
        return queue.submit_job(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to submit background job: {str(exc)}")


@router.get(
    "",
    response_model=List[JobStatusResponse],
    summary="List all background jobs",
)
async def list_jobs(
    limit: int = 50,
    queue: TaskQueueManager = Depends(get_queue_manager),
) -> List[JobStatusResponse]:
    return queue.list_jobs(limit=limit)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get background job status and results",
)
async def get_job(
    job_id: str,
    queue: TaskQueueManager = Depends(get_queue_manager),
) -> JobStatusResponse:
    job = queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job
