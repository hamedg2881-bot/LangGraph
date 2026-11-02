# Deployment and Services

## LangGraph Agent
- systemd unit: langgraph-agent.service
- Working directory: /opt/ai/langgraph-agent
- Environment file: /opt/ai/langgraph-agent/config/agent.env (host-only, secret-bearing)
- Uvicorn command: .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8100 --log-level info
- Agent API port: 8100.
- Open WebUI connects to LangGraph Agent and uses the logical model name Auto; it must not connect directly to model workers.

## Dynamo
- Dynamo frontend API: http://127.0.0.1:8013/v1.
- The Coder worker was intentionally paused/removed from the active worker set to free resources for the Qwen 3.8-VL worker. This is a planned single-heavy-worker operating sequence.
- Latest combined Compose status on 2026-11-02 showed:
  - dynamo-etcd: healthy.
  - dynamo-nats: running.
  - dynamo-frontend: running, host port 8013 mapped to container port 8000.
  - dynamo-vllm-vision38: running.
- Latest Dynamo /v1/models response exposed qwen38-vl only.
- Latest authenticated Registry response exposed qwen38-vl only; approved, enabled, capabilities chat and vision.
- Before editing deployment, inspect the effective Compose configuration. The combined compose ps output listed service keys dynamo-frontend and dynamo-vllm-vision38, while grep of the named files showed keys dynamo-vllm and dynamo-vllm-vision. This mismatch is unresolved.

## Related services to preserve
| Service | Port | Notes |
|---|---:|---|
| Control Center | 5090 | Existing coding/image scenario control |
| Code Intelligence | 8200 | Must remain available |
| AstraMap API | 8300 | Must remain available |
| LangGraph Agent | 8100 | OpenAI-compatible API |

## Secret handling
The live config/agent.env must remain on the host and must never be committed. It contains PostgreSQL credentials and API keys. The separate ADMIN_API_KEY is protected on the host. This repository stores only a sanitized template.

## Operational rules
- Do not restart, stop, rebuild, install, download, or activate services/models without explicit user approval.
- Do not run the Coder and Vision heavy workers together without explicit approval and a verified resource plan.
- Verify service startup logs, runtime model discovery, Registry eligibility, and health after an approved worker switch.
