"""Computer Use tools: cross-platform execution, app launching, and system actions.

Supports Linux and Windows transparently with safe defaults.
"""
import os
import subprocess
import platform
import shutil
from pathlib import Path
from langchain_core.tools import tool

_IS_WINDOWS = platform.system().lower() == "windows"
_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_DIR = _ROOT / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


@tool
def run_command_in_sandbox(command: str) -> str:
    """Execute a shell command inside the sandbox directory.
    
    Safe command runner for building projects, running scripts, and testing.
    Usage: run_command_in_sandbox("python -c 'print(1+1)'")
    """
    # Prevent dangerous commands
    banned = ["rm -rf /", "mkfs", ":(){ :|:& };:", "del /f /s /q c:\\", "format c:"]
    for b in banned:
        if b in command.lower():
            return f"Command rejected: dangerous operation detected ('{b}')."

    try:
        res = subprocess.run(
            command,
            shell=True,
            cwd=str(SANDBOX_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        code = res.returncode
        result = []
        if out:
            result.append(f"[stdout]\n{out}")
        if err:
            result.append(f"[stderr]\n{err}")
        if not result:
            result.append(f"(completed with exit code {code})")
        return "\n".join(result)
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Execution error: {e}"


@tool
def open_url_or_file(target: str) -> str:
    """Open a URL in the default web browser or a file in its default system viewer."""
    try:
        import webbrowser
        if target.startswith("http://") or target.startswith("https://"):
            webbrowser.open(target)
            return f"Opened web URL: {target}"

        # Local file
        if _IS_WINDOWS:
            os.startfile(target)
        elif shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("open"):
            subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Opened target: {target}"
    except Exception as e:
        return f"Failed to open '{target}': {e}"
