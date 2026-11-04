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



## 2026-11-03 — Control Center source reviewed and archived

- Read the complete user-provided text snapshots for `Program.cs`, `HistoryBackgroundService.cs`, `index.html`, and `ControlCenter.csproj`.
- Copied the exact source snapshots into `source/control-center/`; original intake files remain under `archive/control-center/source/`.
- The implementation contains host resource/status APIs, 60-second history sampling, 30-day retention, a Persian RTL dashboard, and legacy profile switching.
- The legacy profile-switch API executes Docker/systemd start/stop commands directly and is not suitable as the model lifecycle manager because it does not coordinate request leases, draining, or queueing.
- The inspected source binds to `0.0.0.0:5090` and contains no application-level authentication/authorization middleware; the mutating profile-switch route therefore needs to be treated as a security issue before continued use.
- UI output escaping is inconsistent for service fields; harden rendering before adding more dynamic data.
- The UI text says read-only while a mutating profile-switch feature is present.
- No production source, service, deployment, container, or model state was changed. Only GitHub documentation/source snapshots were updated.

## 2026-11-03 — Control Center source integration prepared in GitHub

- Updated canonical `source/control-center/Program.cs`: added read-only `GET /api/ai-status` for LangGraph Agent (`LANGGRAPH_AGENT_URL`, default port 8100) and Dynamo (`DYNAMO_URL`, default port 8013); Agent model IDs are read from `/v1/models`.
- Disabled the legacy `POST /api/profile-switch` behavior. The route now returns HTTP 410 Gone and no longer executes Docker/systemd start/stop commands.
- Updated `source/control-center/wwwroot/index.html`: added Agent/Dynamo status cards, removed profile apply controls, retained legacy profile preview as read-only, and escaped dynamic service-card fields.
- `ControlCenter.csproj` and `HistoryBackgroundService.cs` remain unchanged.
- Updated deployment notes, source inventory, roadmap, and changelog.
- These changes exist in GitHub only. Host source, published DLL, and `dgx-control-center.service` have not been changed, built, published, or restarted.
- Before deployment, compare host source files with canonical GitHub content; then run the documented `dotnet publish` command only after explicit approval.


## 2026-11-03 — Vision request verified through logical Auto

- Sent a real multimodal request to `POST /v1/chat/completions` on the LangGraph Agent with `model=Auto`, Persian text, and a JPEG data URL encoded as Base64.
- The Agent returned HTTP success with a substantive Persian description of the document in the image; usage reported 1,586 prompt tokens and 1,445 completion tokens.
- Together with the previously verified Auto text request and Dynamo worker registration/routing logs for namespace `qwen38-vl`, this confirms the end-to-end Vision API path is operational.
- The response's OCR field values have not been independently checked against the source image; semantic plausibility is not proof of exact transcription.
- This was an API-level test. Image upload through the Open WebUI interface has not yet been separately verified in this test.


## 2026-11-03 — Agent Registry route inventory captured

The user supplied the host inspection output for `/opt/ai/langgraph-agent`. It confirms:

- Public routes: `GET /v1/models`, `POST /v1/chat/completions`, and `GET /health`.
- Admin router in `app/api/admin_routes.py`: `GET /admin/models`; `POST /admin/models/sync`; `POST /admin/models/{model_id}/approve`; `POST /admin/models/{model_id}/reject`; `PATCH /admin/models/{model_id}`; `POST /admin/models/{model_id}/enable`; `POST /admin/models/{model_id}/disable`; `GET /admin/models/{model_id}/status`.
- Related contract/schema files: `app/api/admin_auth.py`, `app/api/schemas.py`, and `app/registry/schema.sql`.
- No queue/request-status API was present in the inspected route inventory. Control Center must not show fabricated queue metrics or offer queue controls until a supported Agent/Model Manager API is implemented.
- The exact bodies of the admin route/schema files have not yet been archived as source snapshots. Their route inventory is recorded here; source snapshots must only be added after exact contents are obtained.

This output is now part of the canonical project record. Do not ask the user to repeat this route discovery.


## 2026-11-03 — Agent Registry source bodies captured

The user supplied complete host output for app/api/admin_routes.py, app/api/admin_auth.py, app/api/schemas.py, app/registry/repository.py, app/registry/database.py, and app/main.py.

- Archived exact snapshots: source/app/api/admin_routes.py, source/app/api/admin_auth.py, source/app/registry/repository.py, source/app/registry/database.py, and source/app/main.py.
- Verified the already archived source/app/api/schemas.py matches the supplied host output.
- Admin routes are protected at router level by Depends(require_admin). Authentication checks Bearer scheme and uses secrets.compare_digest; missing configuration returns 503 and invalid credentials return 401.
- GET /admin/models returns Registry rows including approval, enablement, metadata, timestamps, and capabilities.
- POST /admin/models/sync reads Dynamo's /models endpoint and calls sync_discovered_models. Repository upsert for existing IDs updates only last_seen_at and updated_at, preserving approval, enabled state, capabilities, and curated metadata.
- Approve/reject and enable/disable write Registry decisions and audit rows. PATCH can update display name, architecture, quantization, context length, and capabilities.
- Per-model status reports runtime available, unavailable, or unknown; selectable requires approved + enabled + available.
- app/main.py initializes Registry DB using the same PostgreSQL connection string as the LangGraph checkpointer, but a separate Registry pool; shutdown closes the Registry pool. Do not modify or reset checkpointer data.
- app/registry/schema.sql was not included in the supplied command output; its exact host body remains pending capture.
- No host files, services, containers, database rows, or model state were modified during this source archival step.


## 2026-11-03 — Control Center Registry/runtime redesign (GitHub source only)

- Replaced the old profile-manifest-driven `/api/status` with live checks for LangGraph Agent health and logical `/v1/models`, Dynamo frontend health and served-model discovery, fixed known Docker container states, and host resources.
- Dynamo discovery tries the frontend `/v1/models` route first and falls back to `/models`.
- Added read-only `GET /api/registry/models`, which proxies the Agent's authenticated Registry list server-to-server and enriches each row using the Agent's `/admin/models/{model_id}/status` contract. Runtime availability and `selectable` therefore come from the Agent/Dynamo check, not assumptions in the browser.
- `LANGGRAPH_ADMIN_API_KEY` is read from the Control Center process environment only. It is never sent to browser JavaScript or returned by the proxy. If absent, Registry endpoint returns 503.
- Replaced the old profile preview dashboard with Persian RTL Overview, Registry, Runtime/Workers, Resources/History, and Events sections. Removed all profile manifest UI and kept profile-switch as HTTP 410.
- Updated HistoryBackgroundService to record readiness transitions from the new runtime list.
- Registry writes (sync, approve/reject, enable/disable, metadata/capability changes) are intentionally not exposed yet: Control Center has no application-level admin session/authentication design, and exposing these routes anonymously would be unsafe. No queue or model lifecycle controls are shown.
- No host files, service environment, build/publish output, systemd service, containers, PostgreSQL data, or model state were modified. All changes above are committed in GitHub only; compilation and host API verification are pending.

### Immediate next steps
1. Review the new source for compile/runtime issues and verify the exact Dynamo frontend model-list path.
2. Design protected Control Center administrator authentication and server-side secret injection before adding Registry write operations.
3. After explicit approval, synchronize source to `/opt/ai/control-center`, build/publish, restart `dgx-control-center.service`, and verify health/status/Registry APIs.


## 2026-11-04 — Control Center deployment and live API verification

- User ran `dotnet build --no-restore` successfully after replacing the canonical Control Center `Program.cs` and `wwwroot/index.html` files from GitHub.
- User ran `dotnet publish -c Release -o /opt/ai/control-center/publish`; publish succeeded.
- With user execution, `dgx-control-center.service` was restarted and reported `active (running)`; `GET /api/health` returned status `ok`, application `DGX Spark Control Center`, version `2.0.0`.
- Verified API responses: `/api/status`, `/api/ai-status`, `/api/registry/models`, `/api/history`, and `/api/events` all returned parseable JSON. Registry returned 2 models; history returned 1,442 samples; events returned 100 records; runtime listed 9 containers.
- Latest `/api/status`: Agent health `ok`, Agent logical models [`Auto`]; Dynamo health `ok`, Dynamo models [`qwen-coder`, `qwen38-vl`].
- Latest `/api/ai-status`: Agent health and model status `ok`; Agent exposes only `Auto`. Dynamo health `ok`.
- Registry rows: `qwen38-vl` is approved/enabled/selectable with capabilities `chat, vision`, context 32768; `qwen-coder` is approved/enabled/selectable with capability `coding`, context 65536. Both report runtime_status `available`.
- Runtime container inventory: running — `dynamo-etcd`, `dynamo-frontend`, `dynamo-nats`, `dynamo-vllm-coder`, `dynamo-vllm-vision38`, `langgraph-postgres`, `open-webui`; exited — legacy `dynamo-vllm` and `dynamo-vllm-vision`. Discovery intentionally includes stopped containers.
- History event types in the returned 100-event window: 79 `service-readiness-changed`, 21 `runtime-readiness-changed`.
- Registry `last_seen_at` for both models remains 2026-11-03 while current Dynamo discovery sees both models on 2026-11-04. This suggests the explicit Agent Registry sync endpoint has not run since the previous day; it is not evidence of runtime failure. The sync operation must be checked before changing code.
- No additional model, worker, database, or Compose change was made during these read-only checks.


## 2026-11-04 — Control Center 2.0.0 deployment and Registry sync follow-up

- User successfully ran the Release publish and restarted `dgx-control-center.service`; the service is active and `GET /api/health` returns status `ok`, version `2.0.0`.
- All five API endpoints `/api/status`, `/api/ai-status`, `/api/registry/models`, `/api/history`, and `/api/events` returned parseable JSON.
- Latest live status: Agent health `ok`, logical model `Auto`; Dynamo health `ok`, runtime models `qwen-coder` and `qwen38-vl`.
- Registry contains two models. `qwen38-vl` is approved/enabled/selectable with `chat, vision` capabilities and context 32768; `qwen-coder` is approved/enabled/selectable with `coding` capability and context 65536.
- Runtime discovery reports 9 containers: 7 running and 2 exited legacy containers (`dynamo-vllm`, `dynamo-vllm-vision`). Discovery includes stopped containers intentionally.
- User executed authenticated `POST http://127.0.0.1:8100/admin/models/sync`; Agent returned `discovered_count: 2`. Registry `last_seen_at` for both models advanced to `2026-11-04T06:52:30.290923+00:00`; approval remained `approved`, runtime remained `available`.
- The current Agent still has no queue/request lease or Model Manager API. The current Control Center still has no admin-session authentication and exposes Registry as read-only. Do not add anonymous mutation proxies.
- The current Agent source snapshot in GitHub is incomplete for a safe implementation: settings/config package, graph/provider implementation, exact Registry schema file, and some runtime/config files are not all archived. Capture exact host source before modifying production Agent files.
- Dynamo 1.6.1 documentation describes discovery and Planner control signals; the Operator reconciles desired worker counts in Kubernetes. This does not establish a supported bare-metal load/unload HTTP API for this Docker Compose deployment. Worker lifecycle adapter remains a hard implementation gate.
- A unified implementation contract was added at `architecture/model-management.md`. It defines manual metadata-only registration, durable queue/leases, resource admission, drain-first eviction, lifecycle adapter validation, Control Center admin security, monitoring, tests, and deployment gates.
- No host source, Agent service, database schema/data, worker/container, model, or Control Center runtime was changed during this documentation update.


## 2026-11-04 — Agent Model Manager implementation committed to GitHub (not deployed)

The user supplied the exact live host contents of `app/config/settings.py`, `app/providers/dynamo.py`, and `app/registry/schema.sql`. These three files are now archived byte-for-byte in `source/app/`; no environment file or secret was read or committed.

GitHub-only implementation added:
- Manual metadata-only model registration at authenticated `POST /admin/models`. New records are always `pending` and disabled; duplicate IDs return conflict. Registration does not download, install, load, or activate a model.
- Additive PostgreSQL tables `model_runtime_requests` and `model_runtime_leases` in `source/app/registry/schema.sql`; existing Registry and LangGraph checkpointer tables are not altered.
- Durable per-model FIFO admission with PostgreSQL advisory transaction locks, renewable leases, heartbeat, queue timeout, completion/failure/cancellation states, stale lease recovery, and active/queued snapshots.
- Chat and streaming requests acquire a lease before inference and retain it for the graph execution/stream. Queued requests can be cancelled; running requests are not force-cancelled.
- Authenticated Model Manager status/queue endpoints. Load/unload endpoints explicitly return HTTP 501 because graceful worker lifecycle control has not been validated for this bare-metal Dynamo 1.6.1 Compose deployment. No Docker stop/start behavior is implemented.
- Configurable `MODEL_MAX_ACTIVE_PER_MODEL` and `MODEL_QUEUE_TIMEOUT` settings; default per-model concurrency is 8, matching the known worker sequence ceiling but still requiring live-load validation.

Important limitations / gates:
- These source changes are committed to GitHub only. They have not been syntax-checked, tested against PostgreSQL, load-tested, synchronized to the host, or deployed. The next Agent startup would execute the additive schema statements through the existing Registry initializer; do not restart before review and explicit approval.
- Automatic model loading/unloading, resource-based admission, GPU memory accounting, worker desired/observed state reconciliation, and safe drain are not implemented. The API reports lifecycle unsupported rather than fabricating success.
- Control Center Registry mutation UI remains unavailable because it has no administrator session authentication. Do not expose manual registration or mutations through anonymous browser routes.
- No host files, database rows, services, containers, or model runtime state were changed by these GitHub commits.
- Queue admission now has a configurable per-model pending-queue ceiling (`MODEL_MAX_QUEUE_SIZE`, default 1000); a full queue returns HTTP 429 for non-streaming requests and an SSE rate-limit error for streaming requests.
- Admin cancellation now marks only queued requests; the waiting chat caller detects cancellation promptly. Running inference remains untouched. This behavior is source-committed but not yet integration-tested.


## 2026-11-04 — Model Manager safety correction (GitHub only)

- Added explicit Python package initializers. app.config exports Settings/get_settings; app.graph exports build_chat_graph, matching imports in app/main.py.
- Reworked Model Manager admission so expired lease timestamps never release execution capacity. Admission counts every retained lease and also counts orphaned running rows that have no lease; an expired lease is reported as unreconciled rather than reclaimed.
- A successful graph execution marks the request completed and releases its lease in one PostgreSQL transaction. If the request coroutine fails or is cancelled, the request moves to reconciliation_required and its lease remains held. This is intentionally fail-closed because API cancellation, client disconnect, or a transport error does not prove remote Dynamo inference stopped.
- Heartbeat database errors now trigger bounded exponential retry while the invocation coroutine remains alive. Lease expiry is telemetry, not permission to admit another request.
- Queue claiming now uses the per-model advisory transaction lock with a blocking row lock, avoiding SKIP LOCKED overtaking the oldest eligible request under contention.
- Added the reconciliation_required request state through an idempotent schema constraint update. Streaming queue timeouts now return a specific SSE service_unavailable error rather than the generic streaming failure.
- Important operational limitation: no automatic reconciliation/release endpoint has been added. A retained lease can keep a model's admission slot blocked until runtime termination is independently verified and a controlled reconciliation procedure is implemented. Do not manually delete leases merely because their timestamp expired.
- GitHub source only. No host files, PostgreSQL schema/data, Agent service, Dynamo worker, container, or model was changed. No deployment/restart was performed.
- Verification so far is source review and GitHub read-back only. Python syntax/import checks, schema migration against a disposable PostgreSQL database, queue concurrency tests, cancellation/disconnect tests, and Dynamo cancellation behavior remain required before deployment.


## 2026-11-04 — Model Manager cancellation ownership

- Disposable PostgreSQL tests passed for migration/idempotency, FIFO, priority, queue limits/timeouts, failure/cancellation lease retention, concurrent claims, independent Manager ownership, expired-lease capacity protection, and foreign Finish/Reconciliation rejection.
- A two-Manager test exposed that cancel_request() allowed a foreign Manager to cancel a queued request. The canonical GitHub source now adds an owner predicate to this update.
- The fix is not yet regression-tested or deployed. The failed test's finally block removed its disposable request and Registry row. No production database, host source, service, container, or model was changed.


## 2026-11-04 — General Assistant quality and tool-calling review

Source review of the canonical Agent snapshot found that the graph had only one assistant node and called Dynamo directly; there was no ToolNode or tool execution loop. The API also passed the complete Open WebUI message history into a persistent LangGraph thread on every turn, risking duplicate history because the PostgreSQL checkpointer already retained prior messages.

GitHub-only changes now:
- Added an actual LangGraph assistant → ToolNode → assistant cycle.
- Added optional Tavily live search and page extraction tools. They are exposed to the model only when TAVILY_API_KEY is configured. Without the key, the system prompt explicitly prohibits claiming live web access or printing pseudo-tool code.
- Added source-link requirements and untrusted-page instruction handling to the system prompt.
- Enabled Qwen reasoning by default through ENABLE_THINKING (configurable).
- Updated the active Qwen3.8-VL Compose snapshot with Dynamo's qwen3_coder tool parser and qwen3 reasoning parser, matching the Qwen3.5/Qwen3.8 parser family documented by NVIDIA.
- Changed request handling to use the persisted conversation state plus only the latest incoming user message after the first turn, avoiding repeated submission of the full Open WebUI transcript. Incoming system/developer instructions are passed separately to the graph.

Deployment gates:
- All changes are in GitHub only. They have not been copied to the host, installed, tested against the active Dynamo 1.6.1 image, or deployed.
- Live web search remains unavailable until a Tavily API key is configured securely in the host's Agent environment. Never commit or paste the key into GitHub.
- The Vision38 worker must be recreated with the updated Compose arguments before Qwen3.8 tool calls and reasoning parsing can work. This is not yet performed.
- The Agent's streaming/non-streaming tool cycle, checkpoint continuity, model tool-call parsing, and end-to-end search must be verified after deployment.
- Existing PostgreSQL checkpointer data and Model Manager tables must be preserved; no database reset or migration is part of this change.


## 2026-11-04 — Switch live web search provider to SearXNG

- User selected the already deployed SearXNG instance instead of Tavily.
- Agent configuration now uses `SEARXNG_BASE_URL`, defaulting to host-local `http://127.0.0.1:8888`; no API key is required.
- Replaced the Tavily search/extract implementation with a SearXNG `/search` JSON API tool. SearXNG provides search results/snippets; Tavily-specific page extraction has been removed.
- The Agent still uses the LangGraph ToolNode execution cycle and must cite actual URLs returned by search.
- SearXNG JSON output must be enabled in its settings (`search.formats` includes `json`). This has not yet been checked on the host.
- All changes are GitHub-only. No Agent environment, host source, SearXNG configuration, container, service, or database was changed or restarted.
- Runtime verification of SearXNG JSON output, Agent tool execution, Dynamo tool-call parsing, and end-to-end Persian search remains pending.
