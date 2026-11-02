# Current Status

Last verified: 2026-11-02

## Agent deployment

- langgraph-agent.service was restarted successfully after request-scoped routing changes.
- Service state after restart: active.
- GET /health returned HTTP 200 with {"status":"ok"}.
- The running API completed a real Persian text chat request with HTTP 200.
- The running API completed a real image-understanding request with HTTP 200 and correctly identified a generated red PNG as "Red".

## Registry

- PostgreSQL Registry connection verified.
- Registry tables remain separate from LangGraph Checkpointer tables.
- qwen38-vl is approved and enabled, with capabilities chat and vision.
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
  - GET /v1/models now returns only the logical Auto model without querying Dynamo.
- Open WebUI can use the stable logical model name Auto; actual model selection remains request-scoped inside LangGraph.
- The client-supplied model name does not bypass Registry eligibility.

## Verification performed

- python3 -m compileall -q app succeeded before the Auto model-list change.
- Imports of app.model_selector, app.graph.chat, and app.api.routes succeeded before the Auto model-list change.
- Router import exposed 2 routes.
- Direct selector test: chat → qwen38-vl; vision → qwen38-vl.
- Service restart completed before the Auto model-list change; health endpoint returned HTTP 200.
- Real non-streaming text chat returned HTTP 200 and the expected Persian response.
- Real image request returned HTTP 200 and correctly answered Red.
- The Auto model-list change is archived but has not yet been applied or verified on the host.

## Source snapshot status

- Exact current snapshots archived: source/app/model_selector.py, source/app/graph/chat.py, source/app/api/routes.py, and source/app/api/schemas.py.
- Other source files remain pending exact retrieval as listed in source/FILE_INVENTORY.md.

## Next actions

1. Apply the archived Auto model-list change to app/api/routes.py on the DGX Spark host.
2. Compile and verify GET /v1/models returns exactly one model with id Auto.
3. Restart langgraph-agent.service with explicit user approval, then verify health and Auto chat behavior.
4. Add focused tests for coding classification and no-eligible-model behavior.
5. Continue preserving conversation thread IDs and PostgreSQL Checkpointer data.
