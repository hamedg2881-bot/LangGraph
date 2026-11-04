import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver

from app.graph.chat import build_chat_graph
from app.tools.web_intent import is_web_research_request
from app.tools.qwen_tool_calls import parse_qwen_tool_calls
from app.tools.web import WebSearchArgs


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
        self.assertTrue(is_web_research_request("Research recent developments in AI"))
        self.assertTrue(is_web_research_request("درباره معماری مدل‌ها تحقیق کن"))

    def test_does_not_force_search_for_general_chat(self):
        self.assertFalse(is_web_research_request("سلام، حالت چطوره؟"))
        self.assertFalse(is_web_research_request("Explain how a neural network works"))




class QwenToolCallParsingTests(unittest.TestCase):
    def test_converts_complete_registered_tool_call(self):
        tool = _fake_search_tool()
        message = AIMessage(
            content=(
                "<tool_call><function=web_search>"
                "<parameter=query>AI news &amp; research</parameter>"
                "</function></tool_call>"
            )
        )

        parsed = parse_qwen_tool_calls(message, [tool])

        self.assertEqual(parsed.content, "")
        self.assertEqual(len(parsed.tool_calls), 1)
        self.assertEqual(parsed.tool_calls[0]["name"], "web_search")
        self.assertEqual(parsed.tool_calls[0]["args"], {"query": "AI news & research"})

    def test_converts_multiple_calls(self):
        tool = _fake_search_tool()
        message = AIMessage(
            content=(
                "<tool_call><function=web_search>"
                "<parameter=query>first search</parameter>"
                "</function></tool_call>\n"
                "<tool_call><function=web_search>"
                "<parameter=query>second search</parameter>"
                "</function></tool_call>"
            )
        )

        parsed = parse_qwen_tool_calls(message, [tool])

        self.assertEqual(len(parsed.tool_calls), 2)
        self.assertEqual(
            [call["args"]["query"] for call in parsed.tool_calls],
            ["first search", "second search"],
        )

    def test_rejects_unknown_tool_unknown_parameter_and_malformed_markup(self):
        tool = _fake_search_tool()
        cases = [
            "<tool_call><function=delete_all><parameter=query>test</parameter></function></tool_call>",
            "<tool_call><function=web_search><parameter=command>test</parameter></function></tool_call>",
            "<tool_call><function=web_search><parameter=query>test</function></tool_call>",
            "Do this: <tool_call><function=web_search><parameter=query>test</parameter></function></tool_call>",
        ]

        for content in cases:
            with self.subTest(content=content):
                message = AIMessage(content=content)
                self.assertIs(parse_qwen_tool_calls(message, [tool]), message)

    def test_rejects_arguments_that_fail_tool_schema_validation(self):
        tool = StructuredTool.from_function(
            lambda query, max_results=5: query,
            name="web_search",
            description="Schema validation test",
            args_schema=WebSearchArgs,
        )
        message = AIMessage(
            content=(
                "<tool_call><function=web_search>"
                "<parameter=query>x</parameter>"
                "</function></tool_call>"
            )
        )

        self.assertIs(parse_qwen_tool_calls(message, [tool]), message)


class FakeQwenXmlToolCallingModel(FakeToolCallingModel):
    async def ainvoke(self, messages, config=None):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "web_search",
                        "args": {"query": "first search"},
                        "id": "call-initial",
                        "type": "tool_call",
                    }
                ],
            )
        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        if len(tool_messages) == 1:
            return AIMessage(
                content=(
                    "<tool_call><function=web_search>"
                    "<parameter=query>second search</parameter>"
                    "</function></tool_call>"
                )
            )
        if len(tool_messages) == 2:
            return AIMessage(content="پاسخ نهایی")
        raise AssertionError("Unexpected model invocation")


class ChatGraphQwenXmlCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_xml_tool_call_is_normalized_and_executed_by_tool_node(self):
        model = FakeQwenXmlToolCallingModel()
        settings = SimpleNamespace(
            searxng_base_url="http://127.0.0.1:8888",
            web_search_max_results=5,
        )
        with patch("app.graph.chat.build_web_tools", return_value=[_fake_search_tool()]):
            graph = build_chat_graph(MemorySaver(), model=model, settings=settings)
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content="Search the web for current AI news")]},
                config={
                    "recursion_limit": 10,
                    "configurable": {"thread_id": "qwen-xml-tool-cycle"},
                },
            )

        self.assertEqual(result["messages"][-1].content, "پاسخ نهایی")
        self.assertEqual(model.tool_choices, ["required", "auto", "auto"])
        tool_results = [
            message.content for message in result["messages"]
            if isinstance(message, ToolMessage)
        ]
        self.assertEqual(tool_results, ["search-result:first search", "search-result:second search"])

if __name__ == "__main__":
    unittest.main()


class StreamingUpdateTests(unittest.TestCase):
    def test_emits_completed_assistant_text_and_ignores_other_nodes(self):
        from app.api.routes import _assistant_text_from_update

        self.assertEqual(
            _assistant_text_from_update({
                "assistant": {"messages": [AIMessage(content="پاسخ نهایی")]}
            }),
            ["پاسخ نهایی"],
        )
        self.assertEqual(
            _assistant_text_from_update({
                "tools": {"messages": [AIMessage(content="internal result")]}
            }),
            [],
        )

    def test_skips_tool_call_messages(self):
        from app.api.routes import _assistant_text_from_update

        message = AIMessage(
            content="",
            tool_calls=[{
                "name": "web_search",
                "args": {"query": "latest news"},
                "id": "call-stream-test",
                "type": "tool_call",
            }],
        )
        self.assertEqual(
            _assistant_text_from_update({"assistant": {"messages": [message]}}),
            [],
        )


    def test_skips_unparsed_tool_markup(self):
        from app.api.routes import _assistant_text_from_update

        opening = "<" + "tool_" + "call>"
        closing = "<" + "/tool_" + "call>"
        message = AIMessage(content=opening + "raw markup" + closing)
        self.assertEqual(
            _assistant_text_from_update({"assistant": {"messages": [message]}}),
            [],
        )
