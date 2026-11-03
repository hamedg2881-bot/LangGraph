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
