# Unified Model Management Architecture

Last updated: 2026-11-04

## Purpose

This document is the implementation contract for completing Model Registry, Model Manager, Runtime Management, and Monitoring as one coherent control plane on the DGX Spark.

The system architecture remains:

`Open WebUI → LangGraph Agent → NVIDIA Dynamo → Model Workers`

The existing Persian RTL DGX Spark Control Center remains the administrative UI. Open WebUI exposes only the logical `Auto` model. Registry policy and request orchestration stay in LangGraph; Dynamo remains the inference/runtime and worker-discovery layer.

## Current verified baseline (2026-11-04)

- Control Center 2.0.0 is published and running on port 5090; health returns `ok`.
- Agent is healthy on port 8100 and exposes only `Auto` through `GET /v1/models`.
- Dynamo frontend is healthy on port 8013 and currently discovers `qwen-coder` and `qwen38-vl`.
- Registry contains two models:
  - `qwen38-vl`: approved, enabled, capabilities `chat, vision`, context 32768.
  - `qwen-coder`: approved, enabled, capability `coding`, context 65536.
- A manual authenticated `POST /admin/models/sync` completed on 2026-11-04 and reported `discovered_count: 2`; both models' `last_seen_at` values advanced to the current sync time and their administrative decisions remained approved.
- The Control Center reports 9 runtime containers: 7 running and 2 exited legacy containers.
- Existing APIs expose Registry listing/sync/approval/rejection/update/enable/disable/status, host/runtime status, resource history, and events.
- There is currently no request queue API, no Model Manager API, no worker lifecycle adapter, and no Control Center admin-session authentication.
- The current model selection path checks approval, enablement, live Dynamo discovery, and capability. It does not yet acquire a request lease or queue a request while a model is unloaded/busy.

## 1. Model Registry

### Responsibilities

Registry is the catalog and policy store. It is not a model downloader, installer, runtime loader, or worker controller.

Required operations:

- List/search/filter models and inspect metadata, capabilities, context length, quantization, architecture, provider, approval, enablement, last discovery time, live runtime state, and selectability.
- Manually register a model by metadata only. Registration must not download weights, create a container, start a worker, or load the model.
- Automatically discover models from Dynamo.
- Insert newly discovered models as `pending` and disabled.
- Preserve all existing administrative decisions and curated fields during discovery sync. For existing IDs, update discovery timestamps only.
- Approve/reject, enable/disable, and edit metadata/capabilities with audit records.
- Keep approval, enablement, runtime availability, and memory residency as distinct state dimensions.

### Manual registration contract

Proposed authenticated endpoint: `POST /admin/models`.

Required validation:
- Stable, unique model ID; non-empty display name and provider.
- Optional architecture, quantization, context length, capabilities, runtime descriptor, model path reference, and estimated memory footprint.
- Capabilities restricted to the existing supported set.
- Model path and worker descriptor are references/configuration only; registration must never access the filesystem to download or install anything.
- New manual records default to `approval_status=pending` and `is_enabled=false`.
- Duplicate IDs return HTTP 409; invalid metadata returns HTTP 422.
- Audit action records `registered` with actor and notes.

Discovery remains independent from manual registration. A discovered model does not become approved or enabled automatically.

## 2. Model Manager

### Responsibilities

Model Manager is a separate orchestration service within the LangGraph Agent. It coordinates request admission, queueing, model residency, and safe worker lifecycle through a validated Dynamo/worker adapter.

It must not be implemented as direct ad-hoc Docker commands in the UI or Registry.

### Request lifecycle

Every chat request must follow this lifecycle:

1. Classify required capability and find Registry-eligible models.
2. Acquire a request lease for the selected model (or reserve a queue position if it is not ready/capacity is unavailable).
3. Ensure the requested worker is available and admitted under the memory budget.
4. Invoke the existing LangGraph graph with the selected model ID and the existing conversation thread ID.
5. Hold the lease for the complete inference lifetime, including the full streaming response.
6. Release the lease in a `finally`/cancellation-safe path on success, failure, disconnect, and timeout.
7. Mark the queue item terminal and notify the next eligible waiter.

No request may be forcibly interrupted to make room for another model.

### Queue contract

The queue must be durable in the existing PostgreSQL database and must not reuse or modify LangGraph checkpointer tables.

Suggested table prefix: `model_manager_`.

A queue record should include:
- Request/queue ID and idempotency key.
- Requested model ID or capability.
- User/conversation correlation ID (not secrets or message contents).
- State: `queued`, `waiting_for_capacity`, `loading`, `running`, `completed`, `failed`, `cancelled`, or `timed_out`.
- Priority, FIFO sequence, enqueue/start/finish timestamps.
- Lease/heartbeat metadata and safe error code.
- Bounded retry count and expiration/deadline.

Rules:
- FIFO within priority class; no starvation of ordinary requests.
- Configurable queue capacity and maximum wait.
- Backpressure with a clear HTTP 429/503 response when the queue is full/unavailable.
- Cancellation removes a waiting request; cancellation of an active generation follows the inference cancellation path and releases its lease only after execution has actually stopped.
- Stale lease recovery must not infer that a worker is idle solely because an API client disconnected.
- Do not store prompts, generated content, API keys, or other secrets in queue records.
- Queue state and counts exposed to the UI must come from these persisted records, never fabricated counters.

### Residency and resource admission

Model approval and enablement do not imply that weights are resident.

Before loading:
- Read current host memory and GPU memory telemetry.
- Apply a configurable safety reserve for OS/runtime, KV cache, vision activations, CUDA allocations, and transient load peaks.
- Require a model-specific estimated load footprint and a conservative admission margin.
- Serialize heavy load operations on the single DGX Spark accelerator unless a tested resource plan explicitly permits concurrency.
- If capacity is insufficient, wait or select only a safe eviction candidate.

Eviction:
- Candidate must have zero active request leases, zero in-flight worker operations, and exceed a configurable idle interval.
- Mark the model as draining before eviction so no new lease is admitted.
- Wait for all leases to finish and confirm worker idle/readiness through the runtime adapter.
- Only then request unload/worker scale-down.
- If drain times out, abort eviction and return the model to ready state; never force-stop the worker.
- Keep the desired worker state and observed runtime state separate.

### Model Manager APIs (target contract)

Authenticated Agent admin endpoints:
- `GET /admin/model-manager/status`
- `GET /admin/model-manager/queue`
- `GET /admin/model-manager/models/{model_id}`
- `POST /admin/model-manager/models/{model_id}/load`
- `POST /admin/model-manager/models/{model_id}/unload` (drain-first; reject while leases remain unless wait mode is requested)
- `POST /admin/model-manager/queue/{queue_id}/cancel`
- `PATCH /admin/model-manager/policy` for bounded policy fields only.

Every mutation must be audited. Model load/unload APIs must return an operation ID and asynchronous state, not claim success before the runtime confirms it.

## 3. Runtime Management

Runtime Management observes actual runtime state and calls the Model Manager; it does not call Docker/systemd directly from the browser.

Required per-model view:
- Registry approval and enablement.
- Desired state: `stopped`, `starting`, `ready`, `draining`, `stopping`, or `error`.
- Observed Dynamo discovery state and worker identity.
- Worker/container name, component/namespace, endpoint identity, start/last-seen time.
- Active request leases, queue depth, load/unload operation state.
- Resource estimate and observed GPU/host memory where available.

Container inventory remains a separate host-runtime view. A running container is not proof that a model is registered or inference-ready; an exited legacy container is not automatically an error if it is intentionally retired.

### Dynamo lifecycle adapter gate

The deployed stack is NVIDIA Dynamo 1.6.1 with local/bare-metal Docker Compose, etcd/NATS discovery/event services, and vLLM workers. Do not assume Kubernetes Operator APIs are available on this host.

Dynamo's architecture documentation describes worker discovery through etcd and Planner control connections/signals; it describes the Dynamo Operator reconciling desired worker counts in Kubernetes. That is not proof of a supported bare-metal HTTP load/unload API for this deployment.

Before enabling real worker lifecycle operations:
1. Inspect the exact deployed Dynamo 1.6.1 source/runtime and installed CLI/API surfaces.
2. Identify a supported mechanism to start an independently described worker that registers with the shared frontend/discovery plane.
3. Verify graceful drain/termination semantics and worker readiness signals.
4. Resolve the existing Compose host-port collision: the archived Coder worker definition and gateway overlay both publish host port 8013.
5. Verify worker start, discovery, inference, drain, and removal in an isolated controlled test.
6. Implement the adapter behind an explicit capability flag; when unavailable, load/unload endpoints must return HTTP 501/503 and the UI must show the feature as unavailable.

Do not use `docker start/stop`, `docker compose up/down`, or `systemctl start/stop` as a substitute for request-aware lifecycle coordination.

## 4. Monitoring

The Control Center must display only measured/returned values.

Required panels:
- Agent and Dynamo health, HTTP status, and logical Auto model.
- Dynamo-discovered models and last discovery timestamp.
- Registry counts by approval, enablement, and live availability.
- Per-model desired/observed residency, active leases, queue depth, and lifecycle operation state.
- Host RAM, swap, disk, load average, GPU utilization, temperature, power, and GPU memory used/total/free.
- Runtime container inventory with running/exited/created/unknown states and role classification.
- Historical resource samples and runtime/manager events with filters and retention.
- Recent errors with safe, redacted messages.

GPU memory telemetry is currently absent from the Control Center's `nvidia-smi` query and must be added only after exact fields are tested on the GB10 host.

Monitoring APIs should expose timestamps, source, and staleness. A stale value must be labeled stale rather than silently presented as current.

## 5. Control Center integration and security

- Extend the existing Persian RTL Control Center; do not create a second dashboard.
- The current Control Center has no application-level admin session authentication. It must remain read-only for mutating operations until an administrator authentication/session design is implemented.
- Never forward the Agent admin key to browser JavaScript. Keep it server-side.
- Protect all mutating proxy routes with authenticated admin sessions, CSRF protection where cookie sessions are used, strict input validation, and audit logging.
- Read-only monitoring may remain available only within the explicitly trusted network boundary.
- Do not expose Docker socket or raw host command execution through HTTP endpoints.
- Show unavailable/not-implemented states explicitly; never create fake queue counts, residency state, or load/unload buttons.

## 6. Implementation sequence

The four areas are one integrated deliverable but have hard dependency gates:

1. Capture exact current host source for all Agent files that will be modified, including settings, graph/provider, Registry schema/repository, and API startup. The repository currently has only partial source snapshots; do not reconstruct missing production files from memory.
2. Add additive PostgreSQL migration(s) for manual registration, queue, request leases, model desired/observed state, and audit. Preserve all existing Registry rows and LangGraph checkpointer data.
3. Implement Registry manual registration and audit tests.
4. Implement durable queue, leases, cancellation, and streaming-safe release in Agent; test concurrency, disconnects, exceptions, worker failures, queue full, and stale lease recovery.
5. Validate the Dynamo 1.6.1 bare-metal worker lifecycle adapter and resolve port topology.
6. Implement resource admission, serialized load operations, draining, safe idle eviction, and recovery.
7. Add authenticated Agent Model Manager APIs and authenticated Control Center admin integration.
8. Extend monitoring with queue, leases, desired/observed runtime, GPU memory, and operation history.
9. Run unit/integration tests and host API smoke tests; then provide exact GitHub files and one coordinated deployment sequence. No host deployment occurs until the user approves it.

## Non-goals and safety constraints

- No separate Coding Agent; retain one General Assistant.
- Open WebUI connects only to LangGraph Agent and exposes only `Auto`.
- Registry does not download, install, load, unload, or activate models.
- Never force-interrupt active inference.
- Never unload a model while a lease or worker operation is active.
- Never alter LangGraph checkpointer tables or conversation history.
- Never commit environment files, API keys, passwords, tokens, database dumps, model weights, or user data.
- No service restart, deployment, container mutation, model activation, download, or installation without explicit user approval.
