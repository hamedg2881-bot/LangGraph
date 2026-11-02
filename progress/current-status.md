# Current Status

Last verified: 2026-11-02

## Agent deployment
- langgraph-agent.service is active after the approved restart.
- GET /health returned {"status":"ok"}.
- GET /v1/models returns exactly one logical model: Auto.
- A real non-streaming chat request with model=Auto returned the expected Persian response.
- User tested Open WebUI and confirmed the Auto integration works.

## Registry and runtime
- qwen38-vl is approved and enabled in Registry with capabilities chat and vision.
- Latest authenticated GET /admin/models returned qwen38-vl only, approved, enabled, capabilities chat and vision.
- Latest Dynamo GET /v1/models returned qwen38-vl only.
- qwen-coder is not currently present in Registry response or Dynamo runtime response.

## Dynamo worker selection — intentional operational state
- The Coder worker was intentionally taken out of the active deployment to free resources for the Qwen 3.8-VL worker. This is a planned sequencing decision, not an unexpected failure.
- Latest Compose status: etcd and NATS running; dynamo-frontend running on host port 8013; dynamo-vllm-vision38 running.
- Active runtime model exposed by the frontend is qwen38-vl.
- Coder remains intentionally paused until Vision tests are complete. Do not start both heavy workers together without explicit approval and a verified resource plan.

## Actual Compose provenance — verified from container labels
- dynamo-frontend labels identify project=deploy, service=dynamo-frontend, working_dir=/opt/ai/dynamo/deploy, config files:
  /opt/ai/dynamo/deploy/compose.yaml
  /opt/ai/dynamo/deploy/compose.vision38.yaml
  /opt/ai/dynamo/deploy/compose.gateway.yaml
- dynamo-vllm-vision38 labels identify project=deploy, service=dynamo-vllm-vision38, working_dir=/opt/ai/dynamo/deploy, config files:
  /opt/ai/dynamo/deploy/compose.yaml
  /opt/ai/dynamo/deploy/compose.vision38.yaml
- Therefore the earlier comparison against compose.vision.yaml was the wrong Compose overlay for the currently running Vision38 deployment. The effective Compose files must be inspected using the exact label paths before any edits.
- The effective service list from compose.yaml + compose.vision.yaml (etcd, nats, dynamo-vllm, dynamo-vllm-vision) does not describe the running deployment; it is not the active Vision38 stack.
- No Compose files or containers were changed during this inspection.

## Request-scoped routing
- app/model_selector.py classifies requests as vision, coding, or chat.
- Selection requires Registry approval, enablement, live Dynamo discovery, and matching capability.
- app/graph/chat.py consumes the selected model ID from LangGraph RunnableConfig.
- app/api/routes.py selects a model per request and passes it to streaming and non-streaming graph execution.
- GET /v1/models exposes only logical Auto and does not query Dynamo.
- Existing LangGraph graph and PostgreSQL checkpointer are preserved.

## Verification
- Application compile passed after Auto endpoint change.
- Direct ModelList test confirmed exactly one model with id Auto.
- Approved service restart completed; systemd reports active.
- GET /health returned {"status":"ok"}; GET /v1/models returned only Auto.
- Real text request through Auto returned expected Persian response.
- Earlier real vision request through Auto identified a generated red PNG as Red.
- Direct selector checks previously resolved chat and vision to qwen38-vl.

## Next actions
1. Inspect exact active Compose files compose.yaml, compose.vision38.yaml, and compose.gateway.yaml; archive exact deployment definitions in GitHub after retrieval.
2. Complete focused qwen38-vl chat and vision tests through LangGraph Auto.
3. After Vision tests, plan and obtain approval for switching the active heavy worker to qwen-coder.
4. Verify qwen-coder runtime discovery and Registry approval/capabilities before its tests.
5. Preserve conversation thread IDs and PostgreSQL Checkpointer data.

## Operational rules
- Do not stop, restart, rebuild, install, download, or activate services/models without explicit user approval.
- Keep status, deployment docs, source inventory, and changelog synchronized with verified changes.
- Never commit config/agent.env, credentials, API keys, database contents, or host backup bundles.
