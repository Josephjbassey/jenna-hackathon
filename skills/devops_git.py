"""Git & DevOps Automation Skill for Jenna-Unified.

Enables Jenna to:
- Check git repository status, diffs, and unstaged changes
- Inspect commit history and active branches
- Generate structured semantic git commit messages
"""
import subprocess
from pathlib import Path
from langchain_core.tools import tool

_ROOT = Path(__file__).resolve().parent.parent


def _run_git_cmd(args: list) -> str:
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8,
        )
        if res.returncode != 0:
            return f"Git Error (code {res.returncode}): {res.stderr.strip()}"
        return res.stdout.strip()
    except Exception as e:
        return f"Git execution error: {e}"


@tool
def git_status() -> str:
    """Get the current working directory git status, showing modified, untracked, and staged files."""
    out = _run_git_cmd(["status", "--short", "--branch"])
    if not out:
        return "Git repository is clean. No unstaged or untracked changes."
    return f"### Git Status:\n```\n{out}\n```"


@tool
def git_diff(staged: bool = False, max_lines: int = 60) -> str:
    """Show the git diff of modified files.
    
    Args:
        staged: If True, inspect only staged changes (--cached). Defaults to False (working tree diff).
        max_lines: Maximum lines of diff output to return.
    """
    cmd = ["diff"]
    if staged:
        cmd.append("--cached")
    diff_out = _run_git_cmd(cmd)
    if not diff_out:
        return "No changes in diff."

    lines = diff_out.splitlines()
    if len(lines) > max_lines:
        truncated = "\n".join(lines[:max_lines]) + f"\n\n... [{len(lines) - max_lines} more lines truncated]"
        return f"```diff\n{truncated}\n```"
    return f"```diff\n{diff_out}\n```"


@tool
def git_recent_commits(count: int = 5) -> str:
    """Show recent git commit history with short hashes, dates, and authors."""
    log_format = "%h - %an, %ar : %s"
    out = _run_git_cmd(["log", f"-n{count}", f"--pretty=format:{log_format}"])
    return f"### Recent Commits:\n{out}"
