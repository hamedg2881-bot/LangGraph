# Current Status

Last verified: 2026-11-02

## Agent deployment

- langgraph-agent.service restarted successfully after request-scoped routing changes.
- Service state after restart: active.
- GET /health returned HTTP 200 with {"status":"ok"}.
- The running API completed a real Persian text chat request with HTTP 200.
- The running API completed a real image-understanding request with HTTP 200 and correctly identified a generated red PNG as "Red".

## Registry

- PostgreSQL Registry connection verified.
- Registry tables remain separate from LangGraph Checkpointer tables.
- qwen38-vl is now approved and enabled, with capabilities chat and vision.
- Runtime discovery from Dynamo returned qwen38-vl.
- No model download, installation, worker activation, or Dynamo configuration change was performed as part of Registry approval.

## Request-scoped routing — implemented and running

- Added app/model_selector.py:
  - Detects image input as vision.
  - Uses coding-related text signals for coding.
  - Uses chat as the fallback.
  - Queries Dynamo /models at request time.
  - Selects only a model that is approved, enabled, runtime-discoverable, and assigned the required capability.
- Updated app/graph/chat.py:
  - Reads model_id from LangGraph RunnableConfig.
  - Creates the Dynamo chat model for the selected request model.
  - Reuses the existing compiled graph and PostgreSQL checkpointer.
- Updated app/api/routes.py:
  - Selects the model before graph execution.
  - Returns HTTP 503 when no eligible model exists.
  - Passes the selected model ID alongside the existing thread_id.
  - Both streaming and non-streaming graph calls use the same runtime config.
- The client-supplied model name does not bypass Registry eligibility.
- /v1/models has not yet been changed to return only logical Auto; this remains a separate follow-up.

## Verification performed

- python3 -m compileall -q app succeeded.
- Imports of app.model_selector, app.graph.chat, and app.api.routes succeeded.
- Router import exposed 2 routes.
- Direct selector test: chat → qwen38-vl; vision → qwen38-vl.
- Service restart completed; service remained active and health endpoint returned HTTP 200.
- Real non-streaming text chat returned HTTP 200 and the expected Persian response.
- Real image request returned HTTP 200 and correctly answered Red.

## Source snapshot status

- Exact current snapshots archived: source/app/model_selector.py and source/app/graph/chat.py.
- The exact current app/api/routes.py source is running and tested, but its complete contents still need to be retrieved from the host before archiving a source snapshot.
- The patch artifact is not a substitute for a complete source snapshot.
- Other source files remain pending exact retrieval as listed in source/FILE_INVENTORY.md.

## Next actions

1. Retrieve and archive the exact current app/api/routes.py source.
2. Add focused tests for coding classification and no-eligible-model behavior.
3. Decide separately whether /v1/models should expose only Auto.
4. Continue preserving conversation thread IDs and PostgreSQL Checkpointer data.
