# Roadmap

## Completed
- [x] Back up the relevant existing Agent application/config files before Registry work.
- [x] Create Registry SQL schema and tables in existing PostgreSQL database.
- [x] Implement async Registry database pool and repository.
- [x] Add separate secret admin key setting and Bearer authentication.
- [x] Implement admin model list, sync, approve/reject, update, enable/disable, and status endpoints.
- [x] Discover and register `qwen38-vl` as pending/disabled.
- [x] Compile/import checks passed.
- [x] Restart Agent and verify startup.
- [x] Verify health endpoint and unauthenticated admin rejection.
- [x] Verify authenticated admin list returns HTTP 200.
- [x] Inspect existing chat graph, Dynamo model factory, and API routing behavior from the previously supplied source excerpts.
- [x] Define request-scoped model routing design while preserving the compiled graph and checkpointer.

## In progress
- [ ] Capture exact source snapshots for graph, API routes, Dynamo provider, and Registry repository in GitHub.
- [x] Prepare a request-scoped routing patch in `patches/request-scoped-routing.patch` (not yet applied or tested on the host).
- [ ] Implement capability classification and Registry/Dynamo candidate selection.
- [ ] Pass selected model ID through LangGraph runtime config for both streaming and non-streaming requests.
- [ ] Test routing and conversation continuity without changing model approval state.
- [ ] Expose only `Auto` from `/v1/models` after routing is verified.

## Later
- [ ] Define and assign verified capabilities to each model.
- [ ] Admin approval and enablement workflow, only after user decision.
- [ ] Test coding and tool-use routes with eligible workers. Text and Vision through Auto have passed API-level tests (2026-11-03).
- [ ] Improve runtime health checks beyond Dynamo model-list presence.
- [ ] Add operational/admin documentation and automated tests.

## Multi-model Model Manager — new priority
- [ ] Archive and review the exact active base Compose definition and all active overlays.
- [ ] Inspect Dynamo 1.6.1 worker lifecycle APIs and examples for independently starting/stopping workers registered to one shared frontend.
- [ ] Define model lifecycle states and Registry fields separately from approval/enabled status.
- [ ] Define resource telemetry: unified-memory free/used, per-worker resident footprint, KV-cache use, active sequences, load peak, and safe-idle state.
- [ ] Define configurable memory reserve, per-model load estimates, queue policy, eviction scoring, hysteresis, and cooldown.
- [ ] Implement a Model Manager service and a narrow Dynamo lifecycle adapter; do not use Compose edits as per-request scheduling.
- [ ] Add concurrency protection so duplicate requests do not trigger duplicate model loads.
- [ ] Add request leases/reference counts so no worker is unloaded while serving a request.
- [ ] Test load, reuse, queue, safe unload, reload, and failure recovery with Coder and Vision sequentially before allowing concurrent residency.
- [ ] Preserve Registry approvals and PostgreSQL conversation/checkpointer data across worker lifecycle transitions.



## Existing Control Center integration

- [x] Verify existing `dgx-control-center.service` is active.
- [x] Verify published application path and systemd working directory.
- [x] Verify Control Center health endpoint on port 5090.
- [x] Identify legacy profile model names and stale health endpoints (8010/8012).
- [x] Inspect existing Control Center source/UI and API implementation before editing.
- [x] Define and implement the first read-only in-place integration with LangGraph Agent and Dynamo health/model-list endpoints.
- [ ] Complete Registry approval/capability integration; current first phase displays Agent logical model IDs and Dynamo health.
- [ ] Verify model catalog, approval/capability state, runtime readiness, and resource status in the existing UI.


### Control Center source review — 2026-11-03

- [x] Retrieve and inspect the complete existing Control Center source/UI snapshot.
- [x] Preserve the original intake archive and create canonical editable snapshots under `source/control-center/`.
- [ ] Confirm that the archived source snapshot matches the current host working-tree files before any deployment.
- [ ] Design a minimal in-place read-only integration with Registry, Agent, and Dynamo status.
- [x] Disable legacy profile mutation (HTTP 410); no lifecycle controls are exposed.
- [ ] Replace direct Docker/systemd profile switching with a safe Model Manager lifecycle API after Dynamo 1.6.1 lifecycle support is validated.
- [ ] Complete a full output-encoding review and define auth/authorization before adding any future mutating API.
- [ ] Build and test the Control Center without restarting production until explicitly approved.

### Read-only integration source update — 2026-11-03

- [x] Add Agent health and `/v1/models` status to the existing dashboard API.
- [x] Add Dynamo `/health` status to the existing dashboard API.
- [x] Remove profile apply UI and disable the old Docker/systemd profile-switch route.
- [x] Escape dynamic service-card values.
- [ ] Compare canonical source against host working tree, build, and test after explicit deployment approval.


### Auto text and Vision API verification — 2026-11-03

- [x] Verify a real Persian text chat through `model=Auto`.
- [x] Verify a real JPEG image request through `model=Auto` using OpenAI-compatible multimodal message content and a Base64 data URL.
- [x] Confirm the Vision API returned a structured Persian description and token usage.
- [ ] Separately verify image upload and response through the Open WebUI browser interface.
- [ ] Validate OCR field accuracy against the original image before treating extracted business/document values as authoritative.


## Control Center full modernization — 2026-11-03

- [x] Confirm existing .NET 10 Control Center is active on port 5090 and must be evolved in place.
- [x] Capture existing dashboard/API/history implementation and identify obsolete profile-based model checks.
- [x] Capture Agent Registry route inventory from host output: list, sync, approve/reject, patch, enable/disable, per-model status.
- [x] Confirm public Agent model endpoint remains logical `Auto`; admin Registry data is separate.
- [x] Confirm no queue/request-status endpoint was present in inspected Agent routes; do not invent queue UI.
- [ ] Archive exact Agent admin route, schema, auth, and Registry repository source files in GitHub after obtaining their exact contents.
- [ ] Design Control Center backend adapter for authenticated Registry reads/actions, without exposing the Agent admin key to browser JavaScript.
- [ ] Replace legacy profile dashboard concepts with Dashboard, Model Registry, Runtime/Workers, Resource Monitor, Events, and System views.
- [ ] Add safe UI actions for Registry approval/enablement only after verifying request/response schemas and CSRF/auth boundary.
- [ ] Add Dynamo worker discovery and dependency health (frontend, etcd, NATS, PostgreSQL, Agent) from authoritative sources.
- [ ] Keep lifecycle controls read-only until a safe Model Manager API supports request leases, queueing, drain, and safe unload.
- [ ] Remove/retire stale profile manifest usage only after the replacement is verified; retain backups during migration.
- [ ] Build and test locally; deploy/restart only after explicit approval.


## Unified management delivery — integrated priority (2026-11-04)

The four capabilities are one deliverable; do not ship isolated mock controls. Full contract: [architecture/model-management.md](../architecture/model-management.md).

- [ ] Capture exact current host source for all Agent modules to be changed; do not reconstruct missing files.
- [ ] Additive Registry migration and metadata-only manual model registration (new models pending/disabled, audit logged).
- [ ] Durable PostgreSQL request queue and request leases; streaming-safe release on success, failure, timeout, and disconnect.
- [ ] Queue admission/backpressure, cancellation, FIFO/priority policy, stale lease recovery, and concurrency tests.
- [ ] Validate supported Dynamo 1.6.1 bare-metal worker lifecycle control surface; resolve shared frontend/worker topology and existing port 8013 collision.
- [ ] Implement gated lifecycle adapter, memory admission with safety reserve, serialized load, drain-first unload, safe idle eviction, and recovery tests.
- [ ] Add authenticated Model Manager APIs and secure Control Center admin session; do not expose mutations anonymously.
- [ ] Extend Runtime and Monitoring with measured GPU memory, model desired/observed residency, active leases, queue depth, worker readiness, and operation events.
- [ ] Build/unit/integration/smoke tests, then one coordinated deployment after explicit user approval.

Current hard gates: exact host source capture; Dynamo bare-metal lifecycle adapter validation; Control Center administrator authentication. No queue/lifecycle APIs or UI controls are implemented yet; no synthetic metrics are permitted.


## 2026-11-04 implementation checkpoint

Completed in GitHub source only:
- Exact deployed Agent settings, Dynamo provider, and Registry schema snapshots captured from the host.
- Manual metadata-only Registry registration endpoint (pending + disabled by default).
- Durable request queue and renewable per-request leases, integrated with streaming and non-streaming chat execution.
- Authenticated queue/status and queued-request cancellation endpoints.
- Explicit HTTP 501 load/unload responses until a supported Dynamo Compose lifecycle adapter is proven.

Remaining before deployment:
1. Run Python compile/import checks and focused unit/integration tests against the exact installed dependency versions.
2. Validate PostgreSQL UUID binding, advisory-lock concurrency, cancellation, streaming disconnect, lease heartbeat/recovery, and queue timeout under concurrent requests.
3. Decide safe global/per-model admission limits using measured GB10 RAM/GPU memory and actual worker configuration; current default of 8 per model is provisional.
4. Validate a supported Dynamo 1.6.1 bare-metal worker start/readiness/drain/removal mechanism; do not substitute Docker stop/start.
5. Implement resource admission, load operations, drain-first eviction, desired/observed worker state, and GPU memory telemetry only after validation.
6. Design authenticated Control Center admin sessions before exposing any Registry mutation or Model Manager actions in the browser.
7. After source review and explicit user approval, synchronize files, apply additive schema via controlled Agent startup, and verify health/API behavior. No deployment is authorized by these GitHub commits.
- Queue backpressure has a configurable per-model queued-request ceiling (default 1000). Validate the chosen limit and HTTP/SSE behavior in load tests before production deployment.


## General Assistant product quality — primary priority (2026-11-04)

The primary outcome is a polished, all-purpose chat experience through one logical `Auto` assistant. Work should be organized as coherent end-to-end capabilities, not disconnected demos.

Required capability tracks:
1. Core conversation quality: intent understanding, appropriate reasoning depth, reliable concise/detailed answers, multilingual Persian RTL, and robust error handling.
2. Conversation continuity: checkpoint correctness, durable context, edited/regenerated branch handling, concurrent-turn safety, and explicit memory boundaries.
3. Tool orchestration: real structured tool calls, SearXNG search, source-grounded answers, tool timeouts/failures/cancellation, and reusable Tool Registry contracts.
4. Multimodal work: vision and image understanding, document/file analysis, and later audio/video where reliable.
5. Coding and workspace tasks: route to approved coding capability and controlled workspace tools within the same assistant.
6. Intelligent model routing: choose by capability and task complexity while respecting Registry eligibility and Model Manager resource/queue policies.
7. Product acceptance: test meaningful end-to-end tasks through Open WebUI → Auto → Agent → tools/models, including failures. Do not mark a capability complete based only on source implementation or a successful health endpoint.

Keep the existing central General Assistant architecture. Do not add a separate Coding Agent by default. Preserve production state and obtain explicit approval before deployment or service/worker restarts. See `architecture/assistant-quality.md` for the full acceptance contract.


### Tool orchestration hardening — 2026-11-04
- [x] Improve General Assistant task-completion, multilingual/Persian RTL, safe-default, and truthful-action system instructions.
- [x] Strengthen live-search policy and source-grounding requirements.
- [x] Add SearXNG timeout/error classification, response validation, safe URL filtering, deduplication, and bounded snippets.
- [x] Keep structured LangGraph ToolNode execution and handle tool exceptions as model-visible tool errors.
- [ ] Run compile/import and focused tool tests against the exact host dependency versions.
- [ ] Verify Qwen3.8-VL emits compatible structured tool calls through the active Dynamo parser.
- [ ] Verify SearXNG JSON output and Persian research end-to-end after explicit deployment approval.


### General Assistant tool-cycle validation — 2026-11-04
- [x] Make graph model injection functional so the tool cycle can be tested without contacting Dynamo.
- [x] Add deterministic async regression test for structured tool call → ToolNode → ToolMessage → final assistant response.
- [ ] Execute the regression test in the DGX Agent virtual environment and resolve any dependency/API mismatch.
- [ ] Validate actual Qwen3.8-VL structured tool calls through Dynamo's configured parser.
- [ ] Run end-to-end Persian SearXNG research after explicit deployment approval.
- [x] Add deterministic SearXNG response validation and URL-filtering regression tests.
- [ ] Execute graph and SearXNG tests in the DGX Agent virtual environment.

### Deterministic web research routing — 2026-11-04
- [x] Add Persian/English intent detection for explicit web research and current-information requests.
- [x] Force a structured web tool call on the first assistant response for a detected research turn.
- [x] Return to automatic tool choice after the tool result so the assistant can synthesize or continue focused research.
- [x] Disable Qwen thinking only for web-research turns, retaining the configured thinking behavior for normal chat.
- [x] Inject the server-local runtime date/time into the system prompt.
- [x] Add deterministic regression coverage for routing and tool execution.
- [ ] Run compile/import and unit tests in the DGX Agent virtual environment.
- [ ] Run one bounded live Persian research request through Agent Auto and verify SearXNG results, structured tool calls, citations, and final answer.
- [ ] Verify streaming requests preserve the same tool execution and final-response behavior.
\n\n### Qwen XML tool-call compatibility — 2026-11-04\n- [x] Add a strict adapter for complete Qwen XML tool-call text returned in AIMessage.content.\n- [x] Allow only currently registered tool names and schema-declared parameters.\n- [x] Validate parsed arguments with the tool's Pydantic schema before converting to LangChain tool_calls.\n- [x] Keep LangGraph ToolNode as the only tool execution mechanism.\n- [x] Add parser and end-to-end graph regression tests, including multiple calls and malformed/untrusted markup.\n- [ ] Run syntax/import checks and focused tests in the DGX Agent virtual environment.\n- [ ] Synchronize the reviewed source to DGX and verify Persian web research through Auto after explicit deployment approval.\n