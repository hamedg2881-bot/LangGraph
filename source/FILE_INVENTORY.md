# Source and Configuration File Inventory

This inventory tracks project files created or changed on the DGX Spark host. Snapshots are added only when their exact current contents have been retrieved and reviewed. Do not invent missing file contents.

## Chat and routing implementation

| Host path | Purpose | Repository snapshot |
|---|---|---|
| app/model_selector.py | Request capability classification and eligible model selection | source/app/model_selector.py |
| app/graph/chat.py | Compiled LangGraph chat graph and request-scoped model invocation | source/app/graph/chat.py |
| app/api/routes.py | OpenAI-compatible chat endpoint and logical Auto model-list endpoint | source/app/api/routes.py |
| app/api/schemas.py | Pydantic request and model-list response schemas | source/app/api/schemas.py |
| app/providers/dynamo.py | Dynamo-backed LangChain chat model factory | Pending exact snapshot |

## Registry implementation

| Host path | Purpose | Repository snapshot |
|---|---|---|
| app/registry/schema.sql | Registry tables and indexes | database/schema.sql |
| app/registry/database.py | Async PostgreSQL pool and schema initialization | Pending exact snapshot |
| app/registry/repository.py | Registry data access and administrative mutations | Pending exact snapshot |
| app/config/settings.py | Application settings, including admin secret setting | Pending exact snapshot |
| app/api/admin_auth.py | Bearer authentication dependency | Pending exact snapshot |
| app/api/admin_routes.py | Registry administrative endpoints | Pending exact snapshot |
| app/main.py | FastAPI lifespan and router registration | Pending exact snapshot |

## Dynamo deployment snapshots

| Host path | Purpose | Repository snapshot |
|---|---|---|
| /opt/ai/dynamo/deploy/compose.vision38.yaml | Active Qwen 3.8-VL worker service definition | deployment/compose.vision38.yaml |
| /opt/ai/dynamo/deploy/compose.gateway.yaml | Active Dynamo frontend service definition | deployment/compose.gateway.yaml |
| /opt/ai/dynamo/deploy/compose.yaml | Base etcd/NATS and shared network definitions | Pending exact retrieval |
| /opt/ai/dynamo/deploy/compose.vision.yaml | Older/different Vision overlay; not the active Vision38 stack | Not archived as active deployment |


## Dynamo deployment snapshots

| Host path | Purpose | Repository snapshot |
|---|---|---|
| /opt/ai/dynamo/deploy/compose.yaml | Base etcd/NATS and Coder worker definition | deployment/compose.yaml |
| /opt/ai/dynamo/deploy/compose.vision38.yaml | Qwen 3.8-VL worker definition | deployment/compose.vision38.yaml |
| /opt/ai/dynamo/deploy/compose.gateway.yaml | Shared Dynamo frontend definition | deployment/compose.gateway.yaml |
| /opt/ai/dynamo/deploy/compose.vision.yaml | Older/different Vision overlay; not active Vision38 definition | Not archived as active deployment |


## Routing patch

| Repository path | Purpose | Host status |
|---|---|---|
| patches/request-scoped-routing.patch | Historical patch for request-scoped model routing | Applied and verified on host; retained as implementation history |

## Host configuration

| Host path | Purpose | Repository handling |
|---|---|---|
| config/agent.env | Live environment variables and secrets | NEVER COMMIT |
| config/agent.env.example | Sanitized environment template | deployment/agent.env.example after exact review |
| /etc/systemd/system/langgraph-agent.service | Agent systemd unit | Pending sanitized snapshot |
| backups/pre-registry-20261102-120939 | Pre-Registry backup | Host-only; do not commit backup bundle |

## Important

- Do not copy secret-bearing files or live data into GitHub.
- A file marked pending must be fetched from the host before creating its source snapshot.
- Update this inventory whenever a tracked project file is created, modified, or retired.


## Existing Control Center

| Host path | Purpose | Repository documentation |
|---|---|---|
| /opt/ai/control-center/publish/ControlCenter.dll | Existing .NET 10 Control Center published application | deployment/control-center.md (deployment facts; exact source snapshot pending retrieval) |
| /etc/systemd/system/dgx-control-center.service | Control Center systemd unit | deployment/control-center.md (unit facts; exact unit snapshot pending retrieval) |

The published DLL and systemd unit contents have not yet been retrieved. Do not invent source snapshots. Retrieve source files from the host before archiving implementation code. Do not commit secrets or publish output containing credentials.



## Control Center source snapshot — retrieved 2026-11-03

| Host source path | Purpose | Canonical repository snapshot |
|---|---|---|
| /opt/ai/control-center/src/ControlCenter/ControlCenter.csproj | .NET 10 Web SDK project | source/control-center/ControlCenter.csproj |
| /opt/ai/control-center/src/ControlCenter/Program.cs | Minimal API, host telemetry, Agent/Dynamo status, read-only Registry proxy with live per-model availability, history/events APIs; legacy profile-switch route disabled with HTTP 410 | source/control-center/Program.cs |
| /opt/ai/control-center/src/ControlCenter/HistoryBackgroundService.cs | 60-second resource sampling, runtime readiness events, 30-day retention | source/control-center/HistoryBackgroundService.cs |
| /opt/ai/control-center/src/ControlCenter/wwwroot/index.html | Persian RTL dashboard with Overview, Registry, Runtime/Workers, Resources/History, and Events sections | source/control-center/wwwroot/index.html |

The four source files above were fetched from the user's uploaded text snapshots under archive/control-center/source/ and copied byte-for-byte as UTF-8 text into source/control-center/. The original archive is retained as provenance; source/control-center/ is the canonical editable source snapshot going forward.

The initial source snapshot was inspected and then updated in the canonical repository: Program.cs now exposes GET /api/ai-status and disables profile mutation with HTTP 410; index.html shows Agent/Dynamo status, removes profile-apply controls, and escapes dynamic service fields. ControlCenter.csproj and HistoryBackgroundService.cs remain unchanged. These repository edits have not yet been synchronized to the host, built, or deployed.


## Agent Registry source files identified — 2026-11-03

| Host path | Purpose | Repository snapshot |
|---|---|---|
| /opt/ai/langgraph-agent/app/api/admin_routes.py | Registry list, sync, approve/reject, update, enable/disable, per-model status routes | Pending exact source capture |
| /opt/ai/langgraph-agent/app/api/admin_auth.py | Admin Bearer authentication | Pending exact source capture |
| /opt/ai/langgraph-agent/app/api/schemas.py | Agent request/response Pydantic contracts | Pending exact source capture |
| /opt/ai/langgraph-agent/app/registry/schema.sql | PostgreSQL Registry schema | Pending exact source capture |

The host route inventory was supplied on 2026-11-03 and is recorded in `progress/current-status.md` and `deployment/control-center.md`. No exact source body has been fabricated or added to the source tree.


## Agent Registry source snapshots — captured 2026-11-03

| Host path | Purpose | Canonical repository snapshot |
|---|---|---|
| /opt/ai/langgraph-agent/app/api/admin_routes.py | Registry list/sync/approve/reject/update/enable/disable/status API | source/app/api/admin_routes.py |
| /opt/ai/langgraph-agent/app/api/admin_auth.py | Constant-time Bearer admin authentication | source/app/api/admin_auth.py |
| /opt/ai/langgraph-agent/app/api/schemas.py | Chat and public model-list Pydantic schemas | source/app/api/schemas.py (previously archived; exact host output matched) |
| /opt/ai/langgraph-agent/app/registry/repository.py | PostgreSQL Registry repository and policy mutations | source/app/registry/repository.py |
| /opt/ai/langgraph-agent/app/registry/database.py | Async PostgreSQL pool and Registry schema initialization | source/app/registry/database.py |
| /opt/ai/langgraph-agent/app/main.py | FastAPI lifespan, shared PostgreSQL checkpointer, Registry initialization, router registration | source/app/main.py |

The five newly captured files were copied from the exact user-provided host output. source/app/api/schemas.py already existed in the canonical repository and was verified against the supplied output. The app/registry/schema.sql body was not included in this host inspection output and remains pending exact capture. No secrets or environment files were archived.


## Control Center modernization — 2026-11-03

The canonical Control Center source has been redesigned in GitHub only:

- `source/control-center/Program.cs`: replaced profile-manifest status with live Agent, Dynamo, fixed known-container runtime, host telemetry, and a server-side read-only Registry proxy. Registry results are enriched with the Agent's per-model live runtime/selectability endpoint. The Agent admin key is read only from `LANGGRAPH_ADMIN_API_KEY` and is never returned to the browser.
- `source/control-center/wwwroot/index.html`: replaced the legacy profile UI with Persian RTL sections for Overview, Model Registry, Runtime/Workers, Resources/History, and Events. The Registry table shows approval, enablement, capabilities, context length, runtime availability, and selectability.
- `source/control-center/HistoryBackgroundService.cs`: now records runtime readiness transitions from the new `/api/status` response.
- `source/control-center/ControlCenter.csproj`: unchanged.

Security boundary: only read-only Registry access is exposed in this iteration. Registry sync and approval/enablement mutations are intentionally not proxied until a separate Control Center admin authentication/session design is implemented. The service environment must receive `LANGGRAPH_ADMIN_API_KEY` through a protected server-side mechanism; never put it in appsettings committed to GitHub or browser code.

These are GitHub source changes only. No host files, environment variables, build/publish output, systemd service, containers, or models have been changed or restarted. Build and API verification on the DGX host remain pending explicit approval.

## Unified model management design — 2026-11-04

| Repository path | Purpose | Implementation status |
|---|---|---|
| architecture/model-management.md | Integrated contract for Registry, durable queue/leases, residency, Dynamo worker lifecycle adapter, Control Center security, monitoring, and deployment gates | Design documented; implementation pending |

The current Agent and Control Center source snapshots do not yet contain Model Manager APIs, durable queue/lease tables, manual Registry registration, or admin-session authentication. Do not mark these as implemented until exact source files, additive migrations, tests, and host verification are complete.

## Agent runtime source snapshots — captured 2026-11-04

The following files were supplied from the live host at `/opt/ai/langgraph-agent` and committed byte-for-byte as UTF-8 source snapshots:

| Host path | Purpose | Canonical repository snapshot |
|---|---|---|
| app/config/settings.py | Pydantic settings and secret-backed environment configuration | source/app/config/settings.py |
| app/providers/dynamo.py | LangChain OpenAI-compatible Dynamo model factory | source/app/providers/dynamo.py |
| app/registry/schema.sql | Existing PostgreSQL model Registry schema | source/app/registry/schema.sql |

The live `config/agent.env` was not read, copied, or committed. These snapshots complete the missing runtime/config/schema source files needed to reason about the installed Agent. They do not represent a deployment or service restart.

## Model Manager implementation source — 2026-11-04 (GitHub only)

| Repository path | Purpose | Deployment status |
|---|---|---|
| source/app/model_manager.py | Durable per-model queue admission, PostgreSQL request leases, heartbeat, recovery, cancellation, and queue snapshots | Committed; not deployed or tested |
| source/app/registry/schema.sql | Additive model_runtime_requests and model_runtime_leases tables | Committed; not applied to host DB |
| source/app/api/admin_routes.py | Manual metadata-only registration and authenticated Model Manager status/queue/cancel endpoints; lifecycle load/unload returns explicit HTTP 501 | Committed; not deployed |
| source/app/config/settings.py | Queue timeout and per-model active request settings | Committed; not deployed |
| source/app/main.py | ModelManager initialization and authenticated router registration | Committed; not deployed |
| source/app/api/routes.py | Streaming and non-streaming inference protected by request leases | Committed; not deployed |

The queue/lease source is a first implementation checkpoint, not a production-validated Model Manager. Syntax/import checks, PostgreSQL integration tests, concurrency and streaming-disconnect tests, resource-aware admission, Dynamo lifecycle control, GPU memory monitoring, and authenticated Control Center administration remain outstanding. No host source or runtime was changed.
The queue implementation also enforces configurable per-model queue backpressure (`MODEL_MAX_QUEUE_SIZE`, default 1000). This behavior is committed but has not been runtime-tested.


## Agent Model Manager safety correction — 2026-11-04

| Repository path | Purpose | Status |
|---|---|---|
| source/app/__init__.py | Explicit root package initializer | Added |
| source/app/api/__init__.py | Explicit API package initializer | Added |
| source/app/config/__init__.py | Exports Settings and get_settings for Agent startup imports | Added |
| source/app/providers/__init__.py | Explicit providers package initializer | Added |
| source/app/registry/__init__.py | Explicit Registry package initializer | Added |
| source/app/graph/__init__.py | Exports build_chat_graph for Agent startup imports | Added |
| source/app/model_manager.py | Fail-closed lease handling, no expiry-based capacity reclamation, heartbeat retry, reconciliation-required state | Updated |
| source/app/api/routes.py | Explicit streaming queue-timeout SSE response | Updated |
| source/app/registry/schema.sql | Add reconciliation_required request state with repeatable constraint update | Updated |

These changes are canonical GitHub snapshots only. They have not been synchronized to the DGX host or applied to the live PostgreSQL database.
