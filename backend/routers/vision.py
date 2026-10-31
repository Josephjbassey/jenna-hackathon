"""
Vision and Multimodal Reasoning Router for Jenna AI Assistant.
Provides endpoints for:
  - POST /api/v1/segment: Interface with SAM 3.1 for bounding boxes + crop arrays.
  - POST /api/v1/reason: Pipeline visual segments into muse-spark-1.3 for structured JSON output.
"""
from __future__ import annotations
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional

from backend.models.schemas import (
    SegmentRequest, SegmentResponse,
    MultimodalReasonRequest, ReasonResponse
)
from backend.services.meta_service import MetaModelService, get_meta_service

router = APIRouter(prefix="/api/v1", tags=["Vision & Multimodal"])


@router.post(
    "/segment",
    response_model=SegmentResponse,
    summary="Segment visual frame with SAM 3.1",
    description="Accepts an image payload (base64 or direct URL) and returns detected bounding boxes and cropped image segments.",
)
async def segment_endpoint(
    req: SegmentRequest,
    meta_service: MetaModelService = Depends(get_meta_service),
) -> SegmentResponse:
    try:
        return await meta_service.segment_image(
            image_base64=req.image_base64,
            image_url=req.image_url,
            prompt=req.prompt or "",
            confidence_threshold=req.confidence_threshold,
            generate_crops=req.generate_crops,
            max_segments=req.max_segments,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SAM 3.1 segmentation error: {str(exc)}")


@router.post(
    "/segment/upload",
    response_model=SegmentResponse,
    summary="Segment uploaded image file with SAM 3.1",
    description="Direct multipart file upload for visual segmentation.",
)
async def segment_upload_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(""),
    confidence_threshold: float = Form(0.25),
    meta_service: MetaModelService = Depends(get_meta_service),
) -> SegmentResponse:
    try:
        contents = await file.read()
        b64_str = base64.b64encode(contents).decode("utf-8")
        data_url = f"data:{file.content_type or 'image/png'};base64,{b64_str}"
        return await meta_service.segment_image(
            image_base64=data_url,
            prompt=prompt or "",
            confidence_threshold=confidence_threshold,
            generate_crops=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image upload segmentation failed: {str(exc)}")


@router.post(
    "/reason",
    response_model=ReasonResponse,
    summary="Multimodal reasoning with Muse Spark 1.3",
    description="Pipelines visual segments into muse-spark-1.3 for in-depth reasoning with Pydantic structured output validation.",
)
async def reason_endpoint(
    req: MultimodalReasonRequest,
    meta_service: MetaModelService = Depends(get_meta_service),
) -> ReasonResponse:
    try:
        return await meta_service.reason_multimodal(
            prompt=req.prompt,
            segments=req.segments,
            full_image_base64=req.full_image_base64,
            model=req.model,
            temperature=req.temperature,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Muse Spark reasoning error: {str(exc)}")
