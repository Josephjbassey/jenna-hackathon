"""
LangGraph multi-agent orchestration graph for Jenna-Unified.

Implements a compiled StateGraph with:
- Supervisor / Commander (fast model): triages user input, invokes tools, and routes complex tasks.
- Specialist Worker Nodes: Engineer (Coder), Scholar (Researcher), Planner (Reasoning), Writer (Creative).
- Memory Checkpointing (MemorySaver): persistent conversation threads.
- Tool Node: execution of file tools, communications, computer use, and vision.
- Meta Model Integration: Muse Spark, Muse Voice, Muse Image, SAM 3.1 for hackathon.
"""
import os
import sys
from typing import Annotated, Sequence, TypedDict, Literal
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import MODELS, SQUAD_ROLES, ASSISTANT_NAME, USER_NAME, META_MODEL_API_KEY
from core.agent_core import get_model_config, load_skills


class SquadState(TypedDict):
    """The central state flowing through the Jenna multi-agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_action: str
    active_role: str
    task_context: dict  # For passing context between agents


def _get_llm(model_key: str):
    """Factory to build the appropriate LLM (Ollama or LM Studio/OpenAI compatible/Meta)."""
    from langchain_ollama import ChatOllama
    from config import OLLAMA_HOST, OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE

    cfg = get_model_config(model_key)
    provider = cfg.get("provider", "ollama")
    model_name = cfg.get("name", model_key)
    base_url = cfg.get("base_url")
    api_key = cfg.get("api_key")

    if provider in ("nvidia", "ultramarine", "lmstudio", "meta"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=base_url,
            api_key=api_key or "lm-studio",
            model=model_name,
            temperature=0.2 if model_key in ("coder", "planner") else 0.7,
        )
    return ChatOllama(
        base_url=OLLAMA_HOST,
        model=model_name,
        temperature=OLLAMA_OPTIONS.get("temperature", 0.7),
        num_ctx=OLLAMA_OPTIONS.get("num_ctx", 4096),
        num_predict=OLLAMA_OPTIONS.get("num_predict", 350),
        keep_alive=OLLAMA_KEEP_ALIVE,
    )


def _create_specialist_llm(role: str, tools: Sequence[BaseTool]):
    """Create an LLM for a specialist role with their specific tools."""
    role_config = SQUAD_ROLES.get(role, {})
    model_key = role_config.get("model_key", "fast")
    llm = _get_llm(model_key)
    return llm.bind_tools(tools)


class JennaGraphAgent:
    """Compiled LangGraph agent coordinating the Jenna squad."""

    def __init__(self, tools: Sequence[BaseTool] = None):
        self.tools = list(tools or load_skills())
        self.tools_map = {t.name: t for t in self.tools}
        
        # Load Meta tools if API key available
        self.meta_tools = []
        if META_MODEL_API_KEY:
            try:
                from skills.meta_agent_tools import get_meta_tools_for_role
                # Pre-load meta tools for each role
                self.meta_tools_by_role = {
                    role: get_meta_tools_for_role(role) 
                    for role in SQUAD_ROLES.keys()
                }
            except Exception as e:
                print(f"[graph] Meta tools not available: {e}")
                self.meta_tools_by_role = {}
        else:
            self.meta_tools_by_role = {}

        # Base tools for commander
        self.commander_llm = _get_llm("fast").bind_tools(self.tools)
        self.memory = MemorySaver()

        # Build Graph
        workflow = StateGraph(SquadState)

        # Add Nodes
        workflow.add_node("commander", self._commander_node)
        workflow.add_node("tool_executor", self._tool_executor_node)
        
        # Specialist nodes (only added if Meta API key available)
        if META_MODEL_API_KEY:
            workflow.add_node("planner", self._create_specialist_node("planner"))
            workflow.add_node("engineer", self._create_specialist_node("engineer"))
            workflow.add_node("scholar", self._create_specialist_node("scholar"))
            workflow.add_node("writer", self._create_specialist_node("writer"))

        # Add Edges
        workflow.add_edge(START, "commander")
        workflow.add_conditional_edges(
            "commander",
            self._route_commander,
            {
                "execute_tools": "tool_executor",
                "delegate_planner": "planner" if META_MODEL_API_KEY else "tool_executor",
                "delegate_engineer": "engineer" if META_MODEL_API_KEY else "tool_executor",
                "delegate_scholar": "scholar" if META_MODEL_API_KEY else "tool_executor",
                "delegate_writer": "writer" if META_MODEL_API_KEY else "tool_executor",
                "finish": END,
            }
        )
        workflow.add_edge("tool_executor", "commander")
        
        # Specialist edges (return to commander after completion)
        if META_MODEL_API_KEY:
            for specialist in ["planner", "engineer", "scholar", "writer"]:
                workflow.add_edge(specialist, "commander")

        self.graph = workflow.compile(checkpointer=self.memory)

    def _build_commander_prompt(self) -> str:
        meta_roles = []
        if META_MODEL_API_KEY:
            meta_roles = [
                "Planner (Muse Spark): multi-step reasoning, task decomposition, agent orchestration",
                "Engineer (Muse Code): code generation, debugging, refactoring, terminal tasks",
                "Scholar (Muse Wonder): deep research, vision analysis, image segmentation, documentation",
            ]
        return (
            f"You are {ASSISTANT_NAME}, an autonomous local voice assistant for {USER_NAME}. "
            "Keep responses concise, clear, and direct (they may be read aloud by TTS). "
            "Use the available tools when data or action is needed. "
            "For heavy coding, research, or planning, invoke delegate_to_specialist with the appropriate role.\n\n"
            f"Available specialists:\n" + "\n".join(f"- {r}" for r in meta_roles)
        )

    async def _commander_node(self, state: SquadState) -> dict:
        """Commander node: acts as primary conversationalist and tool dispatcher."""
        messages = list(state["messages"])
        sys_prompt = SystemMessage(
            content=self._build_commander_prompt()
        )
        full_context = [sys_prompt] + messages
        response = await self.commander_llm.ainvoke(full_context)
        return {
            "messages": [response],
            "next_action": "execute_tools" if getattr(response, "tool_calls", None) else "finish",
            "active_role": "commander",
        }

    async def _tool_executor_node(self, state: SquadState) -> dict:
        """Executes tool calls generated by the Commander."""
        last_message = state["messages"][-1]
        tool_messages = []

        for call in getattr(last_message, "tool_calls", []):
            name = call["name"]
            args = call.get("args", {})
            call_id = call.get("id", name)
            tool = self.tools_map.get(name)

            if tool is None:
                res = f"Error: Tool '{name}' not found."
            else:
                try:
                    if hasattr(tool, "ainvoke"):
                        res = await tool.ainvoke(args)
                    else:
                        res = tool.invoke(args)
                except Exception as e:
                    res = f"Error running {name}: {e}"

            tool_messages.append(ToolMessage(content=str(res), tool_call_id=call_id))

        return {"messages": tool_messages}

    def _create_specialist_node(self, role: str):
        """Factory to create a specialist node with role-specific tools and prompt."""
        role_config = SQUAD_ROLES.get(role, {})
        model_key = role_config.get("model_key", "fast")
        meta_model = role_config.get("meta_model", "")
        description = role_config.get("description", "")
        
        # Combine base tools + meta tools for this role
        specialist_tools = list(self.tools)
        if role in self.meta_tools_by_role:
            specialist_tools.extend(self.meta_tools_by_role[role])
        
        specialist_llm = _create_specialist_llm(role, specialist_tools)
        
        prompt = SystemMessage(
            content=(
                f"You are the {role_config.get('name', role.title())}. "
                f"{description} "
                f"Model: {meta_model or 'Local'}.\n\n"
                "Complete the assigned task thoroughly. Return only your final output."
            )
        )
        
        async def specialist_node(state: SquadState) -> dict:
            messages = list(state["messages"])
            # Add context if available
            context = state.get("task_context", {})
            if context:
                messages = [SystemMessage(content=f"Task context: {context}")] + messages
            
            full_context = [prompt] + messages
            response = await specialist_llm.ainvoke(full_context)
            return {
                "messages": [response],
                "active_role": role,
            }
        
        return specialist_node

    def _route_commander(self, state: SquadState) -> str:
        """Decide whether to execute tools, delegate to specialist, or complete turn."""
        last_msg = state["messages"][-1]
        
        # Check for tool calls
        if getattr(last_msg, "tool_calls", None):
            for call in last_msg.tool_calls:
                name = call["name"]
                # Route to specialist based on tool name
                if name.startswith("delegate_") and META_MODEL_API_KEY:
                    specialist = name.replace("delegate_", "")
                    if specialist in ["planner", "engineer", "scholar", "writer"]:
                        return f"delegate_{specialist}"
            return "execute_tools"
        return "finish"

    async def run_turn(self, text: str, thread_id: str = "default") -> str:
        """Execute a full conversational turn through the LangGraph state graph."""
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [HumanMessage(content=text)], "task_context": {}}
        
        result = await self.graph.ainvoke(inputs, config=config)
        last_msg = result["messages"][-1]
        return getattr(last_msg, "content", "") or ""


# Global singleton factory
_graph_agent = None

def get_graph_agent() -> JennaGraphAgent:
    global _graph_agent
    if _graph_agent is None:
        _graph_agent = JennaGraphAgent()
    return _graph_agent