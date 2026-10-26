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
            from config import MODELS
            return MODELS

        def switch_model(self, model_key: str):
            nonlocal agent
            set_state("loading")
            agent = Agent(model_key, load_skills())
            set_state("idle")
            console.print(f"[agent] switched to {model_key}")

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
        reply = _run_coro(agent.run_turn(text))
        console.print(f"[bold magenta]{ASSISTANT_NAME}:[/bold magenta] {reply}")
        set_state("speaking")
        speak(reply)
        play_done_tone()
        set_state("idle")

    def on_press(key):
        try:
            current = set()
            # track modifiers simply
            current.add(key)
            if HOTKEY and key in HOTKEY:
                # require full combo via check in listener state below
                pass
        except Exception:
            pass

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
        f"{ASSISTANT_NAME} — {USER_NAME}'s Agent",
        html_path,
        js_api=api,
        width=420,
        height=560,
        resizable=False,
        frameless=True,
        easy_drag=True,
        on_top=True,
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
    from pydantic import BaseModel

    app = FastAPI(title=f"{ASSISTANT_NAME} API")
    agent = build_agent()

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

    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)


def main():
    parser = argparse.ArgumentParser(description=f"{ASSISTANT_NAME} — local voice AI agent")
    parser.add_argument("--desktop", action="store_true", help="Desktop orb overlay + push-to-talk")
    parser.add_argument("--cli", action="store_true", help="Terminal chat")
    parser.add_argument("--api", action="store_true", help="FastAPI HTTP API")
    parser.add_argument("--voice", action="store_true", help="Force voice mode on CLI")
    args = parser.parse_args()

    if args.api:
        start_api()
    elif args.cli:
        start_cli(voice=args.voice)
    else:
        start_desktop()


if __name__ == "__main__":
    main()
