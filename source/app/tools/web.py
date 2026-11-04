import json
from urllib.parse import urlparse

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class WebSearchArgs(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=500,
        description="A focused search query using the user's language and key entities",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=8,
        description="Maximum number of distinct search results",
    )


def _valid_result_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def build_web_tools(base_url: str, max_results: int = 5):
    endpoint = f"{base_url.rstrip('/')}/search"
    default_count = min(max(1, max_results), 8)

    async def search_web(query: str, max_results: int = default_count) -> str:
        count = min(max(1, max_results), 8)
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=5.0),
                follow_redirects=False,
            ) as client:
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
        except httpx.TimeoutException:
            return json.dumps(
                {"ok": False, "error": "search_timeout", "message": "SearXNG did not respond before the search timeout. No results were obtained."},
                ensure_ascii=False,
            )
        except httpx.HTTPStatusError as exc:
            return json.dumps(
                {"ok": False, "error": "search_http_error", "status_code": exc.response.status_code, "message": "SearXNG rejected the search request. No results were obtained."},
                ensure_ascii=False,
            )
        except (httpx.HTTPError, ValueError):
            return json.dumps(
                {"ok": False, "error": "search_unavailable", "message": "SearXNG is unavailable or JSON output is disabled. No results were obtained."},
                ensure_ascii=False,
            )

        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            return json.dumps(
                {"ok": False, "error": "invalid_search_response", "message": "SearXNG returned an invalid response. No results were obtained."},
                ensure_ascii=False,
            )

        results = []
        seen_urls = set()
        for item in data["results"]:
            if not isinstance(item, dict):
                continue
            url = _valid_result_url(item.get("url"))
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({
                "title": str(item.get("title") or "")[:500],
                "url": url,
                "snippet": str(item.get("content") or "")[:2500],
                "published_date": item.get("publishedDate"),
                "engine": item.get("engine"),
            })
            if len(results) >= count:
                break

        return json.dumps(
            {
                "ok": True,
                "provider": "SearXNG",
                "query": query,
                "result_count": len(results),
                "results": results,
            },
            ensure_ascii=False,
        )

    return [
        StructuredTool.from_function(
            name="web_search",
            description=(
                "Search the live web through SearXNG. Use this for current facts, "
                "recent news, trends, rankings, prices, schedules, product details, "
                "or when the user explicitly asks to search the web. For broad "
                "research, run focused searches for the main sub-questions. The "
                "result contains real URLs and snippets; never invent or alter them."
            ),
            coroutine=search_web,
            args_schema=WebSearchArgs,
        ),
    ]
