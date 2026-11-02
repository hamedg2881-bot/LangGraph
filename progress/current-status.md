# Current Status

Last verified: 2026-11-02

## Agent deployment

- `langgraph-agent.service` restarted successfully after Registry integration.
- PID observed after restart: `1299521`.
- Uvicorn listening on `0.0.0.0:8100`.
- Startup log: `Application startup complete`.
- `GET /health`: HTTP 200, `{"status":"ok"}`.
- `GET /admin/models` without credentials: HTTP 401.
- `GET /admin/models` with the host-stored admin key: HTTP 200.
- Admin key is loaded by application settings; observed length 64. Actual value is secret and is not recorded here.

## Registry

- PostgreSQL Registry connection verified.
- Three tables created and verified:
  - `model_registry_models`
  - `model_registry_capabilities`
  - `model_registry_approvals`
- Registry currently contains one discovered model:
  - ID: `qwen38-vl`
  - display name: `qwen38-vl`
  - provider: `nvidia`
  - context length: `32768`
  - approval: `pending`
  - enabled: `false`
  - capabilities: empty
- No approval or enablement action has been performed.
- Discovery sync previously registered this model from Dynamo.

## API behavior

- `/v1/models` still returns raw Dynamo model `qwen38-vl`; the planned `Auto` abstraction is not implemented yet.
- Admin authentication is working.
- Admin list response shape is `{"data": [...]}`.

## Existing chat implementation inspected from prior source excerpts

- `app/graph/chat.py` builds one compiled graph with one assistant node and currently captures a model created at graph construction.
- `app/providers/dynamo.py` exposes `create_chat_model(model: str | None = None)`.
- `app/api/routes.py` uses the same graph for streaming and non-streaming requests; the client model field is currently echoed and does not select the runtime model.
- Existing thread ID derivation and checkpointer must be preserved.
- Exact executable source snapshots are not yet committed in this repository; the prior inspection excerpts are the design reference, not a claim that the full source files are archived.

## Request routing design

- Classify image input as `vision`, code/programming requests as `coding`, and other requests as `chat`.
- Select only models that are approved, enabled, live-discoverable in Dynamo, and assigned the required capability.
- Pass the selected model ID via LangGraph runtime configuration for both `ainvoke` and `astream`.
- Reuse the existing compiled graph and PostgreSQL checkpointer.
- Do not trust the client-supplied model ID to bypass Registry policy.
- Keep `qwen38-vl` pending, disabled, and without capabilities until explicitly configured.

## Next action

Capture only the relevant source sections with a compact, line-limited command, then prepare exact GitHub source snapshots and the implementation patch. No server modification or service restart has been performed for this routing stage.
