import json

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class WebSearchArgs(BaseModel):
    query: str = Field(min_length=3, max_length=500, description="A focused web search query")
    max_results: int = Field(default=5, ge=1, le=8, description="Maximum number of search results")


def build_web_tools(base_url: str, max_results: int = 5):
    endpoint = f"{base_url.rstrip('/')}/search"

    async def search_web(query: str, max_results: int = max_results) -> str:
        count = min(max(1, max_results), 8)
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
                response = await client.get(
                    endpoint,
                    params={
                        "q": query,
                        "format": "json",
                        "language": "all",
                        "safesearch": 0,
                    },
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return json.dumps(
                {
                    "error": (
                        "SearXNG search failed or JSON output is unavailable. "
                        "No search results were obtained."
                    )
                },
                ensure_ascii=False,
            )

        results = []
        for item in data.get("results", [])[:count]:
            if not isinstance(item, dict):
                continue
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": (item.get("content") or "")[:3500],
                "published_date": item.get("publishedDate"),
                "engine": item.get("engine"),
                "score": item.get("score"),
            })
        return json.dumps(
            {"provider": "SearXNG", "query": query, "results": results},
            ensure_ascii=False,
        )

    return [
        StructuredTool.from_function(
            name="web_search",
            description=(
                "Search the live web through the deployment's SearXNG instance for "
                "current facts, recent news, rankings, weekly trends, products, or "
                "authoritative sources. Return actual result titles, URLs, snippets, "
                "and publication dates when available."
            ),
            coroutine=search_web,
            args_schema=WebSearchArgs,
        ),
    ]
