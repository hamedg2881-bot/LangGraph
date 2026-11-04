import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver

from app.graph.chat import build_chat_graph


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
        self.bound_tools = None

    def bind_tools(self, tools, tool_choice="auto"):
        self.bound_tools = tools
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
    async def test_structured_tool_call_executes_and_returns_to_assistant(self):
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
                {"messages": [{"role": "user", "content": "جست‌وجو کن"}]},
                config={
                    "recursion_limit": 8,
                    "configurable": {
                        "thread_id": "tool-cycle-test",
                    },
                },
            )

        self.assertEqual(len(model.calls), 2)
        self.assertEqual(result["messages"][-1].content, "نتیجه بررسی شد")
        self.assertTrue(any(isinstance(message, ToolMessage) for message in model.calls[1]))


if __name__ == "__main__":
    unittest.main()
