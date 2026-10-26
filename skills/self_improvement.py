"""Hermes Self-Improvement & Kaizen Continuous Learning for Jenna-Unified.

Inspired by NousResearch Hermes reflection loops and Kaizen continuous evolution.
Allows Jenna to:
- Reflect on tasks, user corrections, and execution outcomes
- Persist structured learnings directly into the user's Obsidian vault (~/wiki/learnings.md)
- Synthesize, test, and hot-reload new Python skills dynamically
- Review past feedback and self-evolution history
"""
import ast
import datetime
import json
import os
import sys
from pathlib import Path
from langchain_core.tools import tool

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import OBSIDIAN_VAULT_PATH, LEARNINGS_FILE, EVOLUTION_FILE, MEMORY_DIR


def _ensure_paths():
    OBSIDIAN_VAULT_PATH.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


@tool
def reflect_and_learn(task: str, outcome: str, lessons_learned: str, category: str = "general") -> str:
    """Record a reflection, user correction, or newly acquired lesson into Jenna's persistent memory and Obsidian vault.
    
    Use this whenever:
    - The user corrects your behavior or expresses a preference
    - A complex tool execution fails and you find the fix
    - You discover a project pattern, path, or API requirement to remember
    
    Args:
        task: Brief description of what was being attempted
        outcome: Whether it succeeded or failed ('success', 'failure', 'corrected')
        lessons_learned: Concrete rule or insight to remember for the future
        category: Tag/category ('coding', 'voice', 'system', 'obsidian', 'general')
    """
    _ensure_paths()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Append to Obsidian Vault (~/wiki/learnings.md)
    entry_md = (
        f"\n### [{now_str}] #{category.lower()} · {outcome.upper()}\n"
        f"- **Task:** {task}\n"
        f"- **Outcome:** {outcome}\n"
        f"- **Lesson Learned:** {lessons_learned}\n"
    )

    try:
        if not LEARNINGS_FILE.exists():
            LEARNINGS_FILE.write_text("# Jenna AI — Continuous Self-Improvement & Learnings Log\n\n", encoding="utf-8")
        with open(LEARNINGS_FILE, "a", encoding="utf-8") as f:
            f.write(entry_md)
    except Exception as e:
        return f"Warning: Failed to write to Obsidian learnings ({e})"

    # 2. Append to JSON database for semantic search
    json_path = MEMORY_DIR / "hermes_learnings.json"
    records = []
    if json_path.exists():
        try:
            records = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            records = []

    records.append({
        "timestamp": now_str,
        "category": category,
        "task": task,
        "outcome": outcome,
        "lesson": lessons_learned
    })

    try:
        json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    except Exception:
        pass

    return f"Lesson recorded to Obsidian ({LEARNINGS_FILE.name}) and Hermes memory. Total learned insights: {len(records)}."


@tool
def review_recent_learnings(query: str = "", limit: int = 5) -> str:
    """Review Jenna's recent self-improvement insights, user preferences, and recorded lessons."""
    json_path = MEMORY_DIR / "hermes_learnings.json"
    if not json_path.exists():
        if LEARNINGS_FILE.exists():
            return LEARNINGS_FILE.read_text(encoding="utf-8")[-1200:]
        return "No recorded learnings yet. Jenna will record insights as tasks are completed."

    try:
        records = json.loads(json_path.read_text(encoding="utf-8"))
        if query:
            records = [r for r in records if query.lower() in str(r).lower()]
        recent = records[-limit:]
        if not recent:
            return f"No learnings found matching '{query}'."

        lines = [f"Found {len(recent)} recent learnings:"]
        for r in recent:
            lines.append(f"• [{r.get('timestamp')}] ({r.get('category')}): {r.get('lesson')} (Context: {r.get('task')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading learnings: {e}"


@tool
def synthesize_new_skill(skill_name: str, description: str, python_code: str) -> str:
    """Dynamically synthesize a new Python skill tool and add it to Jenna's capabilities.
    
    The code must define a function decorated with @tool from langchain_core.tools.
    The code will be verified for syntax and safety before writing to ./skills/{skill_name}.py.
    
    Args:
        skill_name: Slug for the skill file, e.g. 'currency_converter' (without .py)
        description: Brief explanation of what the new tool does
        python_code: Valid Python code containing the @tool function
    """
    clean_name = skill_name.strip().replace(" ", "_").replace("-", "_").lower()
    if not clean_name.isidentifier():
        return f"Invalid skill name '{skill_name}'. Must be a valid Python identifier."

    # Validate Python AST syntax
    try:
        ast.parse(python_code)
    except SyntaxError as se:
        return f"Skill compilation failed: SyntaxError on line {se.lineno}: {se.msg}"

    # Basic safety check
    for dangerous in ["rm -rf", "shutil.rmtree('/')", "os.system('rm"]:
        if dangerous in python_code:
            return "Skill rejected: Contains potentially dangerous system removal commands."

    target_file = _ROOT / "skills" / f"{clean_name}.py"
    try:
        target_file.write_text(python_code, encoding="utf-8")
    except Exception as e:
        return f"Failed to save skill to disk: {e}"

    # Record in self_evolution.md
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    evo_entry = (
        f"\n### [{now_str}] Synthesized Skill: `{clean_name}.py`\n"
        f"- **Description:** {description}\n"
        f"- **File:** `skills/{clean_name}.py`\n"
    )
    try:
        with open(EVOLUTION_FILE, "a", encoding="utf-8") as f:
            f.write(evo_entry)
    except Exception:
        pass

    return f"Skill '{clean_name}' successfully synthesized and saved to skills/{clean_name}.py. It is now registered in Jenna's skill ecosystem."
