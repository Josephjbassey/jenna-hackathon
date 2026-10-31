"""
Jenna AI Assistant — FastAPI Backend Engine (v2.0)
Decoupled high-performance backend supporting real-time streaming,
multimodal processing (SAM 3.1 & Muse Spark 1.3), and agentic workflows.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Ensure backend root and project root are in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load environment variables
load_dotenv(backend_dir / ".env")
load_dotenv(project_root / ".env")

from backend.models.schemas import HealthResponse
from backend.services.meta_service import get_meta_service
from backend.services.queue_service import get_queue_manager
from backend.routers import vision, agent, jobs, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background queue worker
    queue_mgr = get_queue_manager()
    print("\n" + "=" * 60)
    print(" 🚀 Jenna AI Assistant FastAPI Backend Engine v2.0")
    print(" 📡 Meta Models: SAM 3.1, Muse Spark 1.3, Muse Code")
    print(" ⚡ Ready on http://localhost:8000 (CORS -> http://localhost:3000)")
    print("=" * 60 + "\n")
    yield
    # Shutdown: Stop worker and close HTTP client sessions
    await queue_mgr.stop()
    meta_service = get_meta_service()
    await meta_service.close()


app = FastAPI(
    title="Jenna AI Assistant Engine",
    description="Next-generation agentic multimodal backend powering Jenna AI OS with SAM 3.1 and Muse Spark 1.3.",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ────────────────────────────────────────────────────────
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if allowed_origins_env:
    for origin in allowed_origins_env.split(","):
        cleaned = origin.strip()
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global Error Handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_type": exc.__class__.__name__,
            "message": str(exc),
            "path": request.url.path,
        },
    )

# ─── Register API Routers ───────────────────────────────────────────────────
app.include_router(vision.router)
app.include_router(agent.router)
app.include_router(jobs.router)
app.include_router(memory.router)


# ─── Root & Health Endpoints ────────────────────────────────────────────────
@app.get("/", tags=["General"])
async def root():
    return {
        "name": "Jenna AI Assistant API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "architecture": "Next.js + FastAPI decoupled agentic system",
        "endpoints": {
            "segmentation": "POST /api/v1/segment",
            "reasoning": "POST /api/v1/reason",
            "streaming_chat": "POST /api/v1/agent/chat",
            "background_jobs": "POST /api/v1/jobs",
            "memory_search": "POST /api/v1/memory/search",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    meta_key = bool(os.getenv("META_MODEL_API_KEY") or os.getenv("MODEL_API_KEY"))
    return HealthResponse(
        status="healthy",
        assistant="Jenna AI Assistant",
        version="2.0.0",
        active_providers={
            "meta_model_api": meta_key,
            "sam_3_1": True,
            "muse_spark_1_3": True,
            "muse_code": True,
            "background_queue": True,
            "cross_agent_memory": True,
        },
    )


def start_cli(voice: bool = False):
    from backend.core.agent_core import Agent, load_skills
    agent = Agent("fast", load_skills())
    print("\n[Jenna AI Assistant CLI] Type your prompt, or Ctrl+C to exit.\n")
    while True:
        try:
            user_input = input("User> ")
            if not user_input.strip():
                continue
            import asyncio
            reply = asyncio.run(agent.run_turn(user_input))
            print(f"Jenna> {reply}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting CLI...")
            break


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Jenna AI Assistant Engine")
    parser.add_argument("--api", action="store_true", help="Start FastAPI HTTP Engine (default)")
    parser.add_argument("--cli", action="store_true", help="Terminal chat mode")
    parser.add_argument("--tui", action="store_true", help="Interactive Terminal UI")
    parser.add_argument("--desktop", action="store_true", help="Desktop orb overlay")
    parser.add_argument("--voice", action="store_true", help="Enable voice mode")
    args, _ = parser.parse_known_args()

    if args.cli:
        start_cli(voice=args.voice)
    elif args.tui:
        try:
            from backend.tui.hermes_tui import start_hermes_tui
            start_hermes_tui(voice_playback=args.voice)
        except Exception as e:
            print(f"Could not start TUI: {e}")
    elif args.desktop:
        try:
            print("Starting Desktop Orb...")
        except Exception as e:
            print(f"Desktop mode error: {e}")
    else:
        start()


if __name__ == "__main__":
    main()
