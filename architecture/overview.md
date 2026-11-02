# Architecture Overview

## Request path

`Open WebUI → LangGraph Agent → NVIDIA Dynamo → Model Workers`

Open WebUI is the user-facing interface. The Agent provides a stable OpenAI-compatible API, conversation orchestration, request classification, model selection, and tool coordination. Dynamo exposes available model workers and handles inference execution.

## Responsibilities

### Open WebUI
- User interface and conversation experience.
- Target final public model list: one logical model, `Auto`.
- Does not choose raw worker IDs.

### LangGraph Agent
- Classifies incoming requests (chat, vision, coding, reasoning, tool use).
- Consults Registry metadata and capabilities.
- Checks live Dynamo availability.
- Selects only approved and enabled models.
- Preserves conversation state through the existing PostgreSQL checkpointer.
- Returns a clear error when no eligible model exists.

### Model Registry
- Catalog of discovered models, curated metadata, capabilities, approval, and enablement.
- Does not control model lifecycle or load/unload workers.
- Discovery sync must not overwrite admin-curated data.

### NVIDIA Dynamo
- Runtime discovery and inference routing to model workers.
- Source of truth for whether a worker/model is currently available.

## Persistence

Registry tables are isolated by `model_registry_` prefix in the existing PostgreSQL database `langgraph`. Existing LangGraph checkpointer tables and conversation history must be preserved.

## Shared services and constraints

- Code Intelligence: port 8200.
- AstraMap API: port 8300.
- Control Center: port 5090.
- Agent API: port 8100.
- Heavy model workers are managed according to the existing scenario/resource policy; do not start additional heavy workers for Registry work.
