import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver

from app.graph.chat import build_chat_graph
from app.tools.web_intent import is_web_research_request


def _fake_search_tool():
    def search(query: str) -> str:
        return f"search-result:{query}"

    return StructuredTool.from_function(
        search,
        name="web_search",
        description="Test-only deterministic search tool",
    )


class FakeToolCallingModel:
    def __init__(self):
        self.calls = []
        self.tool_choices = []

    def bind_tools(self, tools, tool_choice="auto"):
        self.tool_choices.append(tool_choice)
        return self

    async def ainvoke(self, messages, config=None):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "web_search",
                        "args": {"query": "آزمایش"},
                        "id": "call-search-1",
                        "type": "tool_call",
                    }
                ],
            )

        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        if not tool_messages:
            raise AssertionError("The assistant was called again without a tool result")
        return AIMessage(content="نتیجه بررسی شد")


class ChatGraphToolCycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_research_forces_tool_then_returns_to_assistant(self):
        model = FakeToolCallingModel()
        settings = SimpleNamespace(
            searxng_base_url="http://127.0.0.1:8888",
            web_search_max_results=5,
        )

        with patch("app.graph.chat.build_web_tools", return_value=[_fake_search_tool()]):
            graph = build_chat_graph(
                checkpointer=MemorySaver(),
                model=model,
                settings=settings,
            )
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content="خبرهای مهم هوش مصنوعی در هفته اخیر را جست‌وجو کن")]},
                config={
                    "recursion_limit": 8,
                    "configurable": {"thread_id": "tool-cycle-test"},
                },
            )

        self.assertEqual(len(model.calls), 2)
        self.assertEqual(model.tool_choices, ["required", "auto"])
        self.assertEqual(result["messages"][-1].content, "نتیجه بررسی شد")
        self.assertTrue(any(isinstance(message, ToolMessage) for message in model.calls[1]))
        self.assertIn("Current server-local date and time:", model.calls[0][0].content)

    async def test_normal_chat_keeps_automatic_tool_choice(self):
        model = FakeToolCallingModel()
        settings = SimpleNamespace(
            searxng_base_url="http://127.0.0.1:8888",
            web_search_max_results=5,
        )
        with patch("app.graph.chat.build_web_tools", return_value=[_fake_search_tool()]):
            graph = build_chat_graph(MemorySaver(), model=model, settings=settings)
            await graph.ainvoke(
                {"messages": [HumanMessage(content="سلام، حالت چطوره؟")]},
                config={"recursion_limit": 8, "configurable": {"thread_id": "normal-chat"}},
            )
        self.assertEqual(model.tool_choices[0], "auto")


class WebIntentTests(unittest.TestCase):
    def test_detects_persian_and_english_research_requests(self):
        self.assertTrue(is_web_research_request("خبرهای مهم هوش مصنوعی در هفته اخیر را جست‌وجو کن"))
        self.assertTrue(is_web_research_request("Search for the latest AI news this week"))
        self.assertTrue(is_web_research_request("قیمت امروز بیت‌کوین چقدر است؟"))

    def test_does_not_force_search_for_general_chat(self):
        self.assertFalse(is_web_research_request("سلام، حالت چطوره؟"))
        self.assertFalse(is_web_research_request("Explain how a neural network works"))


if __name__ == "__main__":
    unittest.main()
