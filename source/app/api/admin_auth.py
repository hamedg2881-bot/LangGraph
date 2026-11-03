import secrets

from fastapi import HTTPException, Request, status


async def require_admin(request: Request):
    settings = request.app.state.settings
    configured_key = settings.admin_api_key

    if configured_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is not configured",
        )

    authorization = request.headers.get("Authorization", "")
    scheme, separator, supplied_key = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not supplied_key
        or not secrets.compare_digest(
            configured_key.get_secret_value(),
            supplied_key,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
