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


## 2026-11-03 — Control Center and sequential model execution

30. Reuse and extend the existing DGX Spark Control Center; do not create a parallel dashboard.
31. The Control Center remains the administrative UI. It should consume LangGraph Registry for the catalog and Dynamo/LangGraph runtime APIs for live model status and lifecycle actions.
32. Every registered model should be independently runnable through the shared architecture. Simultaneous execution or residency of large models is not a requirement.
33. LangGraph selects the best eligible model for each request. Dynamo provides the model runtime; Registry records model metadata, capabilities, approval, and enablement.
34. Keep Open WebUI limited to the logical Auto model.
35. Existing Control Center profile definitions are legacy and currently refer to qwen-coder/qwen36-vl health URLs on ports 8010/8012. Do not treat those URLs as authoritative for the current Dynamo runtime on port 8013.
36. Do not change the running Control Center or model workers until the existing source/UI and current APIs have been inspected and a focused change is approved.


## 2026-11-04 — Unified model management contract

37. Model Registry, Model Manager, Runtime Management, and Monitoring are one integrated control-plane deliverable, with responsibilities separated across Agent, Dynamo, and the existing Control Center.
38. Registry manual registration is metadata-only and defaults to pending/disabled; discovery must never download, install, load, activate, approve, enable, or overwrite curated policy.
39. Every inference must acquire a request lease and release it only after the full inference/stream has actually stopped; no active lease may be forcibly interrupted for eviction.
40. Queue records and request leases must be durable in additive tables in the existing PostgreSQL database; never modify LangGraph checkpointer tables.
41. Model residency is independent from approval, enablement, and Dynamo discovery. Memory admission must reserve headroom for OS, runtime, KV cache, vision activations, and transient load peaks.
42. Worker eviction is drain-first and permitted only after active leases and worker operations reach zero and the runtime confirms safe idle state.
43. Do not assume a bare-metal Dynamo 1.6.1 load/unload HTTP API from Kubernetes Operator/Planner concepts. Validate the deployed lifecycle control surface and implement a gated adapter; no direct Docker/systemd stop/start from the UI.
44. The existing Control Center has no admin-session authentication. Registry and Model Manager mutations must not be exposed through it until server-side authentication, CSRF protections as applicable, validation, and audit logging are implemented.
45. Monitoring may show only measured values from real APIs/telemetry; unimplemented queue, residency, and lifecycle states must be explicitly unavailable, never simulated.
46. The four areas must be delivered as one coherent integration, but implementation is gated by exact source capture, additive DB migration, queue/lease tests, Dynamo lifecycle validation, and authenticated UI integration.
