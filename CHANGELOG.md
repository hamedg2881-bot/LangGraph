# Change Log

## 2026-11-02 — Initial repository documentation
- Created project notebook structure for LangGraph Agent on DGX Spark.
- Recorded architecture, confirmed decisions, current status, and roadmap.
- Added sanitized Registry schema and deployment environment template.
- Recorded successful Registry startup, admin authentication, and health checks.
- No production host files or secrets were changed by this documentation commit.

## 2026-11-02 — Request-scoped model routing
- Implemented per-request capability classification for vision, coding, and chat.
- Added eligibility checks for Registry approval, enablement, live Dynamo discovery, and capability match.
- Updated LangGraph chat invocation to use the selected model ID through RunnableConfig.
- Preserved the existing graph, PostgreSQL checkpointer, and conversation thread IDs.
- Verified real text and image requests through the agent.

## 2026-11-02 — Logical Auto endpoint
- Updated GET /v1/models to return only the logical model Auto, independent of Dynamo availability.
- Kept actual runtime selection in the LangGraph request path.
- Applied the change on the host, compiled the application, and verified GET /v1/models returns only Auto.
- Restarted langgraph-agent.service with user approval; health returned HTTP 200.
- Verified a real chat request through model=Auto.
- User tested Open WebUI and confirmed the Auto integration works.

## 2026-11-02 — Intentional Coder pause for Vision worker
- Coder was intentionally paused to free resources for the Qwen 3.8-VL worker; this is planned sequencing, not an unexpected failure.
- Latest Dynamo runtime and Registry responses expose qwen38-vl only; it is approved, enabled, and has chat and vision capabilities.

## 2026-11-02 — Active Compose provenance and snapshots
- Container labels identify the frontend Compose files as compose.yaml, compose.vision38.yaml, and compose.gateway.yaml.
- Container labels identify the Vision38 worker Compose files as compose.yaml and compose.vision38.yaml.
- Archived the exact retrieved compose.vision38.yaml and compose.gateway.yaml contents under deployment/.
- Updated the source inventory and operational status to identify the still-unarchived base compose.yaml.
- Confirmed compose.vision.yaml is not the active Vision38 overlay.
- No running service or deployment configuration was changed.
