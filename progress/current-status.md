# Current Status

Last verified: 2026-11-02

## Agent deployment
- langgraph-agent.service is active after the approved restart.
- GET /health returned {"status":"ok"}.
- GET /v1/models returns exactly one logical model: Auto.
- A real non-streaming chat request with model=Auto returned the expected Persian response.
- Open WebUI was tested by the user and confirmed working with the Auto endpoint.

## Registry and runtime
- qwen38-vl is approved and enabled in Registry with capabilities chat and vision.
- The latest authenticated GET /admin/models returned qwen38-vl only, with approval_status=approved, is_enabled=true, and capabilities=[chat, vision].
- The latest Dynamo GET /v1/models returned qwen38-vl only.
- qwen-coder is not currently present in the Registry response or Dynamo runtime response.

## Dynamo worker selection — intentional operational state
- The Coder worker was intentionally taken out of the active deployment to free resources and bring up the Qwen 3.8-VL worker. This was a deliberate sequencing decision, not an unexpected failure.
- The current combined Compose status output shows etcd and NATS healthy/running, dynamo-frontend running on host port 8013, and dynamo-vllm-vision38 running.
- The active runtime model exposed by the frontend is qwen38-vl.
- Do not describe the absence of qwen-coder as an accidental outage. It is currently paused by design.
- The next test target is qwen38-vl for chat and vision. Coder testing requires a deliberate switch back to the Coder worker, after the Vision tests are complete.
- Do not start both heavy workers together unless the user explicitly approves and the memory/resource plan supports it.

## Request-scoped routing — implemented
- app/model_selector.py classifies requests as vision, coding, or chat.
- Selection requires Registry approval, enablement, live Dynamo discovery, and matching capability.
- app/graph/chat.py consumes the selected model ID from LangGraph RunnableConfig.
- app/api/routes.py selects a model per request and passes it to streaming and non-streaming graph execution.
- GET /v1/models exposes only the logical Auto model and does not query Dynamo.
- Client model naming does not bypass Registry eligibility.
- Existing LangGraph graph and PostgreSQL checkpointer are preserved.

## Verification performed
- Application compile passed after the Auto endpoint change.
- Direct ModelList test confirmed exactly one model with id Auto.
- Approved service restart completed; systemd reports active.
- GET /health returned {"status":"ok"}.
- GET /v1/models returned only Auto.
- Real text request through Auto returned the expected Persian response.
- Earlier real vision request through Auto returned HTTP success and identified a generated red PNG as Red.
- Direct selector checks previously resolved both chat and vision to qwen38-vl.

## Current deployment observation to reconcile
- The latest docker compose -f compose.yaml -f compose.vision.yaml ps output lists Compose services dynamo-frontend and dynamo-vllm-vision38.
- A subsequent grep of those named files showed service keys dynamo-vllm and dynamo-vllm-vision. These observations do not match and need reconciliation using the effective Compose configuration before any deployment edits.
- No Compose files were modified during this status check.

## Next actions
1. Reconcile the effective Compose configuration and document the exact Coder pause / Vision worker deployment definitions.
2. Complete focused qwen38-vl chat and vision tests through LangGraph Auto.
3. When Vision testing is complete, plan and obtain approval for switching the active heavy worker to qwen-coder.
4. Verify qwen-coder runtime discovery and Registry approval/capabilities before its tests.
5. Continue preserving conversation thread IDs and PostgreSQL Checkpointer data.

## Operational rules
- Do not stop, restart, rebuild, install, download, or activate services/models without explicit user approval.
- Keep this status, deployment documentation, source inventory, and changelog synchronized with verified changes.
- Never commit config/agent.env, credentials, API keys, database contents, or host backup bundles.
