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
| /opt/ai/control-center/src/ControlCenter/Program.cs | Minimal API, status/resource collection, history/events APIs, read-only Agent/Dynamo status; legacy profile-switch route disabled with HTTP 410 | source/control-center/Program.cs |
| /opt/ai/control-center/src/ControlCenter/HistoryBackgroundService.cs | 60-second resource sampling, readiness events, 30-day retention | source/control-center/HistoryBackgroundService.cs |
| /opt/ai/control-center/src/ControlCenter/wwwroot/index.html | Persian RTL dashboard UI with read-only Agent/Dynamo runtime panel | source/control-center/wwwroot/index.html |

The four source files above were fetched from the user's uploaded text snapshots under archive/control-center/source/ and copied byte-for-byte as UTF-8 text into source/control-center/. The original archive is retained as provenance; source/control-center/ is the canonical editable source snapshot going forward.

The initial source snapshot was inspected and then updated in the canonical repository: Program.cs now exposes GET /api/ai-status and disables profile mutation with HTTP 410; index.html shows Agent/Dynamo status, removes profile-apply controls, and escapes dynamic service fields. ControlCenter.csproj and HistoryBackgroundService.cs remain unchanged. These repository edits have not yet been synchronized to the host, built, or deployed.
