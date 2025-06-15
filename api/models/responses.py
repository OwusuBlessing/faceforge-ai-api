from pydantic import BaseModel, HttpUrl
from typing import Optional, Any
from datetime import datetime

class BaseResponse(BaseModel):
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None

class AvatarThemeResponse(BaseResponse):
    data: dict[str, str]

class ImageEditResponse(BaseResponse):
    data: dict[str, Optional[Any]]

class VideoGenerationResponse(BaseResponse):
    data: dict[str, str | str | datetime] 