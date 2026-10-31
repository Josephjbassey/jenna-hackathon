"""Hermes-Style Terminal User Interface (TUI) for Jenna-Unified.

Inspired by NousResearch Hermes & terminal agent workflows:
- Live multi-agent squad roster with real-time status badges
- Rich interactive conversation stream with Markdown & syntax rendering
- Instant dynamic model selector (/model) across Ollama, LM Studio, and Cloud
- Instant Deepgram voice changer (/voice) across Aura voices & local neural models
- Privacy-gated vision control (/screen, /cam) with explicit user consent toggles
- Obsidian vault memory feed (/obsidian) & Hermes self-evolution log (/learn)
"""
import asyncio
import os
import sys
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.markdown import Markdown
from rich.text import Text
from rich.prompt import Prompt

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (
    ASSISTANT_NAME, USER_NAME, MODELS, SQUAD_ROLES,
    discover_all_models, get_vision_permissions, set_vision_permission,
    DEEPGRAM_VOICES, OBSIDIAN_VAULT_PATH, LEARNINGS_FILE,
)
from voice.voice_io import get_available_voices, get_current_voice, set_voice, speak

console = Console()


def _get_telemetry_snippet() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        return f"CPU: {cpu}% | RAM: {round(vm.percent)}% ({round((vm.total - vm.available)/1024**3, 1)}/{round(vm.total/1024**3, 1)} GB)"
    except Exception:
        return "Telemetry: Active"


def render_header(active_model: str, active_voice: str) -> Panel:
    perms = get_vision_permissions()
    screen_badge = "[bold green]GRANTED[/bold green]" if perms.get("screen") else "[dim red]BLOCKED[/dim red]"
    cam_badge = "[bold green]GRANTED[/bold green]" if perms.get("camera") else "[dim red]BLOCKED[/dim red]"
    telem = _get_telemetry_snippet()

    header_text = (
        f"[bold cyan]⚡ {ASSISTANT_NAME.upper()} AI OS[/bold cyan] · [bold magenta]HERMES TUI[/bold magenta]  |  "
        f"Brain: [bold green]{active_model}[/bold green]  |  "
        f"Voice: [bold yellow]{active_voice}[/bold yellow]  |  "
        f"Screen: {screen_badge}  |  "
        f"Cam: {cam_badge}  |  "
        f"[dim]{telem}[/dim]"
    )
    return Panel(header_text, style="cyan", border_style="bright_blue")


def render_squad_table() -> Table:
    table = Table(title="Multi-Agent Squad Roster", border_style="dim", header_style="bold magenta", expand=True)
    table.add_column("Role", style="bold cyan", width=14)
    table.add_column("Specialist", style="white", width=18)
    table.add_column("Model / Engine", style="yellow")
    table.add_column("Status", style="green", width=10)

    for key, meta in SQUAD_ROLES.items():
        m_key = meta.get("model_key", "fast")
        model_name = MODELS.get(m_key, "default")
        status = "● ONLINE" if key == "commander" else "○ READY"
        table.add_row(key.capitalize(), meta.get("name", key), model_name, status)
    return table


def run_model_picker(agent) -> str:
    console.print("\n[bold cyan]── Discovering All Available AI Models ──[/bold cyan]")
    discovered = discover_all_models()
    table = Table(title="Installed & Available AI Models", border_style="cyan", header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model Name", style="bold white")
    table.add_column("Provider", style="magenta")
    table.add_column("Specs / Details", style="dim")

    all_options = []
    idx = 1
    # Ollama
    for m in discovered.get("ollama", []):
        name = m.get("name")
        all_options.append((name, "ollama"))
        table.add_row(str(idx), name, "Ollama (Local)", f"{m.get('size_gb')} GB")
        idx += 1
    # LM Studio
    for m in discovered.get("lmstudio", []):
        name = m.get("name")
        all_options.append((name, "lmstudio"))
        table.add_row(str(idx), name, "LM Studio (:1234)", m.get("role_hint", "Local GGUF"))
        idx += 1
    # Cloud
    for m in discovered.get("cloud", []):
        name = m.get("name")
        all_options.append((name, m.get("provider", "cloud")))
        table.add_row(str(idx), name, m.get("provider", "Cloud").upper(), "API Cloud")
        idx += 1

    console.print(table)
    choice = Prompt.ask("Select model number to activate (or press Enter to cancel)", default="")
    if choice.isdigit() and 1 <= int(choice) <= len(all_options):
        selected_name, selected_prov = all_options[int(choice) - 1]
        console.print(f"[bold green]✓ Switched active brain to {selected_name} ({selected_prov})[/bold green]")
        return selected_name
    return ""


def run_voice_picker() -> str:
    console.print("\n[bold yellow]── Available TTS Voices (Deepgram Aura & Local) ──[/bold yellow]")
    voices = get_available_voices()
    table = Table(title="Select Spoken Voice", border_style="yellow", header_style="bold yellow")
    table.add_column("#", style="dim", width=4)
    table.add_column("Voice Name", style="bold white")
    table.add_column("Engine", style="magenta")
    table.add_column("Style & Accent", style="dim")

    for i, v in enumerate(voices, 1):
        engine_label = "Deepgram Aura (Cloud)" if v.get("engine") == "deepgram" else f"Local ({v.get('engine')})"
        table.add_row(str(i), v.get("name"), engine_label, f"{v.get('accent')} · {v.get('style')}")

    console.print(table)
    choice = Prompt.ask("Select voice number to activate (or press Enter to cancel)", default="")
    if choice.isdigit() and 1 <= int(choice) <= len(voices):
        sel = voices[int(choice) - 1]
        set_voice(sel["id"], sel.get("engine"))
        console.print(f"[bold green]✓ Active voice updated to: {sel['name']} ({sel['id']})[/bold green]")
        return sel["name"]
    return ""


def start_hermes_tui(voice_playback: bool = True):
    """Launch the full Hermes TUI."""
    from main import build_agent, _run_coro
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory

    agent = build_agent()
    active_model = MODELS.get("fast", "qwen3.5:0.8b")
    cur_voice = get_current_voice().get("voice", "aura-asteria-en")

    console.clear()
    console.print(render_header(active_model, cur_voice))
    console.print(render_squad_table())
    console.print(
        Panel(
            "[bold white]Welcome to Jenna Hermes TUI.[/bold white]\n"
            "Commands: [cyan]/model[/cyan] (switch brain) | [yellow]/voice[/yellow] (change voice) | "
            "[magenta]/screen[/magenta] (toggle screen sight) | [magenta]/cam[/magenta] (toggle webcam sight) | "
            "[green]/obsidian[/green] (vault notes) | [blue]/learn[/blue] (self-evolution log) | "
            "[dim]/quit[/dim] (exit)",
            border_style="magenta",
            title="Hermes Command Center"
        )
    )

    history = InMemoryHistory()

    while True:
        try:
            user_input = prompt(f"\n{USER_NAME}> ", history=history).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Hermes session closed.[/dim]")
            break

        if not user_input:
            continue

        # Slash Commands
        if user_input.lower() in ("/quit", "/exit", ":q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        elif user_input.lower() == "/model":
            new_model = run_model_picker(agent)
            if new_model:
                active_model = new_model
            continue

        elif user_input.lower() == "/voice":
            new_voice = run_voice_picker()
            if new_voice:
                cur_voice = new_voice
            continue

        elif user_input.lower() == "/screen":
            perms = get_vision_permissions()
            new_val = not perms.get("screen", False)
            set_vision_permission("screen", new_val)
            state_str = "[bold green]GRANTED[/bold green]" if new_val else "[bold red]BLOCKED[/bold red]"
            console.print(f"Screen vision permission is now: {state_str}")
            continue

        elif user_input.lower() == "/cam":
            perms = get_vision_permissions()
            new_val = not perms.get("camera", False)
            set_vision_permission("camera", new_val)
            state_str = "[bold green]GRANTED[/bold green]" if new_val else "[bold red]BLOCKED[/bold red]"
            console.print(f"Webcam vision permission is now: {state_str}")
            continue

        elif user_input.lower() == "/obsidian":
            from skills.obsidian_tools import search_obsidian
            res = search_obsidian.invoke({"query": "wiki"})
            console.print(Panel(res, title="Obsidian ~/wiki Vault Snapshot", border_style="magenta"))
            continue

        elif user_input.lower() == "/learn":
            from skills.self_improvement import review_recent_learnings
            res = review_recent_learnings.invoke({"limit": 8})
            console.print(Panel(res, title="Hermes Continuous Self-Improvement Log", border_style="green"))
            continue

        elif user_input.lower() == "/tools":
            from core.agent_core import load_skills
            skills = load_skills()
            tool_names = ", ".join(t.name for t in skills)
            console.print(f"[bold cyan]Active Skills ({len(skills)}):[/bold cyan] {tool_names}")
            continue

        elif user_input.lower() == "/clear":
            console.clear()
            console.print(render_header(active_model, cur_voice))
            continue

        elif user_input.lower() == "/help":
            console.print(
                "[bold cyan]Hermes TUI Slash Commands:[/bold cyan]\n"
                "  /model    - Discover & switch between all Ollama, LM Studio, and Cloud models\n"
                "  /voice    - Select Deepgram Aura or local offline TTS voices\n"
                "  /screen   - Toggle desktop screen sight permission\n"
                "  /cam      - Toggle webcam sight permission\n"
                "  /obsidian - View recent notes in ~/wiki\n"
                "  /learn    - View Hermes continuous self-improvement insights\n"
                "  /tools    - List all registered LangGraph skills\n"
                "  /clear    - Redraw screen\n"
                "  /quit     - Exit TUI"
            )
            continue

        # Standard Multi-Agent Conversational Turn
        with console.status(f"[bold cyan]{ASSISTANT_NAME} LangGraph Squad thinking...[/bold cyan]"):
            reply = _run_coro(agent.run_turn(user_input))

        console.print(f"\n[bold magenta]{ASSISTANT_NAME}:[/bold magenta]")
        console.print(Markdown(reply))

        if voice_playback:
            # Speak asynchronously so TUI remains snappy
            import threading
            threading.Thread(target=speak, args=(reply,), daemon=True).start()
