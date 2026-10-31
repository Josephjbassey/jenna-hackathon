"""Browser & Web Content Reader Skill for Jenna-Unified.

Enables Jenna to:
- Read full articles and web pages from URLs
- Convert HTML to clean markdown
- Extract tables and structured documentation from websites
"""
import re
from langchain_core.tools import tool

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


def _clean_html_to_markdown(html_text: str) -> str:
    """Lightweight clean converter from HTML to readable markdown text."""
    # Strip script and style tags
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    # Headings
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text, flags=re.IGNORECASE)
    # Paragraphs and line breaks
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", text, flags=re.IGNORECASE)
    # Links
    text = re.sub(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE)
    # Strip all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@tool
def fetch_webpage_content(url: str, max_chars: int = 4000) -> str:
    """Fetch and read the main content of any public URL as clean Markdown.
    
    Args:
        url: The web URL to inspect (e.g. 'https://docs.python.org/3/whatsnew/3.11.html')
        max_chars: Maximum characters to return (default: 4000)
    """
    if not _HAS_HTTPX:
        return "HTTP client is not available."

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Jenna-Unified-Agent"
    }

    try:
        with httpx.Client(timeout=12.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            raw_html = resp.text

        md_content = _clean_html_to_markdown(raw_html)
        if len(md_content) > max_chars:
            md_content = md_content[:max_chars] + f"\n\n... [Content truncated to {max_chars} chars. Use specific sub-pages if more detail is needed]"

        return f"### Webpage Content from {url}:\n\n{md_content}"
    except Exception as e:
        return f"Failed to fetch content from {url}: {e}"
