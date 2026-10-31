"""Sandboxed file tools: read/write/list files inside ./sandbox only."""
from pathlib import Path
from langchain_core.tools import tool

SANDBOX = Path(__file__).resolve().parent.parent / "sandbox"
SANDBOX.mkdir(exist_ok=True)


def _safe_path(path: str) -> Path:
    p = (SANDBOX / path).resolve()
    if SANDBOX.resolve() not in p.parents and p != SANDBOX.resolve():
        raise ValueError("Path escapes sandbox")
    return p


@tool
def list_files(path: str = ".") -> str:
    """List files in the sandbox directory. Usage: list_files("subdir")"""
    p = _safe_path(path)
    if not p.exists():
        return f"Path not found: {path}"
    if p.is_file():
        return f"{path} (file, {p.stat().st_size} bytes)"
    entries = sorted(p.iterdir())
    lines = [f"{e.name}/" if e.is_dir() else f"{e.name} ({e.stat().st_size} bytes)" for e in entries]
    return "\n".join(lines) if lines else "(empty)"


@tool
def read_file(path: str) -> str:
    """Read a text file inside the sandbox. Usage: read_file("notes.txt")"""
    p = _safe_path(path)
    if not p.exists() or not p.is_file():
        return f"File not found: {path}"
    return p.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Write text to a file inside the sandbox. Usage: write_file("notes.txt", "hello")"""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} bytes to {path}"
