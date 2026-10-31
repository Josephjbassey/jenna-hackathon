"""
Pydantic v2 Schemas for Jenna AI Assistant API.
Provides typed validation for multimodal inputs, SAM 3.1 segmentation,
Muse Spark reasoning, streaming chat, and background jobs.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ─── Common & Health ────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    assistant: str = "Jenna AI Assistant"
    version: str = "2.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active_providers: Dict[str, bool] = Field(default_factory=dict)


# ─── SAM 3.1 Segmentation ───────────────────────────────────────────────────

class BoundingBox(BaseModel):
    box_id: str = Field(..., description="Unique identifier for the segmented region")
    label: str = Field(..., description="Semantic label or class identified by SAM 3.1")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    # Coordinates normalized 0.0 to 1.0 or pixel coordinates: [ymin, xmin, ymax, xmax]
    bbox: List[float] = Field(..., description="[ymin, xmin, ymax, xmax] coordinates (0.0 to 1.0)")
    polygon_mask: Optional[List[List[float]]] = Field(
        default=None,
        description="Optional polygon contour coordinates [[x, y], ...]"
    )
    description: Optional[str] = Field(
        default=None,
        description="Descriptive snippet of the segmented region"
    )


class SegmentCrop(BaseModel):
    box_id: str
    label: str
    crop_base64: str = Field(..., description="Base64 encoded cropped image segment")
    mime_type: str = "image/png"


class SegmentRequest(BaseModel):
    image_base64: Optional[str] = Field(None, description="Base64 data or data URL of the image")
    image_url: Optional[str] = Field(None, description="Direct URL to fetch image from")
    prompt: Optional[str] = Field("", description="Optional text prompt to guide segmentation")
    confidence_threshold: float = Field(0.25, ge=0.0, le=1.0, description="Minimum detection confidence")
    generate_crops: bool = Field(True, description="Whether to extract and return cropped segment arrays")
    max_segments: int = Field(10, ge=1, le=50, description="Maximum number of segments to return")


class SegmentResponse(BaseModel):
    success: bool = True
    model_used: str = "sam-3.1"
    image_width: int
    image_height: int
    bounding_boxes: List[BoundingBox]
    crops: List[SegmentCrop] = Field(default_factory=list)
    processing_time_ms: float
    total_segments: int


# ─── Muse Spark Multimodal Reasoning ───────────────────────────────────────

class EntityObservation(BaseModel):
    entity: str
    box_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    relevance: str = "high"


class StructuredReasoningOutput(BaseModel):
    summary: str = Field(..., description="Executive summary of the multimodal scene")
    entities_detected: List[EntityObservation] = Field(default_factory=list)
    detailed_analysis: str = Field(..., description="In-depth step-by-step reasoning")
    recommended_actions: List[str] = Field(default_factory=list, description="Prescribed actions for agent execution")
    confidence_score: float = Field(0.95, ge=0.0, le=1.0)
    safety_assessment: str = Field("safe", description="Content or operational safety rating")


class MultimodalReasonRequest(BaseModel):
    prompt: str = Field(..., description="User query or reasoning instruction")
    segments: Optional[List[SegmentCrop]] = Field(default=None, description="Cropped image segments to analyze")
    full_image_base64: Optional[str] = Field(default=None, description="Full image base64 if available")
    model: str = Field("muse-spark-1.3", description="Meta Model identifier: muse-spark-1.3 or muse-wonder-1.0")
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    structured_format: bool = Field(True, description="Enforce Pydantic schema validation on output")


class ReasonResponse(BaseModel):
    success: bool = True
    model_used: str
    structured_output: StructuredReasoningOutput
    raw_response: Optional[str] = None
    processing_time_ms: float


# ─── Real-time Streaming Agent Chat ─────────────────────────────────────────

AgentRole = Literal["commander", "planner", "coder", "researcher", "desktop"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    image_base64: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    agent_role: AgentRole = "commander"
    model: Optional[str] = None
    stream: bool = True
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    enable_tools: bool = True
    thread_id: str = "default"


class ChatStreamChunk(BaseModel):
    delta: str = ""
    role: str = "assistant"
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    agent_role: Optional[str] = None


# ─── Async Background Jobs & Webhooks ──────────────────────────────────────

JobType = Literal["segmentation", "multimodal_reasoning", "full_pipeline"]
JobStatus = Literal["queued", "processing", "completed", "failed"]


class JobSubmitRequest(BaseModel):
    job_type: JobType
    payload: Dict[str, Any]
    webhook_url: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    progress: float = Field(0.0, ge=0.0, le=1.0)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# ─── Memory Endpoints ───────────────────────────────────────────────────────

class MemorySearchRequest(BaseModel):
    query: str
    agent: Optional[str] = None
    days: int = 30
    limit: int = 50


class MemoryRecordSchema(BaseModel):
    agent: str
    session_id: str
    timestamp: str
    role: str
    text: str
    cwd: Optional[str] = None
    model: Optional[str] = None
