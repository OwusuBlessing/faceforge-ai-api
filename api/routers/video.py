from fastapi import APIRouter, Depends, HTTPException
from api.models.requests import VideoGenerationRequest
from api.models.responses import VideoGenerationResponse
from api.dependencies.auth import verify_api_key
from src.components.hedra_video import generate_video

router = APIRouter(
    prefix="/video-generation",
    tags=["video"]
)

@router.post("", response_model=VideoGenerationResponse)
async def process_video_generation(request: VideoGenerationRequest = Depends(verify_api_key)):
    """Process video generation request."""
    try:
        result = generate_video(
            image_url=str(request.image_url),
            audio_url=str(request.audio_url),
            text_prompt=request.text_prompt,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            duration=request.duration,
            seed=request.seed
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 