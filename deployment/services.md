# Deployment and Services

## LangGraph Agent
- systemd unit: langgraph-agent.service
- Working directory: /opt/ai/langgraph-agent
- Environment file: /opt/ai/langgraph-agent/config/agent.env (host-only, secret-bearing)
- Uvicorn command: .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8100 --log-level info
- Agent API port: 8100.
- Open WebUI connects to LangGraph Agent and uses logical model name Auto; it must not connect directly to model workers.

## Dynamo
- Dynamo frontend API: http://127.0.0.1:8013/v1.
- Coder worker is intentionally paused to free resources for the Qwen 3.8-VL worker. This is a planned single-heavy-worker operating sequence.
- Latest combined Compose status: dynamo-etcd healthy, dynamo-nats running, dynamo-frontend running on host port 8013, dynamo-vllm-vision38 running.
- Latest Dynamo /v1/models response exposed qwen38-vl only.
- Latest authenticated Registry response exposed qwen38-vl only; approved, enabled, capabilities chat and vision.

### Verified Compose provenance from container labels
- dynamo-frontend: project deploy; service dynamo-frontend; working directory /opt/ai/dynamo/deploy; config files compose.yaml, compose.vision38.yaml, compose.gateway.yaml.
- dynamo-vllm-vision38: project deploy; service dynamo-vllm-vision38; working directory /opt/ai/dynamo/deploy; config files compose.yaml, compose.vision38.yaml.
- The earlier inspection of compose.yaml + compose.vision.yaml was not the active Vision38 stack. Its service list (etcd, nats, dynamo-vllm, dynamo-vllm-vision) must not be used to infer the current running deployment.
- Inspect exact active Compose files and archive their exact contents before editing or switching workers.
- No Compose files or containers were changed during the provenance inspection.

### Archived active Compose overlays
- Exact active worker definition: deployment/compose.vision38.yaml.
- Exact active frontend definition: deployment/compose.gateway.yaml.
- Both files were copied from host output on 2026-11-02 and archived without operational edits.
- Vision38 serves qwen38-vl from /models/qwen38, mapped read-only from /opt/ai/models/Qwen3.8-27B-NVFP4; max model length 32768, max sequences 2, max batched tokens 4096, GPU memory utilization 0.35, FP8 KV cache, multimodal images limited to 2 and videos disabled.
- Frontend publishes container port 8000 as host port 8013.
- Base compose.yaml is referenced by the active containers but its exact contents are not yet archived.

## Related services to preserve
| Service | Port | Notes |
|---|---:|---|
| Control Center | 5090 | Existing coding/image scenario control |
| Code Intelligence | 8200 | Must remain available |
| AstraMap API | 8300 | Must remain available |
| LangGraph Agent | 8100 | OpenAI-compatible API |

## Secret handling
The live config/agent.env must remain on the host and must never be committed. It contains PostgreSQL credentials and API keys. The ADMIN_API_KEY must never be committed. Store only sanitized templates.

## Operational rules
- Do not restart, stop, rebuild, install, download, or activate services/models without explicit user approval.
- Do not run Coder and Vision heavy workers together without explicit approval and a verified resource plan.
- Verify service startup logs, runtime model discovery, Registry eligibility, and health after an approved worker switch.
