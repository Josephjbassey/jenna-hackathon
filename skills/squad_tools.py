"""Squad delegation tools: delegate tasks to specialized subagents.

Enables the primary fast voice agent to dispatch deep coding, planning,
research, or writing tasks to specialized local models (Qwen-Coder, Phi-4, Llama 3.2, etc.).
"""
import os
import sys
from langchain_core.tools import tool

# Ensure root directory is in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


@tool
def delegate_to_specialist(role: str, task: str) -> str:
    """Delegate a complex task to a specialized agent in the squad.
    
    Roles available:
      - 'coder': For code writing, debugging, refactoring, script analysis (uses Qwen2.5-Coder).
      - 'planner': For architectural design, task breakdowns, step-by-step logic (uses Phi-4 / Reasoning).
      - 'researcher': For information retrieval, data analysis, deep synthesis (uses Qwen / Llama).
      - 'writer': For creative writing, documentation, structured reports, email drafts (uses Llama 3.2).
    
    Usage: delegate_to_specialist(role="coder", task="Write a Python script to monitor CPU usage")
    """
    from config import MODELS, SQUAD_ROLES, OLLAMA_HOST, OLLAMA_OPTIONS
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    role = role.lower().strip()
    if role not in MODELS:
        # Fallback to closest matching role or coder
        for cand in ["coder", "planner", "researcher", "writer"]:
            if cand in role:
                role = cand
                break
        else:
            role = "coder"

    model_name = MODELS.get(role, MODELS.get("fast"))
    role_meta = SQUAD_ROLES.get(role, {"name": f"Jenna {role.capitalize()}", "description": "Specialist agent"})

    sys_prompt = (
        f"You are {role_meta.get('name')}, a specialized subagent in the Jenna AI squad.\n"
        f"Your specialty: {role_meta.get('description')}.\n"
        f"Active model: {model_name}.\n"
        "Deliver clear, high-quality, practical output without fluff or unnecessary preamble."
    )

    try:
        from core.agent_core import get_model_config
        cfg = get_model_config(role)
        provider = cfg.get("provider", "ollama")
        model_name = cfg.get("name", role)
        base_url = cfg.get("base_url")
        api_key = cfg.get("api_key")

        if provider in ("nvidia", "ultramarine", "lmstudio"):
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key or "lm-studio",
                model=model_name,
                temperature=0.3 if role in ("coder", "planner") else 0.7,
            )
        else:
            llm = ChatOllama(
                base_url=OLLAMA_HOST,
                model=model_name,
                temperature=0.3 if role in ("coder", "planner") else 0.7,
                num_ctx=OLLAMA_OPTIONS.get("num_ctx", 4096),
                num_predict=600,
            )

        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=task)
        ])
        content = response.content if hasattr(response, "content") else str(response)
        return f"[{role_meta.get('name')} Output via {provider.upper()} ({model_name})]:\n{content}"
    except Exception as e:
        return f"Failed to delegate to {role} ({model_name}): {e}"


@tool
def list_squad_roles() -> str:
    """List the squad roles and active local models assigned to each role."""
    from config import MODELS, SQUAD_ROLES
    lines = ["Active Jenna Squad Roster:"]
    for role_key, meta in SQUAD_ROLES.items():
        model = MODELS.get(role_key, "default")
        lines.append(f" - {meta.get('name')} ({role_key}): model='{model}' — {meta.get('description')}")
    return "\n".join(lines)
