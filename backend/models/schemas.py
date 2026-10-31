"""
Pydantic v2 Schemas for OmniStore AI (by Jenna AI Assistant).
Physical-to-Digital Micro-Commerce Engine (Build for Your World).
Provides typed validation for:
  - SAM 3.1: Visual perception, spatial segmentation & item extraction
  - Muse Spark 1.3: Multimodal cognitive reasoning, inventory categorization & local pricing
  - Muse Code: Agentic software synthesis & mobile-first web storefront generation
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ─── Common & Health ────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    assistant: str = "OmniStore AI (Jenna Platform)"
    version: str = "2.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active_providers: Dict[str, bool] = Field(default_factory=dict)


# ─── SAM 3.1 Segmentation ───────────────────────────────────────────────────

class BoundingBox(BaseModel):
    box_id: str = Field(..., description="Unique identifier for the segmented region")
    label: str = Field(..., description="Semantic label or class identified by SAM 3.1")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bbox: List[float] = Field(..., description="[ymin, xmin, ymax, xmax] coordinates (0.0 to 1.0)")
    polygon_mask: Optional[List[List[float]]] = Field(
        default=None,
        description="Optional polygon contour coordinates [[x, y], ...]"
    )
    description: Optional[str] = Field(
        default=None,
        description="Descriptive snippet of the segmented region"
    )
    area: Optional[int] = Field(default=None, description="Pixel mask area")


class SegmentCrop(BaseModel):
    box_id: str
    label: str
    crop_base64: str = Field(..., description="Base64 encoded cropped image segment")
    mime_type: str = "image/png"


class SegmentRequest(BaseModel):
    image_base64: Optional[str] = Field(None, description="Base64 data or data URL of the image")
    image_url: Optional[str] = Field(None, description="Direct URL to fetch image from")
    prompt: Optional[str] = Field("inventory products", description="Prompt to guide segmentation")
    confidence_threshold: float = Field(0.25, ge=0.0, le=1.0, description="Minimum detection confidence")
    generate_crops: bool = Field(True, description="Whether to extract and return cropped segment arrays")
    max_segments: int = Field(20, ge=1, le=50, description="Maximum number of segments to return")


class SegmentResponse(BaseModel):
    success: bool = True
    model_used: str = "sam-3.1"
    image_width: int
    image_height: int
    bounding_boxes: List[BoundingBox]
    crops: List[SegmentCrop] = Field(default_factory=list)
    processing_time_ms: float
    total_segments: int


# ─── OmniStore Context & Muse Spark Reasoning ───────────────────────────────

class MerchantContext(BaseModel):
    store_name: str = Field(..., example="Mama Cass Market", description="Store or trader name")
    currency: str = Field(default="NGN", example="NGN", description="Local currency code")
    location: str = Field(default="Akure, Nigeria", example="Akure, Nigeria", description="Physical market location")
    whatsapp_number: Optional[str] = Field(default="+2348012345678", description="Merchant WhatsApp for 1-click orders")


class InventoryItem(BaseModel):
    item_id: str = Field(..., description="Unique product SKU/ID")
    name: str = Field(..., description="Localized product name")
    category: str = Field(..., description="Product category")
    suggested_price: float = Field(..., description="Fair market price in merchant currency")
    estimated_quantity: int = Field(default=1, description="Estimated stock count from SAM 3.1 masks")
    description: str = Field(..., description="Localized marketing description for customers")
    image_segment_id: str = Field(..., description="Associated SAM 3.1 segment box ID")
    crop_base64: Optional[str] = Field(default=None, description="Thumbnail image of the product")


class StorefrontSchema(BaseModel):
    store_title: str
    currency: str
    location: str
    whatsapp_number: Optional[str] = "+2348012345678"
    category: str = "General Store & Produce"
    inventory: List[InventoryItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EntityObservation(BaseModel):
    entity: str
    box_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    relevance: str = "high"


class StructuredReasoningOutput(BaseModel):
    summary: str = Field(..., description="Executive summary of inventory scan")
    store_meta: Optional[Dict[str, Any]] = None
    inventory: List[InventoryItem] = Field(default_factory=list)
    entities_detected: List[EntityObservation] = Field(default_factory=list)
    detailed_analysis: str = Field(..., description="Step-by-step cognitive reasoning breakdown")
    recommended_actions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.95, ge=0.0, le=1.0)
    safety_assessment: str = Field("safe", description="Content or operational safety rating")


class MultimodalReasonRequest(BaseModel):
    prompt: str = Field("Classify inventory items, suggest fair local prices, and format store catalog")
    merchant_context: Optional[MerchantContext] = None
    segments: Optional[List[SegmentCrop]] = Field(default=None)
    full_image_base64: Optional[str] = Field(default=None)
    model: str = Field("muse-spark-1.3")
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    structured_format: bool = Field(True)


class ReasonResponse(BaseModel):
    success: bool = True
    model_used: str
    structured_output: StructuredReasoningOutput
    store_schema: Optional[StorefrontSchema] = None
    raw_response: Optional[str] = None
    processing_time_ms: float


# ─── Muse Code Agentic Synthesis ───────────────────────────────────────────

class CodeGenerateRequest(BaseModel):
    target_framework: str = Field(default="nextjs14_tailwind", description="Target framework")
    store_schema: StorefrontSchema
    features: List[str] = Field(
        default_factory=lambda: [
            "mobile_first_grid",
            "whatsapp_checkout_integration",
            "inventory_counter",
            "pwa_offline_ready"
        ]
    )


class CodeGenerateResponse(BaseModel):
    status: str = "compiled"
    model_used: str = "muse-code"
    repository_files: Dict[str, str] = Field(default_factory=dict)
    preview_url: Optional[str] = None
    deployment_ready: bool = True
    files_generated: int = 4
    processing_time_ms: float = 120.0


# ─── End-to-End Pipeline Scan ───────────────────────────────────────────────

class PipelineResponse(BaseModel):
    status: str = "completed"
    store_schema: StorefrontSchema
    deploy_url: Optional[str] = None
    generated_files_count: int = 4
    segments_found: int = 0
    processing_time_ms: float = 0.0
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    code_synthesis: Optional[CodeGenerateResponse] = None


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

JobType = Literal["segmentation", "multimodal_reasoning", "full_pipeline", "storefront_scan"]
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
