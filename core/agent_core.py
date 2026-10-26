"""
Central agent brain: auto-discovers local "skills" (tools) and connects
to configured MCP servers, then builds a chosen Ollama model bound with
everything it found.

Skills: drop any .py file in ./skills/ that defines a tool with the
LangChain `@tool` decorator, and it's picked up automatically on the next
run — no manual registration needed.

MCP servers: configured in ./mcp_config.json. Each enabled entry is queried
at startup via langchain-mcp-adapters and its tools are added to the same
pool the model can call.
"""
import importlib.util
import json
from pathlib import Path
from typing import List

from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_ollama import ChatOllama
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    _HAS_MCP = True
except ImportError:
    MultiServerMCPClient = None
    _HAS_MCP = False

from config import (
    MODELS, DEFAULT_MODEL_KEY, MODEL_PROVIDERS, PROVIDER_MODELS,
    NVIDIA_API_BASE, NVIDIA_API_KEY,
    ULTRAMARINE_API_BASE, ULTRAMARINE_API_KEY,
    LMSTUDIO_HOST, LMSTUDIO_API_KEY,
    OLLAMA_HOST, OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE,
)

TOOLS_DIR = Path(__file__).parent.parent / "skills"
MCP_CONFIG_PATH = Path(__file__).parent.parent / "mcp_config.json"


def load_skills() -> List[BaseTool]:
    """Import every .py file in ./skills/ and collect @tool-decorated functions."""
    tools: List[BaseTool] = []
    if not TOOLS_DIR.exists():
        return tools
    for path in sorted(TOOLS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr in vars(module).values():
                if isinstance(attr, BaseTool):
                    tools.append(attr)
        except Exception as e:
            print(f"[tools] Notice: could not load tool '{path.name}': {e}")
    return tools


async def load_mcp_tools() -> List[BaseTool]:
    """Load tools from every MCP server in mcp_config.json with enabled=true."""
    if not _HAS_MCP or not MCP_CONFIG_PATH.exists():
        return []
    with open(MCP_CONFIG_PATH) as f:
        config = json.load(f)
    servers = {}
    for name, cfg in config.items():
        cfg = dict(cfg)
        if not cfg.pop("enabled", True):
            continue
        servers[name] = cfg
    if not servers:
        return []
    client = MultiServerMCPClient(servers)
    return await client.get_tools()


def get_model_config(model_key: str) -> dict:
    provider = MODEL_PROVIDERS.get(model_key, "ollama")
    # Cloud & LM Studio providers use their own model IDs; Ollama uses MODELS tags.
    if provider in ("nvidia", "ultramarine", "lmstudio"):
        model_name = PROVIDER_MODELS.get(provider, {}).get(model_key, model_key)
    else:
        model_name = MODELS.get(model_key, model_key)
    cfg = {"provider": provider, "name": model_name}
    # Resolve base_url / api_key for OpenAI-compatible providers.
    if provider == "nvidia":
        cfg.update({"base_url": NVIDIA_API_BASE, "api_key": NVIDIA_API_KEY})
    elif provider == "ultramarine":
        cfg.update({"base_url": ULTRAMARINE_API_BASE, "api_key": ULTRAMARINE_API_KEY})
    elif provider == "lmstudio":
        cfg.update({"base_url": LMSTUDIO_HOST, "api_key": LMSTUDIO_API_KEY or "lm-studio"})
    return cfg


class Agent:
    """A chosen local model (Ollama or cloud OpenAI-compatible provider) bound with the combined skill + MCP tool pool."""

    def __init__(self, model_key: str, tools: List[BaseTool]):
        self.model_key = model_key
        self.tools = tools
        self.tools_map = {t.name: t for t in tools}

        cfg = get_model_config(model_key)
        provider = cfg.get("provider", "ollama")
        model_name = cfg.get("name", model_key)
        base_url = cfg.get("base_url", "")
        api_key = cfg.get("api_key", "")

        openai_compatible = ("nvidia", "ultramarine", "lmstudio")
        if provider in openai_compatible:
            if not api_key:
                if provider != "lmstudio":
                    print(f"[agent] {provider.upper()}_API_KEY not set; falling back to Ollama.")
                    provider = "ollama"
                else:
                    api_key = "lm-studio"

        if provider in openai_compatible:
            from langchain_openai import ChatOpenAI
            base_llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key or "lm-studio",
                model=model_name,
                temperature=0.0,
            )
        else:
            base_llm = ChatOllama(
                base_url=OLLAMA_HOST,
                model=model_name,
                temperature=OLLAMA_OPTIONS.get("temperature", 0.7),
                num_ctx=OLLAMA_OPTIONS.get("num_ctx", 4096),
                num_predict=OLLAMA_OPTIONS.get("num_predict", 300),
                keep_alive=OLLAMA_KEEP_ALIVE,
            )

        self.llm = base_llm.bind_tools(tools)
        available_model_names = list(MODELS.keys())
        self.system_prompt = SystemMessage(
            content=(
                "You are Jenna, a local voice-first desktop assistant. "
                "Use a tool rather than guessing whenever the answer depends on real data. "
                "Keep answers concise — they may be read aloud by a text-to-speech engine. "
                "Do not run destructive commands without user confirmation.\n\n"
                f"MODEL SWITCHING RULES:\n"
                f"- You are currently running as the model: {model_key} ({model_name}).\n"
                f"- Available model keys: {available_model_names}.\n"
                "- If the user requests switching models, use the switch_model tool if available."
            )
        )

    async def run_turn(self, user_text: str, history=None) -> str:
        from langchain_core.messages import HumanMessage
        messages = [self.system_prompt]
        if history:
            messages.extend(history)
        messages.append(HumanMessage(content=user_text))

        # Simple ReAct loop: let the model call tools, then answer.
        max_tool_steps = 5
        for _ in range(max_tool_steps):
            ai = await self.llm.ainvoke(messages)
            messages.append(ai)
            if not ai.tool_calls:
                return ai.content or ""
            for tool_call in ai.tool_calls:
                name = tool_call["name"]
                args = tool_call.get("args", {})
                tool = self.tools_map.get(name)
                if tool is None:
                    result = f"Error: unknown tool '{name}'."
                else:
                    try:
                        if hasattr(tool, "ainvoke"):
                            result = await tool.ainvoke(args)
                        else:
                            result = tool.invoke(args)
                    except Exception as e:
                        result = f"Error calling {name}: {e}"
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        return "I had trouble completing that — want to try again?"
