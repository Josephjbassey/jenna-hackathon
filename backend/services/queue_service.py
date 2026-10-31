"""
Async Background Queue and Webhook Dispatch Service.
Handles long-running multimodal inference tasks (SAM 3.1 & Muse Spark pipelines)
with real-time progress tracking, error handling, and webhook delivery.
"""
from __future__ import annotations
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any
import httpx

from backend.models.schemas import JobSubmitRequest, JobStatusResponse, JobType, JobStatus
from backend.services.meta_service import get_meta_service

logger = logging.getLogger("jenna.queue_service")


class TaskQueueManager:
    """Manages async execution, state, and webhook dispatch for background AI tasks."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running: bool = False

    def start(self):
        if not self._running:
            self._running = True
            self._ensure_worker()

    def _ensure_worker(self):
        if self._worker_task is None or self._worker_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._running = True
                self._worker_task = loop.create_task(self._worker_loop())
                logger.info("Background task queue worker task started.")
            except RuntimeError:
                # No active loop in current thread (e.g. running in threadpool)
                pass

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Background task queue worker stopped.")

    def submit_job(self, req: JobSubmitRequest) -> JobStatusResponse:
        """Enqueue a new inference job and return initial status."""
        job_id = f"job-{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow()
        job_record = {
            "job_id": job_id,
            "job_type": req.job_type,
            "status": "queued",
            "progress": 0.0,
            "payload": req.payload,
            "webhook_url": req.webhook_url,
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }
        self._jobs[job_id] = job_record
        self._queue.put_nowait(job_id)
        self._ensure_worker()
        return self._to_schema(job_record)

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        record = self._jobs.get(job_id)
        if not record:
            return None
        return self._to_schema(record)

    def list_jobs(self, limit: int = 50) -> List[JobStatusResponse]:
        sorted_records = sorted(
            self._jobs.values(), key=lambda r: r["created_at"], reverse=True
        )[:limit]
        return [self._to_schema(r) for r in sorted_records]

    def _to_schema(self, record: Dict[str, Any]) -> JobStatusResponse:
        return JobStatusResponse(
            job_id=record["job_id"],
            job_type=record["job_type"],
            status=record["status"],
            progress=record["progress"],
            result=record["result"],
            error=record["error"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            completed_at=record["completed_at"],
        )

    async def _worker_loop(self):
        """Continuously process background queue items."""
        while self._running:
            try:
                job_id = await self._queue.get()
                await self._process_job(job_id)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in background worker loop: {e}")
                await asyncio.sleep(0.5)

    async def _process_job(self, job_id: str):
        record = self._jobs.get(job_id)
        if not record:
            return

        meta = get_meta_service()
        record["status"] = "processing"
        record["progress"] = 0.1
        record["updated_at"] = datetime.utcnow()

        try:
            job_type = record["job_type"]
            payload = record["payload"]

            if job_type == "segmentation":
                record["progress"] = 0.4
                resp = await meta.segment_image(
                    image_base64=payload.get("image_base64"),
                    prompt=payload.get("prompt", ""),
                    confidence_threshold=payload.get("confidence_threshold", 0.25),
                )
                record["progress"] = 0.9
                record["result"] = resp.model_dump()

            elif job_type == "multimodal_reasoning":
                record["progress"] = 0.5
                resp = await meta.reason_multimodal(
                    prompt=payload.get("prompt", "Analyze segments"),
                    segments=payload.get("segments"),
                    full_image_base64=payload.get("full_image_base64"),
                )
                record["progress"] = 0.9
                record["result"] = resp.model_dump()

            elif job_type == "full_pipeline":
                # Step 1: Segment image
                record["progress"] = 0.3
                seg_resp = await meta.segment_image(
                    image_base64=payload.get("image_base64"),
                    prompt=payload.get("prompt", ""),
                )
                record["progress"] = 0.6

                # Step 2: Reason on crops
                reason_resp = await meta.reason_multimodal(
                    prompt=payload.get("reason_prompt", "Evaluate detected regions"),
                    segments=seg_resp.crops,
                )
                record["progress"] = 0.95
                record["result"] = {
                    "segmentation": seg_resp.model_dump(),
                    "reasoning": reason_resp.model_dump(),
                }

            record["status"] = "completed"
            record["progress"] = 1.0
            record["completed_at"] = datetime.utcnow()
            record["updated_at"] = datetime.utcnow()

        except Exception as exc:
            logger.error(f"Job {job_id} failed: {exc}", exc_info=True)
            record["status"] = "failed"
            record["error"] = str(exc)
            record["updated_at"] = datetime.utcnow()

        # Webhook Notification Dispatch
        webhook_url = record.get("webhook_url")
        if webhook_url:
            asyncio.create_task(self._dispatch_webhook(webhook_url, self._to_schema(record)))

    async def _dispatch_webhook(self, url: str, job_status: JobStatusResponse):
        """Asynchronously dispatch completion payload to caller's webhook."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json=job_status.model_dump(mode="json"),
                    headers={"Content-Type": "application/json", "User-Agent": "Jenna-Webhook-Dispatcher/2.0"},
                )
                logger.info(f"Dispatched webhook for {job_status.job_id} to {url}: status {res.status_code}")
        except Exception as e:
            logger.warning(f"Failed to deliver webhook for {job_status.job_id} to {url}: {e}")


# Singleton task manager
_queue_manager: Optional[TaskQueueManager] = None


def get_queue_manager() -> TaskQueueManager:
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = TaskQueueManager()
        _queue_manager.start()
    return _queue_manager
