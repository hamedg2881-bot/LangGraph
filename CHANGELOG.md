# Change Log

## 2026-11-02 — Initial repository documentation
- Created project notebook structure for LangGraph Agent on DGX Spark.
- Recorded architecture, confirmed decisions, current status, and roadmap.
- Added sanitized Registry schema and deployment environment template.
- Recorded successful Registry startup, admin authentication, and health checks.
- No production host files or secrets were changed by this documentation commit.

## 2026-11-02 — Admin API verification
- Confirmed authenticated GET /admin/models returns HTTP 200 with a data array.
- Confirmed qwen38-vl is approved and enabled with chat and vision capabilities.

## 2026-11-02 — Request-scoped model routing
- Implemented per-request capability classification for vision, coding, and chat.
- Added eligibility checks for Registry approval, enablement, live Dynamo discovery, and capability match.
- Updated LangGraph chat invocation to use the selected model ID through RunnableConfig.
- Preserved the existing graph, PostgreSQL checkpointer, and conversation thread IDs.
- Verified real text and image requests through the agent.

## 2026-11-02 — Logical Auto endpoint
- Updated GET /v1/models to return only the logical model Auto, independent of Dynamo availability.
- Kept actual runtime selection in the LangGraph request path.
- Archived exact app/api/routes.py and app/api/schemas.py snapshots.
- Applied the change on the host, compiled the application, and verified GET /v1/models returns only Auto.
- Restarted langgraph-agent.service with user approval; health returned HTTP 200.
- Verified a real chat request with model=Auto returned the expected Persian response.
- User tested Open WebUI and confirmed the Auto integration works.

## 2026-11-02 — Intentional Coder pause for Vision worker
- Recorded that the Coder worker was intentionally taken out of the active deployment to free resources for the Qwen 3.8-VL worker; this was a planned sequencing decision, not an unexpected failure.
- Latest Dynamo runtime discovery exposes qwen38-vl only.
- Latest authenticated Registry response contains qwen38-vl only, approved and enabled with chat and vision capabilities.
- Latest combined Compose status shows etcd, NATS, dynamo-frontend, and dynamo-vllm-vision38 running.
- Recorded a discrepancy between service keys shown by grep in the named Compose files and service names in the combined Compose status. Effective Compose configuration must be inspected before changing deployment files.
- No worker or Compose configuration was changed during this status update.
