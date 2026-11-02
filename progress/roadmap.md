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
- [ ] Test text, vision, coding, and tool-use routes with eligible workers.
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

