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

## Current next step

Inspect the existing graph implementation and model factory, then design the smallest safe change to make model selection request-specific using Registry metadata and live Dynamo availability. Preserve the existing checkpointer and chat history. Do not approve/enable the model yet.
