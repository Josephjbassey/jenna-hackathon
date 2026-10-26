# Jenna AI OS — Suite Dashboard Concept Preview

Here is the concept design for the complete **Jenna AI OS Suite Dashboard**:

![Jenna AI OS Suite Dashboard Mockup](/home/jabs/.gemini/antigravity-ide/brain/053b94e3-6f53-4dc2-81cb-25e55caf7b75/jenna_suite_dashboard_1793024940582.jpg)

---

## Architecture & Layout Breakdown

### 1. Central Core — Interactive 3D Audio-Reactive Sphere
* **Engine**: Procedural WebGL / Three.js particle sphere with perlin-noise displacement.
* **Audio Reactivity**: Binds to mic input and TTS output via Web Audio API `AnalyserNode`.
* **State Colors**:
  * **Cyan / Azure**: Idle & active listening.
  * **Electric Amber**: Synaptic thinking & LangGraph squad planning.
  * **Neon Violet / Emerald**: Neural voice playback (Kokoro ONNX / Piper).

### 2. Left Panel — Multi-Agent Squad Roster
* Real-time status cards for each agent in the squad:
  * **Commander**: `Qwen 3.5 (0.8B)` — Fast voice conversation & intent triage.
  * **Engineer**: `Qwen 2.5 Coder (3B)` / `Qwen3 (4B)` — Code generation & sandbox execution.
  * **Planner**: `NVIDIA Nemotron 30B MoE` / `Phi-4 Mini` — Strategic decomposition & logic.
  * **Scholar**: `Ministral 3B` / `Qwen 3.5 (2B)` — Research & information extraction.
  * **Communicator**: `AgentPhone` & `AgentMail` — Twilio & email integration.
* Click any agent to inspect its active context, prompt history, or force delegation.

### 3. Top Bar — Hardware Telemetry & Dual-Engine Status
* **Hardware Gauges**: Live CPU % and RAM usage using `psutil`.
* **Dual Engine Status**:
  * **Ollama** (`:11434`): Live status badge & model count.
  * **LM Studio** (`:1234`): Live status badge & active server indicator.
* **OS Environment Badge**: Detects current running environment (`Linux / Parrot`, `Omarchy`, or `Windows`).

### 4. Right Panel — Obsidian Wiki & Memory Stream (`~/wiki`)
* **Live Markdown View**: Real-time reader and editor for notes in `/home/jabs/wiki`.
* **Recent Daily Log Feed**: Directly reflects `~/wiki/log.md`.
* **Knowledge Graph Visualizer**: Interactive canvas showing connected notes, entities, and concepts.
* **Quick-Add Button**: One-click voice/text entry to log thoughts directly to Obsidian.

### 5. Bottom Action Dock — Communications & Control
* **Push-to-Talk Orb Trigger**: Hold to speak, release to send (or `Ctrl+Alt+Space` hotkey).
* **Live Spectrum Visualizer**: Dynamic frequency bars matching human vocal range.
* **Quick Tools**:
  * 📞 **AgentPhone**: Initiate SMS or voice calls.
  * ✉️ **AgentMail**: Review outbox and draft messages.
  * 💻 **Sandboxed Terminal**: Quick shell command runner inside `./sandbox`.

---

## Technical Implementation Plan

1. **Frontend**:
   * Single-page rich application in [overlay/index.html](file:///media/jabs/Development1/Linux/python/Jenna-Unified/overlay/index.html) with CSS glassmorphism, Three.js 3D WebGL particle sphere, and SVG graph visualizer.
2. **Backend Bridge in [main.py](file:///media/jabs/Development1/Linux/python/Jenna-Unified/main.py)**:
   * Expose pywebview / FastAPI JavaScript API for:
     * Squad status & model switching.
     * Real-time system telemetry polling (`system_info`).
     * Obsidian vault reading, writing, and search (`obsidian_tools`).
     * Live voice turn dispatch through `JennaGraphAgent`.
