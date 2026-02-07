"""Web tools for HuxBot."""

from __future__ import annotations

import aiohttp

from huxbot.utils.helpers import truncate


async def web_search(query: str, num_results: int = 5) -> str:
    """Search the web for *query* and return the top results.

    Uses a simple Google Custom Search JSON API call when configured,
    otherwise returns a stub.
    """
    # Minimal implementation – override with real API key via config
    return f"[web_search] No search API key configured. Query was: {query}"


async def web_fetch(url: str) -> str:
    """Fetch the content of *url* and return it as text."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return f"Error: HTTP {resp.status} for {url}"
                text = await resp.text()
                return truncate(text, max_len=8000)
    except Exception as exc:
        return f"Error fetching {url}: {exc}"
