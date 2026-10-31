"""
OmniStore AI Pipeline Router.
Implements the 3-model architecture:
  1. SAM 3.1: POST /api/v1/segment (visual perception & spatial masks)
  2. Muse Spark 1.3: POST /api/v1/reason (cognitive market reasoning & pricing)
  3. Muse Code: POST /api/v1/code/generate (storefront synthesis)
  4. End-to-End: POST /api/v1/scan (unified upload -> scan -> catalog -> store deploy)
"""
from __future__ import annotations
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, Dict, Any

from backend.models.schemas import (
    SegmentRequest, SegmentResponse,
    MultimodalReasonRequest, ReasonResponse,
    MerchantContext, CodeGenerateRequest, CodeGenerateResponse,
    PipelineResponse, StorefrontSchema
)
from backend.services.meta_service import MetaModelService, get_meta_service

router = APIRouter(prefix="/api/v1", tags=["OmniStore Pipeline"])


@router.post(
    "/scan",
    response_model=PipelineResponse,
    summary="End-to-End Store Scan Pipeline (SAM 3.1 + Muse Spark + Muse Code)",
    description="Accepts physical storefront/shelf photo, segments goods via SAM 3.1, classifies & prices via Muse Spark, and synthesizes Next.js storefront code via Muse Code.",
)
async def process_store_scan_endpoint(
    store_name: str = Form("Mama Cass Market"),
    currency: str = Form("NGN"),
    location: str = Form("Akure, Nigeria"),
    whatsapp_number: Optional[str] = Form("+2348012345678"),
    file: UploadFile = File(...),
    meta_service: MetaModelService = Depends(get_meta_service),
) -> PipelineResponse:
    try:
        contents = await file.read()
        b64_str = base64.b64encode(contents).decode("utf-8")
        data_url = f"data:{file.content_type or 'image/jpeg'};base64,{b64_str}"
        context = MerchantContext(
            store_name=store_name,
            currency=currency,
            location=location,
            whatsapp_number=whatsapp_number,
        )
        return await meta_service.process_store_scan(
            image_base64=data_url,
            context=context,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Store scan pipeline failed: {str(exc)}")


@router.post(
    "/scan/json",
    response_model=PipelineResponse,
    summary="End-to-End Store Scan Pipeline (JSON Base64 Payload)",
)
async def process_store_scan_json_endpoint(
    payload: Dict[str, Any],
    meta_service: MetaModelService = Depends(get_meta_service),
) -> PipelineResponse:
    try:
        image_b64 = payload.get("image_base64", "")
        context_data = payload.get("merchant_context", {})
        context = MerchantContext(
            store_name=context_data.get("store_name", "Mama Cass Market"),
            currency=context_data.get("currency", "NGN"),
            location=context_data.get("location", "Akure, Nigeria"),
            whatsapp_number=context_data.get("whatsapp_number", "+2348012345678"),
        )
        return await meta_service.process_store_scan(
            image_base64=image_b64,
            context=context,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Store scan error: {str(exc)}")


@router.post(
    "/segment",
    response_model=SegmentResponse,
    summary="1. SAM 3.1 Visual Segmentation",
    description="Extracts spatial bounding boxes, object masks, and crop arrays from physical goods.",
)
async def segment_endpoint(
    req: SegmentRequest,
    meta_service: MetaModelService = Depends(get_meta_service),
) -> SegmentResponse:
    try:
        return await meta_service.segment_image(
            image_base64=req.image_base64,
            image_url=req.image_url,
            prompt=req.prompt or "inventory products",
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
)
async def segment_upload_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("inventory products"),
    confidence_threshold: float = Form(0.25),
    meta_service: MetaModelService = Depends(get_meta_service),
) -> SegmentResponse:
    try:
        contents = await file.read()
        b64_str = base64.b64encode(contents).decode("utf-8")
        data_url = f"data:{file.content_type or 'image/png'};base64,{b64_str}"
        return await meta_service.segment_image(
            image_base64=data_url,
            prompt=prompt or "inventory products",
            confidence_threshold=confidence_threshold,
            generate_crops=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image upload segmentation failed: {str(exc)}")


@router.post(
    "/reason",
    response_model=ReasonResponse,
    summary="2. Muse Spark Multimodal Market Reasoning",
    description="Takes cropped visual segments + merchant context, classifies items, suggests local market prices, and produces structured StorefrontSchema.",
)
async def reason_endpoint(
    req: MultimodalReasonRequest,
    meta_service: MetaModelService = Depends(get_meta_service),
) -> ReasonResponse:
    try:
        return await meta_service.reason_multimodal(
            prompt=req.prompt,
            merchant_context=req.merchant_context,
            segments=req.segments,
            full_image_base64=req.full_image_base64,
            model=req.model,
            temperature=req.temperature,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Muse Spark reasoning error: {str(exc)}")


@router.post(
    "/code/generate",
    response_model=CodeGenerateResponse,
    summary="3. Muse Code Storefront Code Synthesis",
    description="Generates Next.js 14 / Tailwind mobile storefront codebase and WhatsApp checkout route from a store schema.",
)
async def code_generate_endpoint(
    req: CodeGenerateRequest,
    meta_service: MetaModelService = Depends(get_meta_service),
) -> CodeGenerateResponse:
    try:
        return await meta_service.synthesize_storefront(
            schema=req.store_schema,
            target_framework=req.target_framework,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Muse Code synthesis error: {str(exc)}")
