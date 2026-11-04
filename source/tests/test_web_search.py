import json
import unittest
from unittest.mock import patch

from app.tools.web import build_web_tools


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, response=None, **kwargs):
        self.response = response
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        self.request = (url, params, headers)
        return self.response


class WebSearchToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_filters_invalid_and_duplicate_urls_and_bounds_results(self):
        payload = {
            "results": [
                {"title": "First", "url": "https://example.com/a", "content": "محتوا"},
                {"title": "Duplicate", "url": "https://example.com/a", "content": "تکراری"},
                {"title": "Unsafe", "url": "javascript:alert(1)", "content": "bad"},
                {"title": "Second", "url": "http://example.org/b", "content": "متن"},
            ]
        }
        fake_client = FakeAsyncClient(FakeResponse(payload))

        with patch("app.tools.web.httpx.AsyncClient", return_value=fake_client):
            tool = build_web_tools("http://searxng:8080", max_results=2)[0]
            raw = await tool.ainvoke({"query": "آزمایش", "max_results": 2})

        result = json.loads(raw)
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_count"], 2)
        self.assertEqual(
            [item["url"] for item in result["results"]],
            ["https://example.com/a", "http://example.org/b"],
        )
        self.assertEqual(fake_client.request[1]["format"], "json")

    async def test_invalid_searxng_payload_is_not_reported_as_success(self):
        fake_client = FakeAsyncClient(FakeResponse({"unexpected": []}))

        with patch("app.tools.web.httpx.AsyncClient", return_value=fake_client):
            tool = build_web_tools("http://searxng:8080")[0]
            raw = await tool.ainvoke({"query": "آزمایش"})

        result = json.loads(raw)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_search_response")


if __name__ == "__main__":
    unittest.main()
