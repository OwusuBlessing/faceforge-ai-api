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



class VideoGenerationRequest(BaseModel):
    image_url: HttpUrl
    audio_url: HttpUrl
    text_prompt: str
    aspect_ratio: str = "16:9"
    resolution: str = "720p"
    duration: Optional[float] = None
    seed: Optional[int] = 42
    
    class Config:
        # Example for API documentation
        schema_extra = {
            "example": {
                "image_url": "https://example.com/image.jpg",
                "audio_url": "https://example.com/audio.mp3",
                "text_prompt": "A beautiful sunset over mountains",
                "aspect_ratio": "16:9",
                "resolution": "720p",
                "duration": 10.0,
                "seed": 42
            }
        }