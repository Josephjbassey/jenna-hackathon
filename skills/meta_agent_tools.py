"""
Meta Model Agent Skill Assignment
Assigns Meta model tools to appropriate agents based on their roles.
"""
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from skills.meta_models import META_TOOLS, get_meta_client


def get_meta_tools_for_role(role: str) -> List[BaseTool]:
    """Get Meta tools assigned to a specific agent role."""
    role_tools = {
        "commander": [meta_reason, meta_advanced_reason],
        "planner": [meta_reason, meta_advanced_reason],
        "coder": [meta_code_generate, meta_reason],
        "researcher": [meta_advanced_reason, meta_generate_image, meta_segment_image],
        "desktop": [meta_segment_image],
        "communicator": [meta_transcribe],
        "scheduler": [meta_reason],
    }
    tool_funcs = role_tools.get(role, [])
    return [t for t in META_TOOLS if t.func in tool_funcs]


# Import the tool functions for reference
from skills.meta_models import (
    meta_reason, meta_transcribe, meta_generate_image,
    meta_segment_image, meta_advanced_reason, meta_code_generate
)


def inject_meta_tools(tools: List[BaseTool], role: str) -> List[BaseTool]:
    """Inject Meta tools into an agent's tool list based on role."""
    meta_tools = get_meta_tools_for_role(role)
    # Avoid duplicates by name
    existing_names = {t.name for t in tools}
    for tool in meta_tools:
        if tool.name not in existing_names:
            tools.append(tool)
    return tools