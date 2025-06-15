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

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class JobSubmissionResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Any] = None  # The video generation result when completed
    error: Optional[str] = None   # Error message when failed
    progress:str