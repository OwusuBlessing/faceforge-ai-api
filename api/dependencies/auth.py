from fastapi import HTTPException, Depends
from api.models.requests import BaseRequest
from api.core.config import get_settings, Settings

def validate_api_key(api_key: str, settings: Settings) -> bool:
    """Validate if the provided API key matches the configured key."""
    return api_key == settings.API_KEY_ACCESS

async def verify_api_key(request: BaseRequest, settings: Settings = Depends(get_settings)):
    """Dependency to verify API key for all endpoints."""
    if not validate_api_key(request.api_key, settings):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return request 