import httpx


class ModelSelectionError(Exception):
    pass


def required_capability(messages):
    text_parts = []
    has_image = False

    def inspect_content(value):
        nonlocal has_image
        if isinstance(value, str):
            text_parts.append(value)
        elif isinstance(value, dict):
            kind = str(value.get("type", "")).lower()
            if kind in {"image", "image_url", "input_image"} or "image_url" in value or "image" in value:
                has_image = True
            for child in value.values():
                if isinstance(child, (dict, list, str)):
                    inspect_content(child)
        elif isinstance(value, list):
            for child in value:
                inspect_content(child)

    for message in messages:
        if message.role in ("user", "human"):
            inspect_content(message.content)

    if has_image:
        return "vision"

    text = "\n".join(text_parts).lower()
    coding_signals = (
        "```", "def ", "class ", "function ", "select ", "insert ", "update ",
        "delete ", "python", "javascript", "typescript", "c#", "asp.net", "sql",
        "کدنویسی", "برنامه نویسی", "برنامه‌نویسی", "دیباگ", "کامپایل",
        "تابع", "کلاس", "کد بنویس", "کد را", "کد رو",
    )
    return "coding" if any(signal in text for signal in coding_signals) else "chat"


async def select_model(registry, settings, messages):
    capability = required_capability(messages)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.dynamo_base_url.rstrip('/')}/models",
                headers={
                    "Authorization": (
                        f"Bearer {settings.dynamo_api_key.get_secret_value()}"
                    )
                },
            )
            response.raise_for_status()
            runtime_models = response.json().get("data", [])
    except (httpx.HTTPError, ValueError, AttributeError, TypeError) as exc:
        raise ModelSelectionError("Model provider unavailable") from exc

    runtime_ids = {
        item.get("id")
        for item in runtime_models
        if isinstance(item, dict) and item.get("id")
    }

    try:
        registry_models = await registry.list_models()
    except Exception as exc:
        raise ModelSelectionError("Model registry unavailable") from exc

    for model in registry_models:
        model_id, approval_status, is_enabled, capabilities = (
            model[0], model[6], model[7], model[11] or []
        )
        if (
            approval_status == "approved"
            and is_enabled
            and model_id in runtime_ids
            and capability in capabilities
        ):
            return model_id

    raise ModelSelectionError(
        f"No approved and enabled runtime model supports capability: {capability}"
    )
