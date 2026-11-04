# General Assistant Tool Calling and Response Quality

Last updated: 2026-11-04

## Target flow

`Open WebUI → LangGraph Agent → Dynamo model`

Within the Agent:

`assistant → conditional tool dispatch → ToolNode → assistant → final response`

The model does not execute Python or browse by printing code. It emits structured tool calls; LangGraph executes registered tools and returns their results to the model.

## Live web tools

- `web_search`: Tavily Search API; returns actual result titles, URLs, snippets, scores, and publication dates where available.
- `web_extract`: Tavily Extract API; retrieves readable Markdown from a public HTTPS URL.
- Both tools are registered only when `TAVILY_API_KEY` is configured.
- No API key is stored in source control. Add it only to the protected Agent environment.
- Search and extraction errors return explicit tool errors. The model must not describe a failed tool call as a successful search.
- Retrieved page content is untrusted data. It cannot override system instructions.
- Final answers should cite actual result URLs as Markdown links.

Without a configured key, the graph receives no web tools and its system prompt explicitly says live web search is unavailable. The model must not invent tool calls or claim browsing.

## Reasoning

`ENABLE_THINKING` defaults to true. This removes the previous unconditional `enable_thinking=false` override from every Dynamo request. It can be disabled through protected environment configuration if operationally necessary.

The Qwen3.8-VL Dynamo worker snapshot adds:
- `--dyn-tool-call-parser qwen3_coder`
- `--dyn-reasoning-parser qwen3`

These parser names match the Qwen3.5/Qwen3-Coder family in NVIDIA Dynamo's tool-call parsing guidance. The Compose update is a source snapshot only; the worker has not yet been recreated or verified.

## Conversation continuity

Open WebUI sends conversation history on each request. The Agent already persists conversation state using the PostgreSQL LangGraph checkpointer. Re-appending the entire transcript on every turn can duplicate prior messages.

The updated API:
- Reads the existing checkpoint for the conversation thread.
- On the first turn, initializes it from the incoming conversation messages.
- On subsequent turns, appends only the newest user message.
- Passes incoming system/developer instructions separately so they are not repeatedly persisted as conversation turns.

This first implementation assumes the same conversation thread is not reused for a divergent edited branch. Branch-edit/regeneration reconciliation is a separate follow-up.

## Safety and deployment

- No browser-facing raw execution endpoint is introduced.
- Web extraction accepts HTTPS URLs only and rejects obvious local/private host targets.
- Tool execution is bounded by LangGraph recursion limit 12.
- Existing Model Manager lease ownership and PostgreSQL checkpointer tables are not changed.
- These changes are GitHub-only until explicitly synchronized and deployed.
- Deployment requires a protected `TAVILY_API_KEY` value for live web access.
- Verify Dynamo parser arguments and structured tool-call output before declaring tool calling operational.
