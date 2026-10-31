"""Obsidian Vault integration tools for Jenna-Unified.

Allows Jenna to search, read, write, and log daily entries directly into
the user's Obsidian knowledge vault (~/wiki or configured OBSIDIAN_VAULT_PATH).
"""
import os
import sys
import time
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import OBSIDIAN_VAULT_PATH


def _resolve_vault_path(relative_path: str) -> Path:
    """Safely resolve a path inside the Obsidian vault."""
    clean = relative_path.strip().lstrip("/\\")
    if not clean.endswith(".md"):
        clean += ".md"
    p = (OBSIDIAN_VAULT_PATH / clean).resolve()
    # Ensure it doesn't escape the vault
    if OBSIDIAN_VAULT_PATH.resolve() not in p.parents and p != OBSIDIAN_VAULT_PATH.resolve():
        raise ValueError("Target path escapes the Obsidian vault.")
    return p


@tool
def search_obsidian(query: str) -> str:
    """Search for notes, concepts, or logs in the user's Obsidian vault.
    
    Usage: search_obsidian("neural networks")
    """
    if not OBSIDIAN_VAULT_PATH.exists():
        return f"Obsidian vault path '{OBSIDIAN_VAULT_PATH}' does not exist."

    query_lower = query.lower()
    matches = []

    for md_file in OBSIDIAN_VAULT_PATH.rglob("*.md"):
        rel = md_file.relative_to(OBSIDIAN_VAULT_PATH)
        # Match filename
        if query_lower in md_file.name.lower():
            matches.append(f"• [[{rel}]] (title match)")
            continue
        # Match content
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            if query_lower in content.lower():
                # Extract first snippet
                idx = content.lower().find(query_lower)
                start = max(0, idx - 40)
                end = min(len(content), idx + 80)
                snippet = content[start:end].replace("\n", " ").strip()
                matches.append(f"• [[{rel}]]: ...{snippet}...")
        except Exception:
            pass

        if len(matches) >= 10:
            break

    if not matches:
        return f"No Obsidian notes found matching query: '{query}'."
    return "Obsidian Search Results:\n" + "\n".join(matches)


@tool
def read_obsidian_note(note_name: str) -> str:
    """Read the full markdown content of a note from the Obsidian vault.
    
    Usage: read_obsidian_note("concepts/voice_agents.md") or read_obsidian_note("log")
    """
    try:
        path = _resolve_vault_path(note_name)
        if not path.exists():
            # Try searching for matching filename
            for cand in OBSIDIAN_VAULT_PATH.rglob("*.md"):
                if cand.stem.lower() == note_name.lower().replace(".md", ""):
                    path = cand
                    break
            else:
                return f"Obsidian note '{note_name}' not found in {OBSIDIAN_VAULT_PATH}."

        content = path.read_text(encoding="utf-8")
        rel = path.relative_to(OBSIDIAN_VAULT_PATH)
        return f"[Obsidian Note: {rel}]\n{content}"
    except Exception as e:
        return f"Failed to read Obsidian note: {e}"


@tool
def write_obsidian_note(note_name: str, content: str, append: bool = False) -> str:
    """Create or append content to an Obsidian note in the vault.
    
    Usage: write_obsidian_note("concepts/voice_architecture", "# Architecture Notes\n...", append=False)
    """
    try:
        path = _resolve_vault_path(note_name)
        path.parent.mkdir(parents=True, exist_ok=True)

        if append and path.exists():
            existing = path.read_text(encoding="utf-8")
            path.write_text(f"{existing.rstrip()}\n\n{content}\n", encoding="utf-8")
            action = "Appended to"
        else:
            path.write_text(content.strip() + "\n", encoding="utf-8")
            action = "Created"

        rel = path.relative_to(OBSIDIAN_VAULT_PATH)
        return f"Successfully {action.lower()} Obsidian note: [[{rel}]]."
    except Exception as e:
        return f"Failed to write to Obsidian note: {e}"


@tool
def log_to_obsidian_journal(entry: str) -> str:
    """Append a timestamped log entry or memory directly into the Obsidian log.md journal.
    
    Usage: log_to_obsidian_journal("Discussed LangGraph multi-agent architecture and mapped local models.")
    """
    log_path = OBSIDIAN_VAULT_PATH / "log.md"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_entry = f"\n### {timestamp}\n{entry.strip()}\n"

    try:
        if log_path.exists():
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(formatted_entry)
        else:
            log_path.write_text(f"# Obsidian Daily Activity Log\n{formatted_entry}", encoding="utf-8")
        return f"Logged entry to Obsidian log.md at {timestamp}."
    except Exception as e:
        return f"Failed to log to Obsidian: {e}"
