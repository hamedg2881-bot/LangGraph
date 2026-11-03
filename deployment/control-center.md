# DGX Spark Control Center

## Existing deployment (verified 2026-11-03)

- systemd unit: `dgx-control-center.service`
- Status: active
- Application: DGX Spark Control Center
- Runtime: .NET 10
- Published assembly: `/opt/ai/control-center/publish/ControlCenter.dll`
- Working directory: `/opt/ai/control-center/publish`
- Host port: 5090
- Health endpoint: `GET /api/health`
- Verified health response: status `ok`

## Existing API surface observed

- `GET /api/health`
- `GET /api/profiles`
- `GET /api/status`
- Earlier documented endpoints include history, events, and profile switching; their current availability must be rechecked before relying on them.

## Legacy configuration found

The current profile API returns `coding` and `image` profiles and service definitions for `qwen-coder` and `qwen36-vl`. Their health URLs use ports 8010 and 8012. These are legacy values and are not authoritative for the current Dynamo frontend/runtime, whose host API is on port 8013.

The status API reports host resource metrics. On 2026-11-03 it reported 121.69 GiB total memory, 9.47 GiB available, and 112.21 GiB used. This is a historical snapshot, not a live value.

## Agreed direction

Extend this existing Control Center in place. Do not create a parallel dashboard.

The UI should ultimately present:
1. Model catalog and capabilities from the LangGraph Registry.
2. Approval and enablement state from Registry.
3. Actual runtime/readiness state from Dynamo and the Agent.
4. Host memory/resource information.
5. Model selection and lifecycle controls through the existing architecture, with safe request draining/queueing policies.

LangGraph chooses the best eligible model for each request. Dynamo is the inference/runtime layer. Registry is the catalog and policy layer. Open WebUI exposes only `Auto`.

Each model must be independently runnable. Simultaneous execution/residency of heavy models is not required.

## Change safety

- Preserve existing Control Center features and service.
- Do not edit or restart the service until its source/UI and API implementation have been inspected.
- Do not treat legacy profile health URLs as current Dynamo runtime status.
- Do not commit secrets, credentials, live environment files, database contents, or model weights.



## Source inspection — 2026-11-03

The user-provided source snapshot has been read and copied to the canonical source tree:

- `source/control-center/ControlCenter.csproj`
- `source/control-center/Program.cs`
- `source/control-center/HistoryBackgroundService.cs`
- `source/control-center/wwwroot/index.html`

The original uploaded files remain under `archive/control-center/source/` as an immutable intake/archive copy. Future reviewed source updates belong under `source/control-center/`; update the inventory and this document whenever a source file changes.

### Observed implementation

- .NET 10 minimal API listening on `0.0.0.0:5090`.
- APIs: health, profiles, status, history, events, and profile-switch.
- Host telemetry reads `/proc/meminfo`, disk information, load average, and `nvidia-smi`.
- Background service samples every 60 seconds, records readiness transitions, and prunes JSONL history after 30 days.
- Persian RTL UI presents host metrics, service status, legacy profile preview/switching, charts, and event filters.

### Findings and constraints

1. The profile manifest is still the old profile-based control model. Its service definitions and health URLs are not the source of truth for the current Dynamo/LangGraph model runtime.
2. The profile-switch endpoint directly invokes `docker start/stop` and `systemctl start/stop`. It must not be used as the future model scheduler: it has no request-lease/drain/queue coordination with LangGraph or Dynamo and can interrupt active work.
3. The API binds to all interfaces and the inspected source contains no authentication or authorization middleware. In particular, profile switching is an administrative operation exposed without an application-level auth check in this source. Before retaining any mutating endpoint, add an approved authentication/authorization design and network boundary.
4. The UI currently injects several service fields into HTML templates without consistently applying `escapeHtml`; treat service names, URLs, errors, and runtime values as untrusted display data.
5. GPU telemetry reports utilization, temperature, and power only; GPU memory fields are intentionally null.
6. The UI currently labels the dashboard as a read-only initial version while also exposing a mutating profile-switch control; the description and actual behavior are inconsistent.

### Agreed integration direction

Keep the existing dashboard and service. Evolve it in place to read model catalog/approval/capabilities from the LangGraph Registry and live runtime/readiness from the Agent and Dynamo. Model lifecycle actions must go through the future safe Model Manager/Dynamo adapter, with active-request protection and queueing. Do not wire direct Docker/systemd profile switching into model selection. No host deployment or source modification was performed during this inspection.

## Read-only Agent/Dynamo integration — 2026-11-03

The canonical source snapshot now includes a read-only AI runtime panel:

- `GET /api/ai-status` checks the LangGraph Agent at `LANGGRAPH_AGENT_URL` (default `http://127.0.0.1:8100`) using `/health` and `/v1/models`.
- It checks the shared Dynamo frontend at `DYNAMO_URL` (default `http://127.0.0.1:8013`) using `/health`.
- The UI displays Agent health, logical model IDs (expected to include `Auto`), and Dynamo health.
- The UI's legacy profile preview is informational only; the profile apply controls have been removed.
- `POST /api/profile-switch` is retained only as a compatibility response and returns HTTP 410 Gone. It no longer invokes Docker or systemd.
- Dynamic service fields are HTML-escaped in the service cards.
- `ControlCenter.csproj` and `HistoryBackgroundService.cs` were not changed.

These edits are committed to the canonical GitHub source only. The DGX host source tree, published DLL, and running service have not been changed or tested with this version.

### Deployment command after host-source synchronization and user approval

Run from the DGX host only after confirming the host source matches this canonical snapshot and after explicit approval:

```bash
cd /opt/ai/control-center/src/ControlCenter && dotnet publish -c Release -o /opt/ai/control-center/publish
```

Then restart only with explicit approval:

```bash
sudo systemctl restart dgx-control-center.service && sudo systemctl is-active dgx-control-center.service
```

Verify the new endpoint and dashboard:

```bash
curl -fsS http://127.0.0.1:5090/api/ai-status
```

Expected: Agent health and model list are returned, and Dynamo health is checked against port 8013. A failed check is reported as a status value; it does not trigger a model load or service lifecycle action.


## Agent Registry contract discovered from host — 2026-11-03

The user-provided host route inventory confirms the following LangGraph Agent endpoints:

| Method | Route | Purpose |
|---|---|---|
| GET | `/admin/models` | Read Registry catalog |
| POST | `/admin/models/sync` | Discover/synchronize Dynamo model IDs into Registry |
| POST | `/admin/models/{model_id}/approve` | Approve a model |
| POST | `/admin/models/{model_id}/reject` | Reject a model |
| PATCH | `/admin/models/{model_id}` | Update curated model fields |
| POST | `/admin/models/{model_id}/enable` | Enable an approved model |
| POST | `/admin/models/{model_id}/disable` | Disable a model |
| GET | `/admin/models/{model_id}/status` | Read model status |

All admin routes use the Agent's separate Bearer admin authentication. The secret must remain server-side and must never be sent to browser JavaScript. The exact route implementations and Pydantic schemas still need exact source snapshots before wiring mutation forms.

Public Agent routes remain `GET /v1/models` (logical `Auto` only), `POST /v1/chat/completions`, and `GET /health`. Do not confuse the public logical model list with the Registry catalog.

The inspected route inventory contains no request queue, in-flight request, or queue-management endpoint. Therefore the first Control Center modernization must not display invented queue state or provide queue/lifecycle controls. Model lifecycle remains outside the Control Center until a safe Model Manager contract exists.

## Modernization scope

The legacy `coding`/`image` profile UI and profile manifest are obsolete for the current architecture. The existing Control Center will be redesigned in place around:

1. Dashboard and platform health.
2. Model Registry (catalog, capabilities, approval, enablement, discovery).
3. Dynamo runtime and worker discovery.
4. Resource telemetry and history.
5. Events and diagnostics.
6. System dependencies (Agent, Dynamo frontend, etcd, NATS, PostgreSQL, Open WebUI).

Registry is authoritative for administrative model policy; Dynamo is authoritative for live worker availability; LangGraph is authoritative for per-request selection. Do not wire direct Docker/systemd start/stop actions into model selection. Keep PostgreSQL checkpointer and conversation data untouched.

The route inventory above came from the user's supplied host inspection output. The exact source files `app/api/admin_routes.py`, `app/api/admin_auth.py`, `app/api/schemas.py`, and `app/registry/schema.sql` have not yet been archived in this repository. Do not infer request bodies or response schemas from route names alone.


## Exact Agent Registry contract — source captured 2026-11-03

The exact host implementations are archived under source/app/ and the API contract is now verified from source, not inferred from route names.

### Agent admin API

All routes are mounted under /admin/models and the router applies Depends(require_admin) to every endpoint.

| Method | Route | Behavior |
|---|---|---|
| GET | /admin/models | Registry list |
| POST | /admin/models/sync | Fetch Dynamo /models, then upsert discovered models |
| POST | /admin/models/{model_id}/approve | Approve with optional notes |
| POST | /admin/models/{model_id}/reject | Reject with optional notes |
| PATCH | /admin/models/{model_id} | Update display_name, architecture, quantization, context_length, and/or capabilities |
| POST | /admin/models/{model_id}/enable | Enable with optional notes |
| POST | /admin/models/{model_id}/disable | Disable with optional notes |
| GET | /admin/models/{model_id}/status | Return approval, enabled, runtime_status, and selectable |

ModelDecision accepts only optional notes; extra fields are forbidden. ModelUpdate accepts only the listed optional fields; extra fields are forbidden. Supported capabilities are chat, vision, reasoning, coding, and tool_calling.

### Authentication and security

- Admin auth reads the configured admin_api_key, accepts only a Bearer Authorization header, and compares the supplied key using secrets.compare_digest.
- Missing key configuration returns 503; invalid/missing credentials return 401.
- Control Center must proxy admin calls server-to-server. The admin key must never be sent to browser JavaScript, embedded in HTML, or returned by a Control Center endpoint.
- Exact Agent source snapshots are in source/app/api/admin_routes.py, source/app/api/admin_auth.py, source/app/api/schemas.py, source/app/registry/repository.py, source/app/registry/database.py, and source/app/main.py.

### Semantics and implementation caveats

- Registry sync reads Dynamo /models. Existing model rows update only last_seen_at and updated_at; existing approval, enablement, capabilities, and curated metadata are preserved. New-row defaults are defined by the database schema; the schema's exact host source still needs archival.
- Runtime availability is determined by a fresh Dynamo /models query. selectable is true only for approved + enabled + currently available.
- PATCH may update metadata and/or replace the capability set. The repository validates capabilities against the five supported values.
- The current PATCH handler returns updated=true even if the payload contains no fields. A capabilities validation ValueError is not translated to a specific HTTP 4xx in the route. Control Center should validate inputs client-side and surface API errors; a future Agent hardening change may improve these semantics.
- No request queue, active lease, or worker lifecycle API exists in the inspected route set. Do not show queue metrics or offer load/unload/start/stop controls.


## Control Center modernization source — 2026-11-03

The canonical source under `source/control-center/` has been redesigned in GitHub. The existing service identity, port, publish path, and working directory are unchanged in this source-only step.

### Current source API

- `GET /api/health`: application health and source version marker.
- `GET /api/status`: host resources; Agent health and logical model IDs; Dynamo frontend health and model discovery; fixed known-container runtime states.
- `GET /api/ai-status`: compatibility status view for Agent and Dynamo.
- `GET /api/registry/models`: read-only server-side proxy to Agent `GET /admin/models`, enriched with each model's `GET /admin/models/{model_id}/status` result (`runtime_status`, `selectable`).
- `GET /api/history` and `GET /api/events`: existing JSONL history/event views.
- `POST /api/profile-switch`: HTTP 410; direct Docker/systemd profile switching is retired.

The Registry proxy reads `LANGGRAPH_ADMIN_API_KEY` from the Control Center process environment. The key is attached only to server-to-server requests and must never be written to `appsettings*.json`, committed, returned in API responses, or exposed to browser JavaScript. If the variable is absent, Registry reads return 503. Agent base URL is configurable with `LANGGRAPH_AGENT_URL` (default `http://127.0.0.1:8100`); Dynamo frontend with `DYNAMO_URL` (default `http://127.0.0.1:8013`).

### Security and scope boundary

This iteration deliberately exposes Registry reads only. It does not expose `/admin/models/sync`, approve/reject, enable/disable, or PATCH through Control Center. The current service has no application-level administrator authentication/session design; adding mutation proxies before that is implemented would create unauthenticated administrative writes. No queue, lease, load/unload, or worker start/stop controls are implemented because the Agent/Model Manager contract does not currently provide them.

### Build and deployment status

All modernization edits are in GitHub only. The DGX host source, published DLL, environment, and running service have not been changed. Do not copy/publish/restart until explicit user approval. Before enabling Registry reads in production, provide `LANGGRAPH_ADMIN_API_KEY` to the service through a protected systemd environment/credential mechanism outside the repository; do not reuse or expose the Agent's entire `agent.env` file.
