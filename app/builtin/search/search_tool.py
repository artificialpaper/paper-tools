"""Built-in web search tool."""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web for information."""
    logger.info("tool.web_search", extra={"query": query, "max_results": max_results})
    return {"query": query, "results": [], "total": 0, "note": "Implement with SerpAPI or Tavily in production"}
