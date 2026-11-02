# Project Context

Last updated: 2026-11-02

## Project and host

- Project: LangGraph Agent
- Host: NVIDIA DGX Spark, hostname spark-7ea3
- OS: Ubuntu 26.04
- Project directory: /opt/ai/langgraph-agent
- Service: langgraph-agent.service
- Agent API: port 8100
- Current active model exposed by Dynamo: qwen38-vl (Qwen3.8-27B-NVFP4)
- PostgreSQL database: langgraph, schema public, user langgraph

## Agreed architecture

Open WebUI → LangGraph Agent → NVIDIA Dynamo → Model Workers

- Open WebUI will ultimately expose one logical model named Auto.
- LangGraph Agent classifies requests, selects a suitable model, manages conversation state, and coordinates tools.
- Model Registry stores model metadata, capabilities, and administrative approval/enablement.
- NVIDIA Dynamo owns model worker execution and runtime discovery.
- Registry must not download, install, load, or activate models.
- PostgreSQL and LangGraph Checkpointer data must be preserved.
- Code Intelligence on port 8200 and AstraMap API on port 8300 must be preserved.
- Control Center on port 5090 and its coding/image profiles must be preserved.
- Heavy model workers should not be run simultaneously unless explicitly planned.
- New models discovered from Dynamo enter the registry as pending and disabled.

## Registry policy

A model is selectable only when all conditions hold:
1. Approval status is approved.
2. Enablement is true.
3. The model is currently discoverable/available from Dynamo.
4. The model has the capability required by the request.

Approval, enablement, and runtime availability are separate concepts:
- Approval: pending, approved, rejected.
- Enablement: enabled/disabled.
- Runtime: determined live from Dynamo; do not treat a stale stored value as authoritative.

Dynamo synchronization:
- Insert newly discovered models as pending and disabled.
- For existing models, update discovery timestamps only.
- Never overwrite administrative decisions, capabilities, or curated model settings.
- Missing models are not deleted; they are treated as runtime-unavailable.
- Approval and enablement require authenticated admin endpoints.

## Admin API

- GET /admin/models
- POST /admin/models/sync
- POST /admin/models/{id}/approve
- POST /admin/models/{id}/reject
- PATCH /admin/models/{id}
- GET /admin/models/{id}/status
- POST /admin/models/{id}/enable
- POST /admin/models/{id}/disable

All admin routes require a separate ADMIN_API_KEY Bearer token. The key is stored only on the host in config/agent.env, protected by file mode 600. Never copy the real value into this repository or logs.

## Current implementation facts

- Registry tables use the model_registry_ prefix in the existing langgraph PostgreSQL database.
- Checkpointer tables are separate and must remain untouched.
- Psycopg 3 async pool is used for Registry access.
- Registry database is opened in FastAPI lifespan and attached to app.state.
- Registry schema initialization uses idempotent CREATE TABLE IF NOT EXISTS.
- The chat API now performs request-scoped model selection through the Registry and live Dynamo discovery.
- The graph reads the selected model ID from LangGraph RunnableConfig; the same compiled graph and PostgreSQL checkpointer are reused.
- /v1/models still exposes Dynamo model IDs; the planned Auto-only response has not yet been implemented.

## Request-scoped routing — implemented

- Classify requests as vision when image input is present, coding for code/programming requests, and chat as the fallback.
- Select only models that are approved, enabled, currently discoverable in Dynamo, and assigned the required capability.
- Ignore client-supplied model IDs for policy selection; they must not bypass Registry eligibility.
- Pass the selected model ID via LangGraph runtime configuration to both streaming and non-streaming graph execution.
- The currently approved/enabled model qwen38-vl has chat and vision capabilities.
- No coding capability has been assigned to qwen38-vl; coding requests will not select it until an administrator explicitly assigns that capability.
- Do not automatically assign capabilities or approve/enable discovered models.

## Verification on 2026-11-02

- Service restart succeeded; /health returned HTTP 200.
- Selector test chose qwen38-vl for both chat and vision.
- A real Persian text chat request completed successfully.
- A real image-understanding request completed successfully and identified the dominant color as red.
- The complete exact app/api/routes.py source must still be retrieved from the host before archiving.

## Important workflow constraints

- Work step by step; provide one command or one focused action at a time and wait for its output.
- User runs shell commands over SSH.
- Do not repeat already completed architecture investigations.
- No server changes, downloads, installations, service stops, or rebuilds without explicit approval.
- Preserve existing models, containers, databases, services, and project data.
- Never claim a change or test succeeded before its result is observed.
- Keep source/configuration snapshots in this repository synchronized after each project change.
