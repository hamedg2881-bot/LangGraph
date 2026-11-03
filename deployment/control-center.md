# DGX Spark Control Center

## Existing deployment (verified 2026-11-03)

- systemd unit: `dgx-control-center.service`
- Status: active
- Application: DGX Spark Control Center
- Runtime: .NET 10
- Published assembly: `/opt/ai/control-center/publish/ControlCenter.dll`
- Working directory: `/opt/ai/control-center/publish`
- Host port: 5090
- Health endpoint: `GET /api/health`
- Verified health response: status `ok`

## Existing API surface observed

- `GET /api/health`
- `GET /api/profiles`
- `GET /api/status`
- Earlier documented endpoints include history, events, and profile switching; their current availability must be rechecked before relying on them.

## Legacy configuration found

The current profile API returns `coding` and `image` profiles and service definitions for `qwen-coder` and `qwen36-vl`. Their health URLs use ports 8010 and 8012. These are legacy values and are not authoritative for the current Dynamo frontend/runtime, whose host API is on port 8013.

The status API reports host resource metrics. On 2026-11-03 it reported 121.69 GiB total memory, 9.47 GiB available, and 112.21 GiB used. This is a historical snapshot, not a live value.

## Agreed direction

Extend this existing Control Center in place. Do not create a parallel dashboard.

The UI should ultimately present:
1. Model catalog and capabilities from the LangGraph Registry.
2. Approval and enablement state from Registry.
3. Actual runtime/readiness state from Dynamo and the Agent.
4. Host memory/resource information.
5. Model selection and lifecycle controls through the existing architecture, with safe request draining/queueing policies.

LangGraph chooses the best eligible model for each request. Dynamo is the inference/runtime layer. Registry is the catalog and policy layer. Open WebUI exposes only `Auto`.

Each model must be independently runnable. Simultaneous execution/residency of heavy models is not required.

## Change safety

- Preserve existing Control Center features and service.
- Do not edit or restart the service until its source/UI and API implementation have been inspected.
- Do not treat legacy profile health URLs as current Dynamo runtime status.
- Do not commit secrets, credentials, live environment files, database contents, or model weights.
