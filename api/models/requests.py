from pydantic import BaseModel, HttpUrl
from typing import Optional

class BaseRequest(BaseModel):
    api_key: str

class AvatarThemeRequest(BaseRequest):
    image_url: HttpUrl
    theme: str

class ImageEditRequest(BaseRequest):
    image_url: HttpUrl
    section: str
    prompt: str
    mask_url: Optional[HttpUrl] = None

class VideoGenerationRequest(BaseRequest):
    image_url: HttpUrl
    audio_url: HttpUrl
    text_prompt: str
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "720p"
    duration: Optional[float] = None
    seed: Optional[int] = 42 