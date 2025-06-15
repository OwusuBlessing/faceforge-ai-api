from fastapi import HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from api.models.requests import BaseRequest
from api.core.config import get_settings, Settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """Validate API key from header"""
    if not api_key_header or not api_key_header.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "API key is missing or invalid."}
        )
    
    token = api_key_header.split(' ')[1]
    settings = get_settings()
    if token != settings.API_KEY_ACCESS:
        raise HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "API key does not match."}
        )
    
    return token

async def verify_api_key(request: BaseRequest, settings: Settings = Depends(get_settings)):
    """Dependency to verify API key for all endpoints."""
    if not validate_api_key(request.api_key, settings):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return request 