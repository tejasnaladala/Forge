from __future__ import annotations

from duckduckgo_search import DDGS


async def search(query: str, num_results: int = 5) -> list[dict]:
    """Search the web for information. Returns titles, URLs, and snippets."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            return [
                {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
                for r in results
            ]
    except Exception as e:
        return [{"error": str(e)}]


def register_tools(registry) -> None:
    registry.register(
        name="web_search",
        func=search,
        description="Search the web for information. Returns titles, URLs, and snippets.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "num_results": {"type": "integer", "description": "Number of results to return", "default": 5},
            },
            "required": ["query"],
        },
    )
