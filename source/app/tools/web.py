import ipaddress
import json
from urllib.parse import urlsplit

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class WebSearchArgs(BaseModel):
    query: str = Field(min_length=3, max_length=500, description="A focused web search query")
    max_results: int = Field(default=5, ge=1, le=8, description="Maximum number of search results")


class WebExtractArgs(BaseModel):
    url: str = Field(min_length=8, max_length=2048, description="A public HTTPS webpage URL")


def _validate_public_https_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTPS URLs are accepted")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Private and local hosts are not accepted")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ValueError("Private and local hosts are not accepted")
    return value.strip()


def build_web_tools(api_key: str, max_results: int = 5):
    async def search_web(query: str, max_results: int = max_results) -> str:
        count = min(max(1, max_results), 8)
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": count,
            "include_answer": False,
            "include_raw_content": False,
        }
        try:
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return json.dumps(
                {"error": "Web search provider failed; no search results were obtained."},
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
                "published_date": item.get("published_date"),
                "score": item.get("score"),
            })
        return json.dumps(
            {"query": query, "results": results},
            ensure_ascii=False,
        )

    async def extract_web_page(url: str) -> str:
        try:
            safe_url = _validate_public_https_url(url)
        except ValueError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    "https://api.tavily.com/extract",
                    json={
                        "api_key": api_key,
                        "urls": [safe_url],
                        "extract_depth": "basic",
                        "format": "markdown",
                    },
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return json.dumps(
                {"error": "Page extraction failed; the page content was not retrieved."},
                ensure_ascii=False,
            )

        items = data.get("results", [])
        if not items:
            return json.dumps(
                {"url": safe_url, "error": "No page content was returned."},
                ensure_ascii=False,
            )
        item = items[0]
        return json.dumps({
            "url": item.get("url", safe_url),
            "content": (item.get("raw_content") or item.get("content") or "")[:12000],
        }, ensure_ascii=False)

    return [
        StructuredTool.from_function(
            name="web_search",
            description="Search the live web for current facts, recent news, rankings, weekly trends, products, or authoritative sources. Return real result titles, URLs, snippets, and publication dates when available.",
            coroutine=search_web,
            args_schema=WebSearchArgs,
        ),
        StructuredTool.from_function(
            name="web_extract",
            description="Retrieve and extract the readable content of one public HTTPS webpage URL returned by web_search. Use it to verify details before making specific claims.",
            coroutine=extract_web_page,
            args_schema=WebExtractArgs,
        ),
    ]
