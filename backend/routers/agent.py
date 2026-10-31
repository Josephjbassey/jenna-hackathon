"""
Agent Chat Router for Jenna AI Assistant.
Provides endpoints for real-time streaming text generation via StreamingResponse,
agent squad role routing, and tool calling metadata.
"""
from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest, ChatStreamChunk
from backend.services.meta_service import MetaModelService, get_meta_service

router = APIRouter(prefix="/api/v1/agent", tags=["Agent & Chat"])

SQUAD_ROLES_INFO = [
    {
        "role": "commander",
        "name": "Jenna Commander",
        "model": "muse-spark-1.3",
        "description": "Executive coordinator, voice conversationalist, and task decomposer.",
        "capabilities": ["Orchestration", "Task Delegation", "Dialogue Flow"],
    },
    {
        "role": "planner",
        "name": "Jenna Planner",
        "model": "muse-spark-1.3",
        "description": "Multi-step reasoning, structured task planning, agent orchestration.",
        "capabilities": ["Hierarchical Planning", "Dependency Mapping", "Verification"],
    },
    {
        "role": "coder",
        "name": "Jenna Engineer",
        "model": "muse-code",
        "description": "Code generation, debugging, refactoring, terminal tasks.",
        "capabilities": ["Full-Stack Dev", "Bug Fixing", "AST Validation"],
    },
    {
        "role": "researcher",
        "name": "Jenna Scholar",
        "model": "muse-spark-1.3",
        "description": "Web research, factual aggregation, documentation, vision analysis.",
        "capabilities": ["Deep Research", "Multimodal Grounding", "Synthesis"],
    },
    {
        "role": "desktop",
        "name": "Jenna Operator",
        "model": "sam-3.1",
        "description": "Desktop automation, GUI inspection, click-and-type execution.",
        "capabilities": ["SAM 3.1 Segmentation", "Screen Inspection", "Window Tracking"],
    },
]


@router.get("/roles", summary="Get squad agent roles and assigned models")
async def get_roles():
    return {"roles": SQUAD_ROLES_INFO}


@router.post(
    "/chat",
    summary="Real-time streaming agent chat",
    description="Streams token-by-token output using FastAPI StreamingResponse and Server-Sent Events (SSE).",
)
async def chat_endpoint(
    req: ChatRequest,
    meta_service: MetaModelService = Depends(get_meta_service),
):
    try:
        messages_dicts = [m.model_dump() for m in req.messages]
        model_name = req.model or ("muse-code" if req.agent_role == "coder" else "muse-spark-1.3")

        if req.stream:
            async def event_generator():
                try:
                    async for chunk in meta_service.stream_chat(
                        messages=messages_dicts,
                        agent_role=req.agent_role,
                        model=model_name,
                        temperature=req.temperature,
                        enable_tools=req.enable_tools,
                    ):
                        yield f"data: {chunk.model_dump_json()}\n\n"
                    # Emit final done signal
                    yield "data: [DONE]\n\n"
                except Exception as stream_err:
                    err_chunk = ChatStreamChunk(
                        delta=f"\n[Stream Error: {str(stream_err)}]",
                        finish_reason="error",
                        agent_role=req.agent_role,
                    )
                    yield f"data: {err_chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            # Non-streaming accumulation
            full_text = []
            async for chunk in meta_service.stream_chat(
                messages=messages_dicts,
                agent_role=req.agent_role,
                model=model_name,
                temperature=req.temperature,
                enable_tools=req.enable_tools,
            ):
                if chunk.delta:
                    full_text.append(chunk.delta)
            
            return {
                "role": "assistant",
                "content": "".join(full_text),
                "agent_role": req.agent_role,
                "model": model_name,
            }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(exc)}")
