# Change Log

## 2026-11-02 — Initial repository documentation
- Created project notebook structure for LangGraph Agent on DGX Spark.
- Recorded architecture, confirmed decisions, current status, and roadmap.
- Added sanitized Registry schema and deployment environment template.
- Recorded successful Registry startup, admin authentication, and health checks.
- No production host files or secrets were changed by this documentation commit.

## 2026-11-02 — Admin API verification
- Confirmed authenticated `GET /admin/models` returns HTTP 200 with a `data` array.
- Confirmed `qwen38-vl` remains pending, disabled, and has no assigned capabilities.
- No model approval, enablement, or capability mutation performed.

## 2026-11-02 — Request-scoped model routing design
- Recorded the request capability categories: vision, coding, and chat.
- Chose per-request model selection through LangGraph runtime configuration.
- Preserved the existing compiled graph, PostgreSQL checkpointer, and conversation thread IDs.
- Required Registry approval, enablement, live Dynamo discovery, and capability match before selection.
- Deferred changing `/v1/models` to `Auto` until routing is implemented and tested.
- No server code or runtime configuration changed in this documentation update.
