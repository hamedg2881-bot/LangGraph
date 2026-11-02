# Change Log

## 2026-11-02 — Initial repository documentation
- Created project notebook structure for LangGraph Agent on DGX Spark.
- Recorded architecture, confirmed decisions, current status, and roadmap.
- Added sanitized Registry schema and deployment environment template.
- Recorded successful Registry startup, admin authentication, and health checks.
- No production host files or secrets were changed by this documentation commit.

## 2026-11-02 — Admin API verification
- Confirmed authenticated GET /admin/models returns HTTP 200 with a data array.
- Confirmed qwen38-vl was initially pending, disabled, and had no assigned capabilities.

## 2026-11-02 — Request-scoped model routing design
- Recorded request capability categories: vision, coding, and chat.
- Chose per-request model selection through LangGraph runtime configuration.
- Preserved the existing compiled graph, PostgreSQL checkpointer, and conversation thread IDs.
- Required Registry approval, enablement, live Dynamo discovery, and capability match before selection.
- Deferred changing /v1/models to Auto until routing implementation and tests.

## 2026-11-02 — Request-scoped routing implemented and verified
- Added app/model_selector.py for capability classification and Registry/Dynamo eligibility checks.
- Updated the LangGraph chat node to consume the selected model ID from RunnableConfig.
- Updated the chat API route to select a model per request and pass it to both streaming and non-streaming graph execution.
- Approved and enabled qwen38-vl in Registry with chat and vision capabilities.
- Verified selector results for chat and vision both resolve to qwen38-vl.
- Restarted langgraph-agent.service with user approval; health check returned HTTP 200.
- Verified a real Persian text chat request and a real image-understanding request both returned HTTP 200.

## 2026-11-02 — Logical Auto model endpoint
- Updated GET /v1/models to return only the logical model Auto, independent of Dynamo availability.
- Kept runtime model selection in the chat request path, where Registry approval, enablement, live runtime discovery, and capability matching are enforced.
- Archived the exact current app/api/routes.py and app/api/schemas.py source snapshots.
- Host application and endpoint verification are pending user application and service restart.

## 2026-11-02 — Logical Auto endpoint applied and verified
- Applied the archived app/api/routes.py change on the DGX Spark host.
- Compiled the application and verified the model-list response contains exactly one model, Auto.
- Restarted langgraph-agent.service with user approval; service state is active and health returned HTTP 200.
- Verified GET /v1/models exposes only Auto.
- Verified a real non-streaming chat request using model=Auto returned the expected Persian response.
