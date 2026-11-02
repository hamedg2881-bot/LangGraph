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
- The complete exact app/api/routes.py source snapshot remains pending retrieval from the host.
- /v1/models still exposes the Dynamo model list; switching that endpoint to logical Auto remains a separate decision.
