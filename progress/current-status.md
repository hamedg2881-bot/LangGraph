# Current Status

Last verified: 2026-11-02

## Agent deployment
- langgraph-agent.service is active.
- GET /health returned {"status":"ok"}.
- GET /v1/models returns exactly one logical model: Auto.
- A real text request through Auto returned the expected Persian response.
- User confirmed Open WebUI works with Auto.

## Registry and runtime
- qwen38-vl is approved and enabled in Registry with chat and vision capabilities.
- Latest Dynamo GET /v1/models returned qwen38-vl only.
- qwen-coder is intentionally paused and is not currently present in Registry or Dynamo runtime.

## Dynamo worker selection
- Coder was intentionally taken out of the active deployment to free resources for Qwen 3.8-VL. This is deliberate sequencing, not an accidental outage.
- Current containers: dynamo-etcd, dynamo-nats, dynamo-frontend, dynamo-vllm-vision38.
- Frontend host port: 8013.
- Active served model: qwen38-vl.
- Heavy workers must remain sequential unless the user explicitly approves concurrent operation and a resource plan.

## Active Compose provenance and archived snapshots
- Container labels identify dynamo-frontend as project deploy/service dynamo-frontend, using compose.yaml + compose.vision38.yaml + compose.gateway.yaml.
- Container labels identify dynamo-vllm-vision38 as project deploy/service dynamo-vllm-vision38, using compose.yaml + compose.vision38.yaml.
- Exact retrieved contents of compose.vision38.yaml and compose.gateway.yaml are now archived at deployment/compose.vision38.yaml and deployment/compose.gateway.yaml.
- The exact base compose.yaml has not yet been retrieved or archived.
- compose.vision.yaml is not the overlay used by the active Vision38 worker. Its service list must not be treated as the active deployment.
- Vision38 definition mounts /opt/ai/models/Qwen3.8-27B-NVFP4 at /models/qwen38, serves qwen38-vl, max model length 32768, max sequences 2, batch tokens 4096, GPU memory utilization 0.35, FP8 KV cache, multimodal images limited to 2, videos disabled, shared memory 16 GB.
- Frontend definition serves Dynamo HTTP on container port 8000, published as host port 8013.
- No deployment configuration or running container was changed during this inspection.


## Multi-model management target — newly confirmed
- The desired operating model is multiple approved model choices with resource-aware residency, not manual one-model-at-a-time Compose switching.
- Model approval/availability in Registry must be independent of whether model weights are currently resident in memory.
- A Model Manager should load on demand, keep hot models resident within a safe memory budget, queue requests when needed, and unload only safely idle workers with no in-flight requests.
- Coder was intentionally paused earlier to free resources for Qwen 3.8-VL; that was an interim operational choice, not the desired permanent architecture.
- Long-term target: one shared Dynamo frontend/control plane with independently managed workers, subject to validation of Dynamo 1.6.1 lifecycle APIs.
- Exact base Compose file is now archived at deployment/compose.yaml (commit b9033286fef97f80d6e564acb668b5d4a984246a).
- The archived base Compose file defines a Coder worker that publishes host port 8013. The gateway overlay also publishes 8013; therefore the current definitions cannot simply be started together unchanged. This conflict must be resolved as part of the worker lifecycle redesign, not by starting the dormant service now.
- No host deployment or running service was modified in this documentation step.


## Request-scoped routing
- app/model_selector.py classifies requests as vision, coding, or chat.
- Selection requires Registry approval, enablement, live Dynamo discovery, and matching capability.
- app/graph/chat.py consumes the selected model ID from LangGraph RunnableConfig.
- app/api/routes.py selects a model per request and passes it to streaming and non-streaming graph execution.
- GET /v1/models exposes only logical Auto and does not query Dynamo.
- PostgreSQL Checkpointer and conversation thread IDs are preserved.

## Verification
- Application compile passed after Auto endpoint change.
- GET /health returned {"status":"ok"}; GET /v1/models returned only Auto.
- Real text request through Auto returned expected Persian response.
- Earlier real vision request through Auto identified a generated red PNG as Red.
- Direct selector checks previously resolved chat and vision to qwen38-vl.

## Next actions
1. Retrieve and archive the exact base compose.yaml.
2. Complete focused qwen38-vl chat and vision tests through LangGraph Auto.
3. After Vision tests, obtain explicit approval before switching the active heavy worker to qwen-coder.
4. Verify qwen-coder runtime discovery and Registry approval/capabilities before testing it.
5. Preserve conversation thread IDs and PostgreSQL Checkpointer data.

## Operational rules
- Do not stop, restart, rebuild, install, download, or activate services/models without explicit user approval.
- Keep status, deployment docs, source inventory, and changelog synchronized with verified changes.
- Never commit config/agent.env, credentials, API keys, database contents, or host backup bundles.


## 2026-11-03 — Existing Control Center verified

- `dgx-control-center.service` is active.
- systemd launches `/usr/bin/dotnet /opt/ai/control-center/publish/ControlCenter.dll` with working directory `/opt/ai/control-center/publish`.
- `GET /api/health` on port 5090 returned `{"status":"ok","application":"DGX Spark Control Center",...}`.
- `GET /api/profiles` shows legacy `coding` and `image` profiles. Their service definitions still reference `qwen-coder` and `qwen36-vl`, with health endpoints on ports 8010 and 8012.
- `GET /api/status` reports host resources and legacy service checks. The old model health URLs do not reflect the current Dynamo frontend on port 8013 and must not be used as authoritative model runtime status.
- Latest observed host resource snapshot: total 121.69 GiB, available 9.47 GiB, used 112.21 GiB; no model load was attempted.
- No Control Center files, service settings, containers, models, or host configuration were changed during this inspection.

## Corrected model-management goal

- Each model needs to be independently runnable within the shared architecture; simultaneous execution/residency of heavy models is not a requirement.
- LangGraph selects the best eligible model for each request.
- Dynamo remains the runtime/inference layer and manages worker execution.
- Registry represents model catalog, capabilities, approval, and enablement independently from current runtime residency.
- The existing Control Center is the management UI to extend; do not create a second dashboard or replace it.
- Next work: map existing Control Center endpoints/UI to LangGraph Registry and Dynamo runtime, then plan a minimal in-place extension.
