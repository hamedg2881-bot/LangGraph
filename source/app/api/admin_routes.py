import httpx

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.api.admin_auth import require_admin


router = APIRouter(
    prefix="/admin/models",
    tags=["Model Registry Admin"],
    dependencies=[Depends(require_admin)],
)

model_manager_router = APIRouter(
    prefix="/admin/model-manager",
    tags=["Model Manager"],
    dependencies=[Depends(require_admin)],
)


class ModelRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    display_name: str
    provider: str = "nvidia-dynamo"
    architecture: str | None = None
    quantization: str | None = None
    context_length: int | None = None
    capabilities: list[str] = ["chat"]
    notes: str | None = None


class ModelDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str | None = None



@router.post("", status_code=201)
async def register_model(payload: ModelRegistration, request: Request):
    model_id = payload.id.strip()
    display_name = payload.display_name.strip()
    if not model_id or len(model_id) > 200 or not display_name or len(display_name) > 200:
        raise HTTPException(status_code=422, detail="Invalid model id or display name")
    if payload.context_length is not None and payload.context_length < 1:
        raise HTTPException(status_code=422, detail="context_length must be positive")
    try:
        created = await request.app.state.registry.register_manual_model(
            model_id=model_id,
            display_name=display_name,
            provider=payload.provider.strip(),
            architecture=payload.architecture,
            quantization=payload.quantization,
            context_length=payload.context_length,
            capabilities=payload.capabilities,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not created:
        raise HTTPException(status_code=409, detail="Model already exists")
    return {
        "id": model_id,
        "approval_status": "pending",
        "is_enabled": False,
        "registration_source": "manual",
    }


@router.get("/runtime/queue")
async def runtime_queue(request: Request):
    return await request.app.state.model_manager.snapshot()


@router.get("")
async def list_models(request: Request):
    models = await request.app.state.registry.list_models()

    return {
        "data": [
            {
                "id": row[0],
                "display_name": row[1],
                "provider": row[2],
                "architecture": row[3],
                "quantization": row[4],
                "context_length": row[5],
                "approval_status": row[6],
                "is_enabled": row[7],
                "first_seen_at": row[8],
                "last_seen_at": row[9],
                "metadata": row[10],
                "capabilities": row[11],
            }
            for row in models
        ]
    }


@router.post("/sync")
async def sync_models(request: Request):
    settings = request.app.state.settings
    url = f"{settings.dynamo_base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {settings.dynamo_api_key.get_secret_value()}"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.dynamo_timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve models from Dynamo",
        ) from exc

    models = payload.get("data", [])
    if not isinstance(models, list):
        raise HTTPException(
            status_code=502,
            detail="Invalid model list returned by Dynamo",
        )

    await request.app.state.registry.sync_discovered_models(models)

    return {
        "discovered_count": len(models),
        "message": "Model discovery completed",
    }


@router.post("/{model_id}/approve")
async def approve_model(
    model_id: str,
    payload: ModelDecision,
    request: Request,
):
    updated = await request.app.state.registry.set_approval(
        model_id=model_id,
        approved=True,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"id": model_id, "approval_status": "approved"}


@router.post("/{model_id}/reject")
async def reject_model(
    model_id: str,
    payload: ModelDecision,
    request: Request,
):
    updated = await request.app.state.registry.set_approval(
        model_id=model_id,
        approved=False,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"id": model_id, "approval_status": "rejected"}


class ModelUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = None
    architecture: str | None = None
    quantization: str | None = None
    context_length: int | None = None
    capabilities: list[str] | None = None


@router.patch("/{model_id}")
async def update_model(
    model_id: str,
    payload: ModelUpdate,
    request: Request,
):
    fields = payload.model_dump(exclude_unset=True)
    capabilities = fields.pop("capabilities", None)

    if fields:
        updated = await request.app.state.registry.update_model(
            model_id=model_id,
            fields=fields,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Model not found")

    if capabilities is not None:
        updated = await request.app.state.registry.set_capabilities(
            model_id=model_id,
            capabilities=capabilities,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Model not found")

    return {"id": model_id, "updated": True}


@router.post("/{model_id}/enable")
async def enable_model(
    model_id: str,
    payload: ModelDecision,
    request: Request,
):
    updated = await request.app.state.registry.set_enabled(
        model_id=model_id,
        enabled=True,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"id": model_id, "is_enabled": True}


@router.post("/{model_id}/disable")
async def disable_model(
    model_id: str,
    payload: ModelDecision,
    request: Request,
):
    updated = await request.app.state.registry.set_enabled(
        model_id=model_id,
        enabled=False,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"id": model_id, "is_enabled": False}


@router.get("/{model_id}/status")
async def model_status(model_id: str, request: Request):
    models = await request.app.state.registry.list_models()
    model = next((row for row in models if row[0] == model_id), None)

    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    settings = request.app.state.settings
    url = f"{settings.dynamo_base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {settings.dynamo_api_key.get_secret_value()}"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.dynamo_timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        available = any(
            item.get("id") == model_id
            for item in payload.get("data", [])
            if isinstance(item, dict)
        )
        runtime_status = "available" if available else "unavailable"
    except (httpx.HTTPError, ValueError):
        runtime_status = "unknown"

    return {
        "id": model_id,
        "approval_status": model[6],
        "is_enabled": model[7],
        "runtime_status": runtime_status,
        "selectable": (
            model[6] == "approved"
            and model[7]
            and runtime_status == "available"
        ),
    }


@model_manager_router.get("/status")
async def model_manager_status(request: Request):
    queue = await request.app.state.model_manager.snapshot()
    return {
        **queue,
        "worker_lifecycle": {
            "supported": False,
            "adapter": "dynamo-compose",
            "reason": (
                "A supported graceful load/drain/unload control surface has not "
                "been validated for this bare-metal Dynamo 1.6.1 Compose deployment."
            ),
        },
    }


@model_manager_router.get("/queue")
async def model_manager_queue(request: Request):
    return await request.app.state.model_manager.snapshot()


@model_manager_router.post("/models/{model_id}/load", status_code=501)
async def load_model_not_supported(model_id: str):
    raise HTTPException(
        status_code=501,
        detail=(
            "Worker lifecycle is unavailable: the deployed Dynamo Compose "
            "lifecycle adapter has not been validated. No container was started."
        ),
    )


@model_manager_router.post("/models/{model_id}/unload", status_code=501)
async def unload_model_not_supported(model_id: str):
    raise HTTPException(
        status_code=501,
        detail=(
            "Worker lifecycle is unavailable: graceful drain and unload are not "
            "validated. No active inference or container was interrupted."
        ),
    )


@model_manager_router.post("/queue/{request_id}/cancel")
async def cancel_queued_request(request_id: str, request: Request):
    cancelled = await request.app.state.model_manager.cancel_queued(request_id)
    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail="Request is not queued or cannot be cancelled safely",
        )
    return {"id": request_id, "state": "cancelled"}
