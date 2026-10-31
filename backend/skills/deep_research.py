"""Deep Research & Web Intelligence Skill for Jenna-Unified.

Inspired by top agent research skills:
- Live web search with DuckDuckGo Search (no API keys required)
- Multi-query synthesis
- News search & domain filtering
- Citation gathering
"""
from typing import List, Optional
from langchain_core.tools import tool

try:
    from duckduckgo_search import DDGS
    _HAS_DDG = True
except ImportError:
    _HAS_DDG = False


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the public live web for up-to-date facts, documentation, news, or technical answers.
    
    Args:
        query: Search keywords or question
        max_results: Number of results to return (default: 5)
    """
    if not _HAS_DDG:
        return "DuckDuckGo search package is not available in the environment."

    try:
        results = []
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            for i, r in enumerate(raw_results, 1):
                title = r.get("title", "Untitled")
                link = r.get("href", "")
                snippet = r.get("body", "")
                results.append(f"{i}. [{title}]({link})\n   {snippet}")

        if not results:
            return f"No search results found for '{query}'."

        return f"### Web Search Results for '{query}':\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Web search encountered an error: {e}"


@tool
def deep_research_topic(topic: str, num_queries: int = 3) -> str:
    """Perform a deep multi-faceted research synthesis across multiple search queries on a complex topic.
    
    Args:
        topic: The broad topic, technology, or problem to research
        num_queries: Number of perspective queries to execute (default: 3)
    """
    if not _HAS_DDG:
        return "Search engine not available."

    perspectives = [
        f"{topic} overview architecture",
        f"{topic} best practices comparison",
        f"{topic} latest updates 2026",
    ]

    findings = []
    with DDGS() as ddgs:
        for q in perspectives[:num_queries]:
            try:
                sub_res = list(ddgs.text(q, max_results=2))
                findings.append(f"#### Perspective: '{q}'")
                for r in sub_res:
                    findings.append(f"- **{r.get('title')}**: {r.get('body')} ([Source]({r.get('href')}))")
            except Exception:
                continue

    if not findings:
        return f"Deep research could not retrieve data for topic '{topic}'."

    return f"### Deep Research Dossier: {topic}\n\n" + "\n".join(findings)


@tool
def search_latest_news(query: str, max_results: int = 5) -> str:
    """Search for the most recent news articles published regarding a subject.
    
    Args:
        query: Topic or organization to find recent news for
        max_results: Number of news stories (default: 5)
    """
    if not _HAS_DDG:
        return "Search engine not available."

    try:
        news_items = []
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results))
            for i, n in enumerate(raw, 1):
                title = n.get("title", "")
                link = n.get("url", "")
                date = n.get("date", "")
                body = n.get("body", "")
                news_items.append(f"{i}. **{title}** ({date})\n   {body}\n   Link: {link}")

        if not news_items:
            return f"No recent news found for '{query}'."

        return f"### Recent News for '{query}':\n\n" + "\n\n".join(news_items)
    except Exception as e:
        return f"News search error: {e}"
