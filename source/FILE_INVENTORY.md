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
