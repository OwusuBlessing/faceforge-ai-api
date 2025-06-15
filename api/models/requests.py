from pydantic import BaseModel, HttpUrl
from typing import Optional

class BaseRequest(BaseModel):
    pass

class AvatarThemeRequest(BaseRequest):
    image_url: str
    theme: str

class ImageEditRequest(BaseRequest):
    image_url: str 
    section: str
    prompt: str
    mask_url: Optional[str] = None

class VideoGenerationRequest(BaseRequest):
    image_url: str
    audio_url: str
    text_prompt: str
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "720p"
    duration: Optional[float] = None
    seed: Optional[int] = 42 