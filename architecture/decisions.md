# Architecture Decisions

## Confirmed decisions

1. Keep the architecture: Open WebUI → LangGraph Agent → NVIDIA Dynamo → Model Workers.
2. Open WebUI ultimately sees only logical model `Auto`.
3. Registry is metadata and policy storage, not a model lifecycle manager.
4. Dynamo is authoritative for live runtime discovery.
5. New discoveries are pending and disabled by default.
6. Approval, enablement, and runtime availability remain independent.
7. Registry tables live in existing PostgreSQL database `langgraph`, schema `public`, with prefix `model_registry_`.
8. Preserve all existing checkpointer tables and conversation history.
9. Use Psycopg 3 async pool; initialize Registry in FastAPI lifespan and attach services to `app.state`.
10. Protect all admin endpoints with a separate `ADMIN_API_KEY` Bearer token; use constant-time comparison and never log or expose the key.
11. Do not download/install/load/activate models through Registry.
12. Preserve Code Intelligence (8200), AstraMap (8300), Control Center (5090), and existing profile behavior.
13. Keep heavy model workers from competing for unified memory.

## Deferred decisions

- Exact classification and routing policy per request type.
- Per-request graph/model construction strategy while preserving checkpointer state.
- Final `Auto` response format and behavior for `/v1/models`.
- Runtime health validation beyond presence in Dynamo `/models`.
- Admin UI and richer audit metadata.
