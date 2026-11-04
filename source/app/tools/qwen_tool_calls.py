import html
import re
from uuid import uuid4

from langchain_core.messages import AIMessage


_TOOL_BLOCK = re.compile(
    r"<tool_call>\\s*<function=([A-Za-z_][A-Za-z0-9_.-]*)>\\s*(.*?)"
    r"\\s*</function>\\s*</tool_call>",
    re.DOTALL,
)
_PARAMETER = re.compile(
    r"<parameter=([A-Za-z_][A-Za-z0-9_.-]*)>(.*?)</parameter>",
    re.DOTALL,
)


def _parse_block(block_body: str, tool):
    fields = getattr(tool.args_schema, "model_fields", {})
    arguments = {}
    position = 0

    for match in _PARAMETER.finditer(block_body):
        if block_body[position:match.start()].strip():
            return None
        name = match.group(1)
        if name not in fields or name in arguments:
            return None
        value = html.unescape(match.group(2).strip())
        if "<parameter=" in value or "</parameter>" in value:
            return None
        arguments[name] = value
        position = match.end()

    if block_body[position:].strip() or not arguments:
        return None

    try:
        validated = tool.args_schema.model_validate(arguments)
    except (TypeError, ValueError):
        return None

    return validated.model_dump(mode="python")


def parse_qwen_tool_calls(message, tools):
    """Convert complete Qwen XML tool markup into validated LangChain tool calls."""
    if not isinstance(message, AIMessage) or not isinstance(message.content, str):
        return message
    content = message.content
    if "<tool_call>" not in content:
        return message

    tool_map = {tool.name: tool for tool in tools}
    parsed_calls = []
    position = 0

    for match in _TOOL_BLOCK.finditer(content):
        if content[position:match.start()].strip():
            return message
        tool_name = match.group(1)
        tool = tool_map.get(tool_name)
        if tool is None:
            return message
        arguments = _parse_block(match.group(2), tool)
        if arguments is None:
            return message
        parsed_calls.append(
            {
                "name": tool_name,
                "args": arguments,
                "id": f"call_{uuid4().hex}",
                "type": "tool_call",
            }
        )
        position = match.end()

    if not parsed_calls or content[position:].strip():
        return message

    return message.model_copy(
        update={
            "content": "",
            "tool_calls": parsed_calls,
            "invalid_tool_calls": [],
        }
    )
