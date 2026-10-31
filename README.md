# Jenna AI Assistant — Decoupled Next.js + FastAPI Multimodal Architecture

**Track:** Indie Developer | **Team:** Joseph John  
**Hackathon:** Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026)  
**Problem Statement:** Build for Your World — High-Performance Agentic Multimodal AI OS  

---

## Architecture Overview

Jenna has been upgraded from a coupled prototype into a production-grade, decoupled monorepo architecture:

- **Frontend (`frontend/`):** Next.js 14+ (App Router, TypeScript, Tailwind CSS) featuring real-time Web Streams chat, interactive HTML5 SAM 3.1 visual segmentation canvas with bounding box overlays, structured Muse Spark reasoning visualizers, and background task queue trackers.
- **Backend (`backend/`):** Python FastAPI engine powered by Pydantic v2, async HTTPX connection pooling with exponential backoff retries, and high-fidelity fallback simulation for local and offline execution.
- **Meta Model API Layer:** Native support for:
  - `sam-3.1`: Visual segmentation, bounding box coordinate normalization (`[ymin, xmin, ymax, xmax]`), and segment crop array extraction.
  - `muse-spark-1.3`: Multimodal reasoning, agent orchestration, and structured Pydantic JSON validation.
  - `muse-code`: Full-stack code generation, refactoring, and AST inspection.
  - `muse-voice-transcribe-1.0`: High-speed audio transcription.
- **Cross-Agent Memory & Skills:** SQLite + FTS5 full-text search indexing conversation history across Hermes, Claude, and Antigravity harnesses.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NEXT.JS 14+ APP ROUTER FRONTEND                       │
│  (React 18, TypeScript, Tailwind CSS, Web Streams API, HTML5 Canvas)        │
│                                                                             │
│   ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│   │ Streaming Chat UI    │  │ SAM 3.1 Overlay      │  │ Muse Spark       │  │
│   │ (SSE Token Feed)     │  │ (Canvas Bounding Box)│  │ (Structured JSON)│  │
│   └──────────┬───────────┘  └──────────┬───────────┘  └────────┬─────────┘  │
└──────────────┼─────────────────────────┼───────────────────────┼────────────┘
               │ HTTP / Stream           │ POST /segment         │ POST /reason
               ▼                         ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI BACKEND ENGINE                             │
│       (Uvicorn ASGI, Pydantic v2, Async HTTPX, Background Worker Queue)     │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  API Routers (/api/v1)                                              │   │
│   │  • /agent/chat       • /segment      • /reason                      │   │
│   │  • /jobs             • /memory       • /health                      │   │
│   └──────────────────────────────────┬──────────────────────────────────┘   │
│                                      │                                      │
│   ┌──────────────────────────────────┴──────────────────────────────────┐   │
│   │  MetaModelService (backend/services/meta_service.py)                │   │
│   │  • Async HTTPX Client  • Exponential Backoff  • Fallback Engine     │   │
│   └──────────────────────────────────┬──────────────────────────────────┘   │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
     ┌──────────────────────┐                     ┌──────────────────────┐
     │  Meta Model API      │                     │  Local Storage       │
     │  • sam-3.1           │                     │  • SQLite + FTS5     │
     │  • muse-spark-1.3    │                     │  • Obsidian Vault    │
     │  • muse-code         │                     │  • Sandbox Outbox    │
     └──────────────────────┘                     └──────────────────────┘
```

---

## Squad Roles & Model Assignment

| Role | Primary Model | Function & Capabilities |
|------|--------------|-------------------------|
| **Commander** | `muse-spark-1.3` | Executive coordinator, voice conversationalist, and task decomposer |
| **Planner** | `muse-spark-1.3` | Hierarchical planning, multi-step dependency analysis, validation |
| **Engineer** | `muse-code` | Code generation, debugging, refactoring, terminal execution |
| **Scholar** | `muse-spark-1.3` / `muse-wonder` | Web research, factual synthesis, visual document analysis |
| **Operator** | `sam-3.1` | Desktop GUI inspection, visual bounding box localization |

---

## API Specification (`/api/v1`)

### 1. Visual Segmentation (`POST /api/v1/segment`)
Accepts an image payload (base64 data URL or external URL) and returns detected bounding boxes and cropped image segments:
```json
{
  "image_base64": "data:image/png;base64,...",
  "prompt": "Locate terminal console and code window",
  "confidence_threshold": 0.25,
  "generate_crops": true,
  "max_segments": 10
}
```
**Response:**
```json
{
  "success": true,
  "model_used": "sam-3.1",
  "image_width": 1280,
  "image_height": 720,
  "bounding_boxes": [
    {
      "box_id": "box-seg-001",
      "label": "Code Editor & Active Buffer",
      "confidence": 0.96,
      "bbox": [0.08, 0.05, 0.72, 0.58],
      "description": "Active IDE window containing TypeScript / Next.js implementation"
    }
  ],
  "crops": [
    {
      "box_id": "box-seg-001",
      "label": "Code Editor",
      "crop_base64": "..."
    }
  ],
  "processing_time_ms": 112.5,
  "total_segments": 1
}
```

### 2. Multimodal Reasoning (`POST /api/v1/reason`)
Pipelines visual segments into `muse-spark-1.3` for in-depth reasoning with structured Pydantic schema validation:
```json
{
  "prompt": "Analyze visual segments and formulate refactoring strategy",
  "segments": [...],
  "model": "muse-spark-1.3",
  "structured_format": true
}
```
**Response:**
```json
{
  "success": true,
  "model_used": "muse-spark-1.3",
  "structured_output": {
    "summary": "Executive analysis of the target visual scene",
    "entities_detected": [
      {
        "entity": "Codebase Work Area",
        "box_id": "box-seg-001",
        "properties": { "framework": "Next.js + FastAPI" },
        "relevance": "critical"
      }
    ],
    "detailed_analysis": "Muse Spark 1.3 step-by-step breakdown...",
    "recommended_actions": [
      "Confirm SAM 3.1 bounding box overlays render with accurate canvas coordinates.",
      "Stream Muse Spark agent reasoning tokens directly to the client chat UI."
    ],
    "confidence_score": 0.98,
    "safety_assessment": "safe"
  },
  "processing_time_ms": 154.2
}
```

### 3. Real-Time Streaming Agent Chat (`POST /api/v1/agent/chat`)
Streams token-by-token output via `StreamingResponse` using Server-Sent Events (`text/event-stream`), compatible with the browser's native Web Streams API:
```json
{
  "messages": [
    { "role": "user", "content": "Outline the execution plan for the squad" }
  ],
  "agent_role": "planner",
  "stream": true,
  "temperature": 0.7
}
```

### 4. Background Jobs & Webhooks (`POST /api/v1/jobs`)
Enqueues long-running multimodal inference pipelines with optional webhook callbacks:
```json
{
  "job_type": "full_pipeline",
  "payload": {
    "image_base64": "...",
    "prompt": "Segment frame and run multimodal audit"
  },
  "webhook_url": "https://api.example.com/webhooks/jenna"
}
```

### 5. Cross-Agent Memory (`POST /api/v1/memory/search`)
Queries conversation history from the SQLite + FTS5 store across multiple agent harnesses.

---

## Local Setup & Quick Start

### Option 1: Docker Compose (Recommended)

Orchestrate both the FastAPI backend and Next.js frontend with a single command:
```bash
# 1. Clone repository
git clone https://github.com/Josephjbassey/jenna-hackathon.git
cd jenna-hackathon

# 2. Configure environment
cp .env.example .env

# 3. Launch via Docker Compose
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

---

### Option 2: Local Development

#### 1. Backend Setup
```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

#### 3. Run Backend Test Suite
Verify that all routes and integrations pass with zero syntax or import errors:
```bash
python3 backend/tests/test_api.py
```

---

## Environment Variables Reference

| Variable | Description | Default / Example |
|----------|-------------|-------------------|
| `META_MODEL_API_KEY` | Meta Model API Bearer token | `sk-meta-...` (Optional; fallback simulation enabled) |
| `META_MODEL_API_BASE` | Base URL for Meta Model API | `https://api.meta.ai/v1` |
| `HOST` | Backend host address | `0.0.0.0` |
| `PORT` | Backend port | `8000` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `DATABASE_URL` | Cross-agent memory SQLite path | `sqlite:///./memory/cross_agent.db` |
| `NEXT_PUBLIC_API_URL` | Frontend endpoint to FastAPI API | `http://localhost:8000/api/v1` |

---

## License

MIT © Joseph John Bassey & Jenna AI Team. Built for the Meta Global AI Developer Hackathon 2026.
