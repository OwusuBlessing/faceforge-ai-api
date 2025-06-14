from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class BaseResponse(BaseModel):
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None

class AvatarThemeResponse(BaseResponse):
    data: dict[str, HttpUrl]

class ImageEditResponse(BaseResponse):
    data: dict[str, HttpUrl]

class VideoGenerationResponse(BaseResponse):
    data: dict[str, str | HttpUrl | datetime] 