from fastapi import APIRouter, Depends, HTTPException
from api.models.requests import AvatarThemeRequest
from api.models.responses import AvatarThemeResponse
from api.dependencies.auth import get_api_key
from api.dependencies.validators import validate_theme
from src.components.avatar_theme import theme_generation

router = APIRouter(
    prefix="/avatar-theme",
    tags=["avatar"]
)

@router.post("", response_model=AvatarThemeResponse)
async def process_avatar_theme(
    request: AvatarThemeRequest,
    _: str = Depends(get_api_key)
):
    """Process avatar theme generation request."""
    try:
        theme_enum = validate_theme(request.theme)
        result = theme_generation(image_url=str(request.image_url), theme=theme_enum)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 