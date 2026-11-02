# Deployment and Services

## LangGraph Agent

- systemd unit: `langgraph-agent.service`
- Working directory: `/opt/ai/langgraph-agent`
- Environment file: `/opt/ai/langgraph-agent/config/agent.env` (host-only, secret-bearing)
- Uvicorn command: `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8100 --log-level info`
- Restart policy: systemd service configured with automatic restart.
- Agent API port: 8100.

## Related services to preserve

| Service | Port | Notes |
|---|---:|---|
| Control Center | 5090 | Existing coding/image scenario control |
| Code Intelligence | 8200 | Must remain available |
| AstraMap API | 8300 | Must remain available |
| LangGraph Agent | 8100 | OpenAI-compatible API |

Dynamo endpoint configured for Agent: `http://127.0.0.1:8013/v1`.

## Secret handling

The live `config/agent.env` must remain on the host and must never be committed. It contains PostgreSQL credentials and API keys. The separate `ADMIN_API_KEY` is 64 hex characters and is protected by file mode 600 on the host. This repository stores only a blank template.

## Operational caution

Do not restart, stop, rebuild, install, or download services/models without explicit user approval. Verify service startup logs and health after an approved restart.
