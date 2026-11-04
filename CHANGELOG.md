# Change Log

## 2026-11-02 — Initial repository documentation
- Created project notebook structure for LangGraph Agent on DGX Spark.
- Recorded architecture, confirmed decisions, current status, and roadmap.
- Added sanitized Registry schema and deployment environment template.
- Recorded successful Registry startup, admin authentication, and health checks.
- No production host files or secrets were changed by this documentation commit.

## 2026-11-02 — Request-scoped model routing
- Implemented per-request capability classification for vision, coding, and chat.
- Added eligibility checks for Registry approval, enablement, live Dynamo discovery, and capability match.
- Updated LangGraph chat invocation to use the selected model ID through RunnableConfig.
- Preserved the existing graph, PostgreSQL checkpointer, and conversation thread IDs.
- Verified real text and image requests through the agent.

## 2026-11-02 — Logical Auto endpoint
- Updated GET /v1/models to return only the logical model Auto, independent of Dynamo availability.
- Kept actual runtime selection in the LangGraph request path.
- Applied the change on the host, compiled the application, and verified GET /v1/models returns only Auto.
- Restarted langgraph-agent.service with user approval; health returned HTTP 200.
- Verified a real chat request through model=Auto.
- User tested Open WebUI and confirmed the Auto integration works.

## 2026-11-02 — Intentional Coder pause for Vision worker
- Coder was intentionally paused to free resources for the Qwen 3.8-VL worker; this is planned sequencing, not an unexpected failure.
- Latest Dynamo runtime and Registry responses expose qwen38-vl only; it is approved, enabled, and has chat and vision capabilities.

## 2026-11-02 — Active Compose provenance and snapshots
- Container labels identify the frontend Compose files as compose.yaml, compose.vision38.yaml, and compose.gateway.yaml.
- Container labels identify the Vision38 worker Compose files as compose.yaml and compose.vision38.yaml.
- Archived the exact retrieved compose.vision38.yaml and compose.gateway.yaml contents under deployment/.
- Updated the source inventory and operational status to identify the still-unarchived base compose.yaml.
- Confirmed compose.vision.yaml is not the active Vision38 overlay.
- No running service or deployment configuration was changed.

## 2026-11-02 — Multi-model resource-aware residency direction
- User clarified the target is multiple available models with automatic memory-aware residency and switching, not permanent manual switching between Coder and Vision.
- Recorded the Model Manager direction: on-demand loading, bounded resident set, active-request protection, safe idle eviction, request queueing, memory reserve, and load/unload hysteresis.
- Archived the exact base compose.yaml as deployment/compose.yaml.
- Noted a host-port collision in the current definitions: the base Coder service and gateway both publish host port 8013. Do not start the dormant Coder service unchanged alongside the gateway.
- No runtime services or host configuration were changed.


## 2026-11-03 — Control Center baseline and corrected model goal
- Confirmed the existing `dgx-control-center.service` is active and its health API responds successfully on port 5090.
- Recorded the actual published assembly path and working directory.
- Inspected existing profile/status APIs; identified legacy qwen-coder/qwen36-vl profile entries and old health ports 8010/8012.
- Recorded that the existing Control Center must be extended in place; no replacement UI is to be created.
- Corrected the model-management requirement: models must be independently runnable and selected by LangGraph; simultaneous execution of heavy models is not required.
- No production files, services, containers, or model runtime state were changed.


## 2026-11-03 — Control Center source reviewed and organized
- Retrieved the user's uploaded UTF-8 source snapshots for Program.cs, HistoryBackgroundService.cs, index.html, and ControlCenter.csproj.
- Copied the exact snapshots into the canonical editable tree under source/control-center/ while retaining archive/control-center/source/ as the original intake archive.
- Reviewed existing API behavior, history sampling, dashboard UI, and legacy profile switching.
- Documented stale profile-based model control, missing application-level authentication on the mutating route, inconsistent UI output escaping, and the read-only-label mismatch.
- No host source, published assembly, running service, container, or model runtime was changed.

## 2026-11-03 — Control Center read-only Agent/Dynamo integration
- Added `GET /api/ai-status` to report LangGraph Agent health and model IDs from `/v1/models`, plus shared Dynamo frontend health.
- Added a Persian RTL dashboard panel for Agent and Dynamo status.
- Disabled legacy `POST /api/profile-switch` with HTTP 410; removed profile-apply UI so Control Center cannot directly stop/start Docker or systemd model services.
- Retained the old profile preview as informational/read-only and escaped dynamic service-card values.
- Updated deployment instructions, source inventory, current status, and roadmap.
- Source changes are committed in GitHub only; no host files, build output, systemd service, containers, or model runtime were changed.

## 2026-11-03 — Auto Vision API end-to-end test

- Sent a JPEG image as a Base64 data URL with a Persian prompt to the LangGraph Agent's OpenAI-compatible chat completions endpoint using logical model `Auto`.
- Received a successful completion with a detailed Persian description of the document; reported usage was 1,586 prompt tokens and 1,445 completion tokens.
- This verifies the Agent's multimodal request path to the Vision-capable runtime at API level, following successful Dynamo registration and Auto text-chat verification.
- OCR accuracy has not been independently validated against the source image, and the Open WebUI image-upload path remains a separate UI-level test.
- No model, container, service, or deployment configuration was changed by this test.


## 2026-11-03 — Agent Registry contract inventory captured for Control Center redesign
- Recorded the exact Agent admin route inventory from the user's host inspection output: list, sync, approve/reject, patch, enable/disable, and per-model status.
- Recorded that public `/v1/models` is distinct from the admin Registry and exposes logical `Auto`.
- Confirmed the inspected Agent route inventory contains no queue/request-status API; queue metrics and controls must not be fabricated in the dashboard.
- Marked exact admin route/auth/schema source snapshots as pending until their full contents are captured; no source code or schema was invented.
- Reaffirmed that the existing Control Center is to be modernized in place and legacy profile semantics are obsolete.
- Documentation-only update; no DGX host files, services, containers, databases, or models were changed.


## 2026-11-03 — Agent Registry source snapshots archived

- Archived exact user-supplied host source for Agent admin routes, Bearer auth, Registry repository, Registry database pool, and FastAPI startup/lifespan.
- Verified the existing archived Pydantic schemas match the newly supplied host output.
- Confirmed router-wide admin auth, constant-time Bearer token comparison, Dynamo-backed discovery sync, decision/audit writes, metadata/capability patching, and live per-model availability/selectability semantics.
- Documented API validation caveats and the absence of queue or worker lifecycle endpoints.
- Updated source inventory, current status, and Control Center integration contract.
- Documentation/source archival only: no DGX host files, running services, databases, containers, or models were changed. No secrets were committed.


## 2026-11-03 — Control Center Registry/runtime redesign (source-only)

- Replaced profile-manifest status with live LangGraph Agent, Dynamo frontend/model discovery, known Docker runtime states, and host telemetry.
- Added a server-side read-only Agent Registry proxy enriched with per-model runtime availability and selectability.
- Kept the Agent admin key server-side via process environment; no browser exposure or committed secret values.
- Rebuilt the Persian RTL UI around Overview, Model Registry, Runtime/Workers, Resources/History, and Events; removed obsolete profile preview.
- Updated resource history sampling to track runtime readiness transitions.
- Intentionally withheld Registry mutation routes pending Control Center administrator authentication. Retained HTTP 410 for legacy profile switching and did not add worker lifecycle/queue controls.
- GitHub source changes only; no host files, service environment, build, publish, restart, containers, database, or models were changed. Build/runtime verification remains pending.


## 2026-11-04 — Control Center deployed and verified on DGX Spark

- User successfully built and published the updated .NET 10 Control Center, then restarted `dgx-control-center.service`.
- Service is active; `GET /api/health` returned `ok` with application version `2.0.0`.
- Verified parseable responses from status, AI status, Registry, history, and events APIs.
- Agent exposes logical `Auto`; Dynamo discovers `qwen-coder` and `qwen38-vl`.
- Registry reports both models approved, enabled, runtime-available, and selectable; capabilities are coding for Coder and chat/vision for Vision38.
- Runtime discovery reports seven running containers and two exited legacy containers.
- Noted stale Registry `last_seen_at` timestamps (2026-11-03) despite current Dynamo discovery; investigate explicit Registry sync before any source changes.
- No model lifecycle, Compose, or database mutation was performed by the verification tests.


## 2026-11-04 — Unified model management architecture recorded

- Recorded the latest verified Control Center 2.0.0 deployment and successful explicit Agent Registry synchronization (2 discovered models; both timestamps refreshed).
- Added the integrated design contract for Registry manual metadata registration, durable request queue/leases, resource-aware model residency, safe drain-first eviction, Runtime Management, and measured Monitoring.
- Documented the hard gate for validating a supported Dynamo 1.6.1 bare-metal worker lifecycle adapter; Kubernetes Operator behavior is not assumed to be available in the current Docker Compose deployment.
- Recorded the Control Center admin-authentication requirement before exposing mutating endpoints.
- Updated decisions, current status, roadmap, README, and source inventory.
- Documentation-only GitHub update. No host source, database, services, containers, models, or runtime configuration were changed. No secrets were committed.


## 2026-11-04 — Agent Model Manager and manual Registry source implementation (GitHub only)

- Captured the exact host versions of Agent settings, Dynamo provider, and Registry schema into the canonical source tree; no secrets or `agent.env` content was accessed.
- Added manual metadata-only Registry registration with pending approval and disabled state by default.
- Added additive PostgreSQL queue/request and renewable lease tables.
- Added durable per-model FIFO admission, lease heartbeat/recovery, queue timeout, completion/failure/cancellation tracking, and queue snapshots.
- Integrated request leases around non-streaming and streaming graph inference; running requests are never forcibly cancelled.
- Added authenticated Model Manager status/queue/cancel endpoints. Load/unload endpoints explicitly return HTTP 501 until a supported graceful Dynamo 1.6.1 Compose lifecycle mechanism is validated.
- Updated source inventory, current status, and roadmap.
- All changes are committed to GitHub only. They have not been compiled, tested against the host database, deployed, or restarted. No host or runtime state was changed.
- Added configurable per-model queue backpressure; full queues return HTTP 429 or an SSE rate-limit error without starting inference.
- Admin cancellation now marks only queued requests; the waiting chat caller detects cancellation promptly. Running inference remains untouched. This behavior is source-committed but not yet integration-tested.


## 2026-11-04 — Model Manager lease safety and package correction (GitHub only)

- Added all six explicit __init__.py package files; the config and graph packages export the symbols imported by Agent startup.
- Removed expired-lease deletion and automatic failure/reclaim behavior. Admission now counts retained leases regardless of expiry and fails closed on running requests with missing leases.
- Added reconciliation_required for failed/cancelled invocations whose remote inference termination cannot be verified; these requests retain capacity leases.
- Heartbeat retries transient database failures with bounded backoff; it does not convert a missed heartbeat into proof that inference stopped.
- Replaced FOR UPDATE SKIP LOCKED with a row lock under the per-model advisory lock to preserve queue ordering.
- Added an SSE-specific queue-timeout error.
- Source changes are committed to GitHub only. No host, database, service, worker, or model state was modified. Deployment remains blocked on syntax/import validation, PostgreSQL migration tests, concurrency/stream cancellation tests, and a safe runtime reconciliation procedure.


## 2026-11-04 — Model Manager cancellation ownership fix (GitHub only)

- A PostgreSQL integration test with two independent ModelManager instances demonstrated that the original cancel_request() could cancel another manager's queued request because its UPDATE lacked an owner predicate.
- Updated cancel_request() to require both request ID and the calling manager's owner, matching the ownership boundary already enforced by cancel_queued().
- The cross-manager cancellation test exposed the issue on the disposable langgraph_migration_test database. Its finally cleanup removed the test request and model; no production database or service was touched.
- The source fix is committed to GitHub only. It has not yet been fetched into the review workspace, regression-tested, synchronized to the host, or deployed.


## 2026-11-04

### Product direction — high-quality all-purpose General Assistant

- Added `architecture/assistant-quality.md` as the governing product and acceptance contract.
- Recorded that the primary goal is a complete, versatile, high-quality chat experience through one central General Assistant and logical Auto model.
- Documented quality requirements for intent understanding, reasoning, conversation continuity, real tool execution, SearXNG web research, vision, document/file analysis, coding/workspace, image-generation workflows, Persian RTL, routing, safety, and end-to-end acceptance.
- Updated architecture overview, confirmed decisions, roadmap, current status, README links, and source inventory.
- Documentation and GitHub only; no host deployment, service restart, worker/model change, or database operation was performed.


## 2026-11-04 — General Assistant tool orchestration hardening (GitHub only)

- Improved the General Assistant system prompt for task completion, multilingual/Persian RTL behavior, safe defaults, multi-step work, truthful action reporting, and transparent failure handling.
- Strengthened web-search usage requirements for current/recent questions and explicit research requests; responses must rely on actual returned URLs and distinguish search errors from successful evidence.
- Hardened SearXNG integration with bounded timeouts, explicit error categories, response validation, HTTP(S)-only URL filtering, deduplication, bounded snippets, and result counts.
- Kept structured LangGraph tool execution and enabled ToolNode error handling.
- Updated source inventory, tool-calling architecture, current status, and roadmap.
- GitHub-only source/documentation changes. No host deployment, service restart, SearXNG configuration, database, worker, or model changes were performed. Runtime verification remains pending.
