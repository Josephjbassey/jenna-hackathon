"""
Delegation Tools for Squad Coordination
Allows Commander to delegate tasks to specialist agents.
"""
from langchain_core.tools import tool
from typing import Dict, Any, List


@tool
def delegate_to_planner(task: str, context: str = "") -> str:
    """
    Delegate a planning/task decomposition task to the Planner agent (Muse Spark).
    Use for: breaking down complex goals, creating execution plans, agent orchestration.
    
    Args:
        task: The task to plan (e.g., "Build a web scraper for docs")
        context: Additional context (e.g., "User wants Python, use requests/BeautifulSoup")
    
    Returns:
        A structured plan with steps, dependencies, and agent assignments.
    """
    return f"[DELEGATED TO PLANNER] Task: {task}\nContext: {context}\n\nThis will be processed by the Planner agent with Muse Spark."


@tool
def delegate_to_engineer(task: str, context: str = "") -> str:
    """
    Delegate a code/engineering task to the Engineer agent (Muse Code).
    Use for: code generation, debugging, refactoring, terminal tasks, architecture.
    
    Args:
        task: The engineering task (e.g., "Create a FastAPI endpoint for user auth")
        context: Technical context (e.g., "Use JWT, PostgreSQL, async SQLAlchemy")
    
    Returns:
        Generated code, implementation, or debugging solution.
    """
    return f"[DELEGATED TO ENGINEER] Task: {task}\nContext: {context}\n\nThis will be processed by the Engineer agent with Muse Code."


@tool
def delegate_to_scholar(task: str, context: str = "") -> str:
    """
    Delegate a research/analysis task to the Scholar agent (Muse Wonder).
    Use for: deep research, vision analysis, image segmentation, documentation synthesis.
    
    Args:
        task: The research task (e.g., "Analyze this image for defects")
        context: Research context (e.g., "Focus on structural cracks in concrete")
    
    Returns:
        Research findings, analysis, or vision results.
    """
    return f"[DELEGATED TO SCHOLAR] Task: {task}\nContext: {context}\n\nThis will be processed by the Scholar agent with Muse Wonder."


@tool
def delegate_to_writer(task: str, context: str = "") -> str:
    """
    Delegate a writing/content task to the Writer agent (Muse Spark).
    Use for: documentation, reports, creative writing, content generation.
    
    Args:
        task: The writing task (e.g., "Write API documentation for the auth module")
        context: Style/context (e.g., "OpenAPI 3.0 format, technical audience")
    
    Returns:
        Generated content in the requested format.
    """
    return f"[DELEGATED TO WRITER] Task: {task}\nContext: {context}\n\nThis will be processed by the Writer agent with Muse Spark."


# List all delegation tools
DELEGATION_TOOLS = [
    delegate_to_planner,
    delegate_to_engineer,
    delegate_to_scholar,
    delegate_to_writer,
]