# Architecture Decisions

## Confirmed decisions

1. Keep the architecture: Open WebUI → LangGraph Agent → NVIDIA Dynamo → Model Workers.
2. Open WebUI ultimately sees only logical model `Auto`.
3. Registry is metadata and policy storage, not a model lifecycle manager.
4. Dynamo is authoritative for live runtime discovery.
5. New discoveries are pending and disabled by default.
6. Approval, enablement, and runtime availability remain independent.
7. Registry tables live in existing PostgreSQL database `langgraph`, schema `public`, with prefix `model_registry_`.
8. Preserve all existing checkpointer tables and conversation history.
9. Use Psycopg 3 async pool; initialize Registry in FastAPI lifespan and attach services to `app.state`.
10. Protect all admin endpoints with a separate `ADMIN_API_KEY` Bearer token; use constant-time comparison and never log or expose the key.
11. Do not download/install/load/activate models through Registry.
12. Preserve Code Intelligence (8200), AstraMap (8300), Control Center (5090), and existing profile behavior.
13. Keep heavy model workers from competing for unified memory.
14. Model selection is request-scoped. Pass the selected model ID through LangGraph runtime configuration; do not rebuild the graph or replace the checkpointer per request.
15. The client-supplied `model` value must not bypass Registry approval, enablement, capability, or live-availability checks.
16. Perform live Dynamo discovery for selection and require all Registry eligibility conditions before selecting a model.
17. Classify requests into the required capability categories: `vision` when image input is present, `coding` for programming/code requests, and `chat` as the general fallback. Do not automatically grant capabilities to discovered models.
18. Keep `/v1/models` unchanged until request routing is implemented and tested; only then expose the logical `Auto` model.

## Request routing implementation plan

- Reuse the existing compiled graph and PostgreSQL checkpointer.
- Update the graph node to read the selected model ID from LangGraph `RunnableConfig` and instantiate the Dynamo chat model for that request.
- The API route resolves the request capability, reads Registry candidates, checks live Dynamo model discovery, and selects only an approved + enabled model with the required capability.
- Pass the selected model ID alongside the existing conversation `thread_id` in both streaming and non-streaming graph calls.
- Return a clear selection error when no eligible model exists; do not silently fall back to an unapproved or incapable model.
- Preserve current conversation/thread ID derivation and message conversion.

## Deferred decisions

- Exact coding-request classifier signals and precedence for mixed image/code requests.
- Runtime health validation beyond presence in Dynamo `/models`.
- Admin UI and richer audit metadata.

## Multi-model residency and resource management — confirmed direction
19. The system must support multiple registered/approved model workers; it must not require manual Compose edits to switch between Coder, Vision, and general chat.
20. Separate model eligibility from model residency: a model can remain approved and selectable in Registry while its weights are unloaded from accelerator memory.
21. Add a Model Manager responsible for worker lifecycle and residency decisions, using measured resource availability, per-model load footprint, active requests, queue depth, and recent usage.
22. Load a requested model on demand when resource budget permits. If capacity is insufficient, queue the request and consider only safely idle/unreferenced workers as eviction candidates.
23. Never unload a model with active requests or forcibly interrupt in-flight inference. Release only after the worker reports safe idle state.
24. Use a configurable memory reserve for runtime overhead, KV cache, vision activations, and transient load peaks; do not allocate the full reported free memory to model weights.
25. Keep Dynamo as the inference/runtime discovery layer, Registry as the approved catalog/policy layer, and LangGraph as the request orchestration layer. Model Manager coordinates lifecycle across them.
26. The desired policy is multi-model availability with a bounded set of resident workers, not necessarily all model weights resident simultaneously.
27. Before implementation, inspect the Dynamo worker lifecycle/control APIs supported by the deployed version and validate whether workers can be started/stopped independently while sharing one frontend, etcd, and NATS.
28. Do not implement Compose-based worker switching as the long-term manager. Compose remains deployment/bootstrap configuration; Model Manager should use a controlled worker lifecycle adapter.
29. No worker lifecycle behavior or deployment has been changed by recording this design direction.
