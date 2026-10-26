"""
Jenna-Unified — unified local voice AI agent.

Usage:
  python main.py            # desktop orb overlay + push-to-talk (default)
  python main.py --desktop  # same as above
  python main.py --cli      # terminal chat (prompt_toolkit + rich)
  python main.py --api      # FastAPI HTTP API (uvicorn on :8787)
  python main.py --voice    # force voice mode on CLI
"""
import argparse
import asyncio
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from config import ASSISTANT_NAME, USER_NAME, HOTKEY, DASHBOARD_HOST, DASHBOARD_PORT
from core.agent_core import Agent, load_skills, load_mcp_tools

console = Console()

_agent = None
_loop = None


def _ensure_loop():
    global _loop
    if _loop is None:
        _loop = asyncio.new_event_loop()
        t = threading.Thread(target=_loop.run_forever, daemon=True)
        t.start()
    return _loop


def _run_coro(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ensure_loop()).result()


async def _build_agent_async():
    tools = load_skills()
    mcp_tools = await load_mcp_tools()
    all_tools = tools + mcp_tools
    try:
        from core.graph_agent import JennaGraphAgent
        return JennaGraphAgent(all_tools)
    except Exception as e:
        console.print(f"[yellow]Notice: LangGraph init fallback to ReAct Agent ({e})[/yellow]")
        return Agent("fast", all_tools)


def build_agent():
    global _agent
    if _agent is None:
        _agent = _run_coro(_build_agent_async())
    return _agent


# ── Desktop (orb overlay + tray + hotkey) ────────────────────────────────

def start_desktop():
    from voice.voice_io import (
        record_audio, record_until_silence, transcribe, speak,
        play_listen_tone, play_done_tone, build_wake_word_detector,
    )
    import webview
    from pynput import keyboard

    window = None
    agent = build_agent()

    def set_state(state: str):
        nonlocal window
        if window is not None:
            try:
                window.evaluate_js(f"window.setState && window.setState('{state}')")
            except Exception:
                pass

    class Api:
        def hide(self):
            nonlocal window
            if window:
                window.hide()

        def quit(self):
            nonlocal window
            if window:
                window.destroy()

        def get_models(self):
            from config import discover_all_models
            return discover_all_models()

        def switch_model(self, model_name: str, provider: str = "ollama"):
            nonlocal agent
            set_state("loading")
            from config import MODELS
            MODELS["fast"] = model_name
            # Rebuild graph agent or reconfigure
            from core.agent_core import load_skills, load_mcp_tools
            from core.graph_agent import JennaGraphAgent
            tools = load_skills()
            mcp_tools = _run_coro(load_mcp_tools())
            agent = JennaGraphAgent(tools + mcp_tools)
            set_state("idle")
            console.print(f"[agent] switched active model to {model_name} ({provider})")
            return {"status": "ok", "active": model_name, "provider": provider}

        def get_available_voices(self):
            from voice.voice_io import get_available_voices, get_current_voice
            return {
                "voices": get_available_voices(),
                "current": get_current_voice(),
            }

        def set_voice(self, voice_id: str, engine: str = None):
            from voice.voice_io import set_voice
            return set_voice(voice_id, engine)

        def get_vision_permissions(self):
            from config import get_vision_permissions
            return get_vision_permissions()

        def set_vision_permission(self, target: str, allowed: bool):
            from config import set_vision_permission
            return set_vision_permission(target, allowed)

        def get_hermes_learnings(self):
            from skills.self_improvement import review_recent_learnings
            return review_recent_learnings.invoke({"limit": 8})

        def get_telemetry(self):
            import psutil, platform, shutil
            try:
                vm = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=None)
                path = "C:\\" if platform.system().lower() == "windows" else "/"
                total, used, free = shutil.disk_usage(path)
                return {
                    "cpu_percent": cpu,
                    "ram_used_mb": (vm.total - vm.available) // (2**20),
                    "ram_total_mb": vm.total // (2**20),
                    "ram_percent": vm.percent,
                    "disk_free_gb": free // (2**30),
                    "disk_total_gb": total // (2**30),
                    "os": f"{platform.system()} {platform.release()}",
                }
            except Exception as e:
                return {"error": str(e)}

        def get_squad_info(self):
            from config import SQUAD_ROLES, MODELS, MODEL_PROVIDERS, PROVIDER_MODELS, OLLAMA_HOST, LMSTUDIO_HOST
            import urllib.request
            ollama_ok = False
            try:
                urllib.request.urlopen(f"{OLLAMA_HOST.rstrip('/')}/api/tags", timeout=0.6)
                ollama_ok = True
            except Exception:
                pass

            lmstudio_ok = False
            try:
                urllib.request.urlopen(f"{LMSTUDIO_HOST.rstrip('/')}/models", timeout=0.6)
                lmstudio_ok = True
            except Exception:
                pass

            roles = []
            for r_key, meta in SQUAD_ROLES.items():
                prov = MODEL_PROVIDERS.get(r_key, "ollama")
                if prov in ("nvidia", "ultramarine", "lmstudio"):
                    model_tag = PROVIDER_MODELS.get(prov, {}).get(r_key, "default")
                else:
                    model_tag = MODELS.get(r_key, "default")
                roles.append({
                    "key": r_key,
                    "name": meta.get("name"),
                    "description": meta.get("description"),
                    "model": model_tag,
                    "provider": prov,
                })

            return {
                "roles": roles,
                "ollama_online": ollama_ok,
                "lmstudio_online": lmstudio_ok,
            }

        def get_obsidian_data(self):
            from config import OBSIDIAN_VAULT_PATH
            log_file = OBSIDIAN_VAULT_PATH / "log.md"
            logs = []
            if log_file.exists():
                try:
                    content = log_file.read_text(encoding="utf-8")
                    lines = [l.strip() for l in content.splitlines() if l.strip()]
                    logs = lines[-12:]
                except Exception:
                    pass

            notes = []
            try:
                for p in list(OBSIDIAN_VAULT_PATH.rglob("*.md"))[:15]:
                    notes.append(str(p.relative_to(OBSIDIAN_VAULT_PATH)))
            except Exception:
                pass

            return {
                "vault_path": str(OBSIDIAN_VAULT_PATH),
                "recent_logs": logs,
                "recent_notes": notes,
            }

        def save_obsidian_entry(self, text: str):
            from skills.obsidian_tools import log_to_obsidian_journal
            return log_to_obsidian_journal.invoke({"entry": text})

        def run_sandbox_command(self, cmd: str):
            from skills.computer_tools import run_command_in_sandbox
            return run_command_in_sandbox.invoke({"command": cmd})

        def send_chat_turn(self, text: str):
            nonlocal agent, window
            set_state("thinking")
            reply = _run_coro(agent.run_turn(text))
            set_state("idle")
            return {"reply": reply}

        def trigger_voice_record(self):
            threading.Thread(target=handle_voice_turn, daemon=True).start()
            return {"status": "listening"}

    def handle_voice_turn():
        nonlocal window, agent
        if window:
            window.show()
        play_listen_tone()
        set_state("listening")
        audio = record_until_silence()
        set_state("thinking")
        text = transcribe(audio)
        if not text.strip():
            set_state("idle")
            return
        console.print(f"\n[bold white]{USER_NAME}:[/bold white] {text}")
        if window:
            try:
                window.evaluate_js(f"window.appendUserTurn && window.appendUserTurn({json.dumps(text)})")
            except Exception:
                pass
        reply = _run_coro(agent.run_turn(text))
        console.print(f"[bold magenta]{ASSISTANT_NAME}:[/bold magenta] {reply}")
        if window:
            try:
                window.evaluate_js(f"window.appendAssistantTurn && window.appendAssistantTurn({json.dumps(reply)})")
            except Exception:
                pass
        set_state("speaking")
        speak(reply)
        play_done_tone()
        set_state("idle")

    # Robust hotkey: track pressed set
    _pressed = set()

    def on_press_kb(key):
        _pressed.add(key)
        if HOTKEY and HOTKEY.issubset(_pressed):
            threading.Thread(target=handle_voice_turn, daemon=True).start()

    def on_release_kb(key):
        _pressed.discard(key)

    # HTML overlay
    overlay_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay")
    html_path = os.path.join(overlay_dir, "index.html")
    api = Api()
    window = webview.create_window(
        f"{ASSISTANT_NAME} AI OS — Executive Suite",
        html_path,
        js_api=api,
        width=1240,
        height=780,
        min_size=(960, 600),
        resizable=True,
        frameless=False,
        easy_drag=True,
        on_top=False,
    )

    listener = keyboard.Listener(on_press=on_press_kb, on_release=on_release_kb)
    listener.daemon = True
    listener.start()

    console.print(f"[bold cyan]{ASSISTANT_NAME} desktop agent running.[/bold cyan] "
                  f"Push-to-talk: {' + '.join(k.name if hasattr(k,'name') else str(k) for k in HOTKEY)}")
    webview.start(debug=False)
    listener.stop()


# ── CLI (terminal chat) ─────────────────────────────────────────────────

def start_cli(voice: bool = False):
    from voice.voice_io import (
        record_audio, record_until_silence, transcribe, speak,
        play_listen_tone, play_done_tone,
    )
    agent = build_agent()
    console.print(f"[bold cyan]{ASSISTANT_NAME} CLI[/bold cyan] — type your message, or Ctrl+C to exit.\n")
    if voice:
        console.print("[dim]Voice mode: speak when prompted.[/dim]\n")

    while True:
        try:
            if voice:
                play_listen_tone()
                audio = record_until_silence()
                text = transcribe(audio)
                if not text.strip():
                    console.print("[dim](no speech)[/dim]\n")
                    continue
                console.print(f"\n[bold white]{USER_NAME}:[/bold white] {text}")
            else:
                from prompt_toolkit import prompt
                text = prompt(f"{USER_NAME}> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        reply = _run_coro(agent.run_turn(text))
        console.print(f"[bold magenta]{ASSISTANT_NAME}:[/bold magenta] {reply}\n")
        if voice:
            speak(reply)
            play_done_tone()


# ── API (FastAPI) ───────────────────────────────────────────────────────

def start_api():
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    from pathlib import Path

    app = FastAPI(title=f"{ASSISTANT_NAME} API")
    agent = build_agent()

    # Serve overlay static assets (theme switcher CSS/JS)
    static_dir = Path(__file__).parent / "overlay"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    class TurnIn(BaseModel):
        text: str
        model: str = "fast"

    @app.post("/turn")
    async def turn(payload: TurnIn):
        nonlocal_agent = Agent(payload.model, load_skills())
        reply = await nonlocal_agent.run_turn(payload.text)
        return {"reply": reply}

    @app.get("/health")
    async def health():
        return {"status": "ok", "agent": ASSISTANT_NAME}

    # Theme API endpoints
    from jenna.themes import REGISTRY

    @app.get("/api/themes")
    async def list_themes():
        return REGISTRY.list_themes()

    @app.get("/api/themes/{theme_name}/css")
    async def get_theme_css(theme_name: str):
        css = REGISTRY.css_variables(theme_name, prefix="jenna")
        from fastapi.responses import Response
        return Response(content=css, media_type="text/css")

    @app.get("/api/themes/current")
    async def get_current_theme():
        # Detect current Omarchy theme
        current = REGISTRY.current_omarchy_theme()
        return {"theme": current or "catppuccin"}

    # Cross-Agent Memory API endpoints
    from jenna.memory.cross_agent import get_cross_agent_memory
    from pydantic import BaseModel
    from typing import Optional

    class MemorySearchIn(BaseModel):
        query: str
        agent: Optional[str] = None
        days: int = 30
        limit: int = 50

    class MemoryDigestIn(BaseModel):
        days: int = 1
        vault_path: Optional[str] = None

    @app.get("/api/memory/stats")
    async def memory_stats():
        mem = get_cross_agent_memory()
        return mem.stats()

    @app.post("/api/memory/ingest")
    async def memory_ingest():
        mem = get_cross_agent_memory()
        return mem.ingest_all()

    @app.post("/api/memory/search")
    async def memory_search(payload: MemorySearchIn):
        mem = get_cross_agent_memory()
        return mem.search(payload.query, payload.agent, payload.days, payload.limit)

    @app.get("/api/memory/recent")
    async def memory_recent(agent: Optional[str] = None, days: int = 7, limit: int = 100):
        mem = get_cross_agent_memory()
        return mem.recent(agent, days, limit)

    @app.post("/api/memory/digest")
    async def memory_digest(payload: MemoryDigestIn):
        mem = get_cross_agent_memory()
        vault = Path(payload.vault_path) if payload.vault_path else Path.home() / "wiki"
        digest_file = mem.write_daily_digest(vault, payload.days)
        return {"digest_file": str(digest_file)}

    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)


def main():
    parser = argparse.ArgumentParser(description=f"{ASSISTANT_NAME} — local voice AI agent")
    parser.add_argument("--desktop", action="store_true", help="Desktop orb overlay + push-to-talk")
    parser.add_argument("--cli", action="store_true", help="Terminal chat")
    parser.add_argument("--tui", action="store_true", help="Hermes-style interactive Terminal User Interface")
    parser.add_argument("--api", action="store_true", help="FastAPI HTTP API")
    parser.add_argument("--voice", action="store_true", help="Force voice mode on CLI")
    args = parser.parse_args()

    if args.tui:
        from tui.hermes_tui import start_hermes_tui
        start_hermes_tui(voice_playback=args.voice)
    elif args.api:
        start_api()
    elif args.cli:
        start_cli(voice=args.voice)
    else:
        start_desktop()


if __name__ == "__main__":
    main()
