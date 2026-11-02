# Source and Configuration File Inventory

This inventory tracks project files created or changed on the DGX Spark host. Snapshots are added only when their exact current contents have been retrieved and reviewed. Do not invent missing file contents.

## Chat and routing implementation

| Host path | Purpose | Repository snapshot |
|---|---|---|
| `app/graph/chat.py` | Compiled LangGraph chat graph and assistant node | Pending exact snapshot |
| `app/api/routes.py` | OpenAI-compatible chat and model-list endpoints | Pending exact snapshot |
| `app/providers/dynamo.py` | Dynamo-backed LangChain chat model factory | Pending exact snapshot |

## Registry implementation

| Host path | Purpose | Repository snapshot |
|---|---|---|
| `app/registry/schema.sql` | Registry tables and indexes | `database/schema.sql` |
| `app/registry/database.py` | Async PostgreSQL pool and schema initialization | Pending exact snapshot |
| `app/registry/repository.py` | Registry data access and administrative mutations | Pending exact snapshot |
| `app/config/settings.py` | Application settings, including admin secret setting | Pending exact snapshot |
| `app/api/admin_auth.py` | Bearer authentication dependency | Pending exact snapshot |
| `app/api/admin_routes.py` | Registry administrative endpoints | Pending exact snapshot |
| `app/main.py` | FastAPI lifespan and router registration | Pending exact snapshot |

## Host configuration

| Host path | Purpose | Repository handling |
|---|---|---|
| `config/agent.env` | Live environment variables and secrets | NEVER COMMIT |
| `config/agent.env.example` | Sanitized environment template | `deployment/agent.env.example` after exact review |
| `/etc/systemd/system/langgraph-agent.service` | Agent systemd unit | Pending sanitized snapshot |
| `backups/pre-registry-20261102-120939` | Pre-Registry backup | Host-only; do not commit backup bundle |

## Important

- Do not copy secret-bearing files or live data into GitHub.
- A file marked pending must be fetched from the host before creating its source snapshot.
- Update this inventory whenever a tracked project file is created, modified, or retired.
