# General Assistant Tool Calling and Response Quality

Last updated: 2026-11-04

## Target flow

`Open WebUI → LangGraph Agent → Dynamo model`

Within the Agent:

`assistant → conditional tool dispatch → ToolNode → assistant → final response`

The model does not execute Python or browse by printing code. It emits structured tool calls; LangGraph executes registered tools and returns their results to the model.

## Live web search

- `web_search`: SearXNG JSON Search API at the configured `SEARXNG_BASE_URL` (default `http://127.0.0.1:8888`).
- The tool returns actual result titles, URLs, snippets, engines, scores, and publication dates where available.
- No external API key is required.
- SearXNG must allow JSON output. Its `settings.yml` must include `json` in the enabled `search.formats` list (for example, `[html, json]`).
- Search errors, disabled JSON output, and invalid responses return an explicit tool error. The model must not describe a failed tool call as a successful search.
- Retrieved page content is untrusted data. It cannot override system instructions.
- Final answers should cite actual result URLs as Markdown links.

The Agent runs on the DGX host and defaults to the host-published SearXNG endpoint `http://127.0.0.1:8888`. Override it through the protected Agent environment if the network topology changes.

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
- Tool execution is bounded by LangGraph recursion limit 12.
- Existing Model Manager lease ownership and PostgreSQL checkpointer tables are not changed.
- These changes are GitHub-only until explicitly synchronized and deployed.
- Verify that SearXNG JSON output is enabled and reachable from the Agent host before declaring live web search operational.
- Verify Dynamo parser arguments and structured tool-call output before declaring tool calling operational.


## Reliability and answer grounding — 2026-11-04

The SearXNG tool returns a machine-readable `ok` flag and explicit error category. A successful response also includes `result_count`; zero results are not evidence. The tool validates the response shape, keeps only HTTP(S) result URLs, removes duplicate URLs, bounds snippet length, and uses bounded connection/request timeouts.

The General Assistant prompt requires live search for current/recent questions and explicit research requests. It must distinguish search errors and empty results from successful research, cite only URLs returned by SearXNG, and avoid claiming to have opened full pages when only snippets were retrieved. ToolNode converts execution exceptions into tool errors for the assistant to handle. These source changes are not deployed or runtime-verified.


## Deterministic graph testability — 2026-11-04

`build_chat_graph` accepts an optional model object for isolated tests. When supplied, that object is bound to the same registered tools and used for graph invocation; in production, when no model object is supplied, the graph constructs the request-selected Dynamo model from `model_id`. This prevents tests from accidentally making live inference calls.

`source/tests/test_chat_graph.py` exercises a complete structured tool cycle with a fake model and deterministic tool: model tool call → LangGraph ToolNode execution → ToolMessage returned to model → final assistant message. The test is committed but is not yet run against the DGX virtual environment. It does not establish compatibility with the live Qwen parser or SearXNG service.

`source/tests/test_web_search.py` adds deterministic tests for result URL filtering/deduplication, max-result bounds, JSON request mode, and malformed provider responses. These tests have been committed but not executed in the deployed environment.
