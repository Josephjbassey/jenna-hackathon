# Jenna AI OS — Meta AI Developer Hackathon Entry

**Track:** Indie Developer | **Team:** Joseph John  
**Hackathon:** Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026)  
**Problem Statement:** Build for Your World

---

## What is Jenna?

Jenna is a **local-first AI OS** with a 5-agent squad running on 8GB RAM via LangGraph, voice I/O, and vision. Built for a Nigerian student developer (FUTA CSC/25/2960) who needs powerful AI that works offline on modest hardware.

### The 5-Agent Squad
| Role | Model | Function |
|------|-------|----------|
| **Commander** | Muse Spark 1.3 | Executive coordination, voice conversationalist, task decomposition |
| **Planner** | Muse Spark 1.3 | Multi-step reasoning, structured task planning |
| **Engineer** | Muse Code | Code generation, debugging, refactoring, terminal tasks |
| **Scholar** | Muse Wonder 1.0 | Web research, factual aggregation, documentation |
| **Communicator** | Muse Spark 1.3 | SMS/calls (Twilio), email, inter-agent messaging |

---

## Built During Hackathon (Oct 27 – Nov 4)

### Meta Model API Integration
- ✅ **Muse Spark 1.3** — Planner and Commander agents (reasoning/coordination)
- ✅ **Muse Voice Transcribe 1.0** — Speech-to-text pipeline (replaces Whisper)
- ✅ **Muse Image 1.0** — Image generation/understanding (Scholar agent)
- ✅ **SAM 3.1** — Segmentation anything (vision pipeline)
- ✅ **Muse Code** — Code generation (Engineer agent)
- ✅ **Muse Wonder 1.0** — Advanced research (Scholar agent)

### Other Hackathon Features
- Cross-agent memory with FTS5 search (Hermes, Claude, Antigravity ingestion)
- Real-time telemetry dashboard
- Multi-theme UI (19 Omarchy themes, warm minimalist design)
- Desktop orb overlay + push-to-talk voice interface
- Terminal chat and FastAPI HTTP API

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Core** | Python 3.12, LangGraph, FastAPI |
| **Meta Models** | Muse Spark 1.3, Muse Voice Transcribe 1.0, Muse Image 1.0, SAM 3.1 |
| **Local Models** | Ollama (Qwen 3.5 0.8B, Gemma 2 2B), LM Studio |
| **Voice** | Muse Voice Transcribe (STT), Deepgram/Piper/Kokoro (TTS) |
| **Vision** | Muse Image + SAM 3.1 (Meta), local webcam/screen capture |
| **Memory** | SQLite + FTS5, cross-agent aggregation (Hermes, Claude, Antigravity) |
| **UI** | Webview overlay, warm minimalist design, 19 Omarchy themes |
| **Sandbox** | Isolated command execution with safety filters |
| **Observability** | LangSmith tracing, psutil telemetry |
| **Infrastructure** | Modal (GPU inference), Fireworks (serverless), Baseten (TPM) |

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/josephjbassey/jenna-hackathon
cd jenna-hackathon

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure Meta Model API (hackathon credits)
export META_MODEL_API_KEY="your-key-here"
cp .env.example .env

# 4. Run (desktop, CLI, or API)
python main.py --desktop   # Desktop overlay + push-to-talk
python main.py --cli       # Terminal chat
python main.py --api       # FastAPI HTTP API (localhost:8787)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Jenna AI OS — 5-Agent Squad (LangGraph)                    │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Commander   │   │ Planner     │   │ Engineer    │       │
│  │ (Muse Spark)│◄─►│ (Muse Spark)│◄─►│ (Muse Code) │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│  ┌─────────────┐   ┌─────┴────────┐                        │
│  │ Scholar     │   │ Communicator │                        │
│  │ (Muse Wonder)│   │ (Muse Spark) │                        │
│  └─────────────┘   └──────────────┘                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Cross-Agent Memory (SQLite + FTS5)                  │    │
│  │ Hermes | Claude | Antigravity | Obsidian            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
        │                         │
        ▼                         ▼
┌───────────────┐        ┌──────────────────┐
│ Muse Voice    │        │ Muse Image +     │
│ Transcribe    │        │ SAM 3.1          │
└───────────────┘        └──────────────────┘
```

---

## Demo Video

A 3-minute demo video is available at: [TODO: Add YouTube/Drive link]

---

## Credits & Partners

This project uses credits and infrastructure from:
- **Meta Model API** — Muse Spark, Muse Voice Transcribe, Muse Image, SAM 3.1
- **Modal** — GPU inference for heavy models
- **Fireworks** — Serverless inference on open-weight models
- **Baseten** — 2M TPM rate limit for multi-agent parallel calls
- **LangSmith** — LangGraph squad tracing and debugging
- **Tavily** — Scholar agent live web search
- **Zoho Catalyst** — Serverless backend, auth, DB, cron, ML services

---

## License

MIT — See LICENSE file
