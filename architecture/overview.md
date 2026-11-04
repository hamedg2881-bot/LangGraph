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

## Multi-model residency management

The target is a catalog of multiple approved models with resource-aware residency, rather than a single manually switched worker.

### Model Manager responsibilities
- Track each model's lifecycle state: registered, approved, unloaded, loading, ready, busy, unloading, or failed.
- Track measured memory use and conservative load estimates, active request references, last-used time, and queue demand.
- Load an eligible model on demand when the resource budget allows.
- Keep frequently used models resident when doing so does not violate the configured memory reserve.
- When memory is constrained, select only idle models with no active request references for safe unloading.
- Queue requests when no safe eviction or load is currently possible; never terminate in-flight requests to reclaim memory.
- Publish lifecycle state back to Registry/Agent and confirm live worker availability through Dynamo.

### Resource policy
- Distinguish model approval from residency. Unloaded models remain approved and available for future scheduling.
- Budget for weights, KV cache, runtime overhead, multimodal activations, and temporary loading peaks.
- Use hysteresis/minimum residency and cooldown windows to avoid repeatedly loading and unloading models under fluctuating demand.
- Treat memory figures as measured estimates and validate actual worker startup and memory after each lifecycle action.

### Runtime topology
- Keep one shared Dynamo frontend, etcd, and NATS plane.
- Run model workers as independently managed workers that register with the shared Dynamo discovery plane.
- Do not expose a separate host-facing frontend port for each model worker.
- Compose is bootstrap/deployment configuration, not the permanent model scheduler. A lifecycle adapter must be validated against the deployed Dynamo version before automation.



## General Assistant product objective

The Agent is intended to be a high-quality, all-purpose assistant, not merely a thin proxy to a model. It must understand intent, preserve conversation context, route internally to approved capabilities, execute real tools, and return reliable natural responses. Open WebUI continues to expose only `Auto`; users should not need to select workers or tools. Persian RTL and multilingual use are first-class requirements. The detailed product acceptance contract is maintained in [General Assistant quality requirements](assistant-quality.md).
