from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from api.models.requests import VideoGenerationRequest
from api.models.responses import VideoGenerationResponse, JobSubmissionResponse, JobStatusResponse
from api.dependencies.auth import get_api_key
from src.components.hedra_video import generate_video
import uuid
import asyncio
from typing import Dict, Any
from datetime import datetime
import logging
import os
import time
import requests
from config import Config

router = APIRouter(
    prefix="/video-generation",
    tags=["video"]
)

logger = logging.getLogger(__name__)

class Session(requests.Session):
    def __init__(self, api_key: str):
        super().__init__()
        self.base_url: str = "https://api.hedra.com/web-app/public"
        self.headers["x-api-key"] = api_key

    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        request.url = f"{self.base_url}{request.url}"
        return super().prepare_request(request)

async def start_hedra_generation(request_data: dict) -> str:
    """Start video generation with Hedra API and return generation ID"""
    try:
        api_key = Config.HEDRA_API_KEY
        if not api_key:
            raise ValueError("HEDRA_API_KEY not found in environment variables")

        session = Session(api_key=api_key)

        # Get model ID
        model_id = session.get("/models").json()[0]["id"]
        model_id = "d1dd37a3-e39a-4854-a298-6510289f9cf2"

        # Download and upload image
        image_response = requests.get(request_data["image_url"])
        image_response.raise_for_status()
        image_data = image_response.content

        image_upload_response = session.post(
            "/assets",
            json={"name": "input_image.jpg", "type": "image"},
        )
        image_id = image_upload_response.json()["id"]
        session.post(f"/assets/{image_id}/upload", files={"file": image_data}).raise_for_status()

        # Download and upload audio
        audio_response = requests.get(request_data["audio_url"])
        audio_response.raise_for_status()
        audio_data = audio_response.content

        audio_id = session.post(
            "/assets", json={"name": "input_audio.mp3", "type": "audio"}
        ).json()["id"]
        session.post(f"/assets/{audio_id}/upload", files={"file": audio_data}).raise_for_status()

        # Prepare generation request
        generation_request_data = {
            "type": "video",
            "ai_model_id": model_id,
            "start_keyframe_id": image_id,
            "audio_id": audio_id,
            "generated_video_inputs": {
                "text_prompt": request_data["text_prompt"],
                "resolution": request_data["resolution"],
                "aspect_ratio": request_data["aspect_ratio"],
            },
        }

        # Add optional parameters
        if request_data["duration"] is not None:
            generation_request_data["generated_video_inputs"]["duration_ms"] = int(request_data["duration"] * 1000)
        if request_data["seed"] is not None:
            generation_request_data["generated_video_inputs"]["seed"] = request_data["seed"]

        # Start generation
        generation_response = session.post("/generations", json=generation_request_data).json()
        return generation_response["id"]

    except Exception as e:
        logger.error(f"Failed to start Hedra generation: {str(e)}")
        raise

@router.post("/submit", response_model=JobSubmissionResponse)
async def submit_video_generation_job(
    request: VideoGenerationRequest,
    _: str = Depends(get_api_key)
):
    """Submit a video generation job and return Hedra generation ID as job ID"""
    try:
        request_data = {
            "image_url": str(request.image_url),
            "audio_url": str(request.audio_url),
            "text_prompt": request.text_prompt,
            "aspect_ratio": request.aspect_ratio,
            "resolution": request.resolution,
            "duration": request.duration,
            "seed": request.seed
        }
        
        # Start generation and get Hedra generation ID
        hedra_generation_id = await start_hedra_generation(request_data)
        
        return {
            "job_id": hedra_generation_id,  # Use Hedra generation ID as our job ID
            "status": "queued",
            "message": "Video generation job submitted successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to submit video generation job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit job: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,  # This is actually the Hedra generation ID
    _: str = Depends(get_api_key)
):
    """Get the status of a video generation job by querying Hedra API directly"""
    try:
        api_key = Config.HEDRA_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="HEDRA_API_KEY not configured"
            )

        session = Session(api_key=api_key)
        
        # Get status from Hedra API
        status_response = session.get(f"/generations/{job_id}/status")
        
        if status_response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        status_response.raise_for_status()
        hedra_data = status_response.json()
        
        hedra_status = hedra_data["status"]
        
        # Map Hedra status to our status
        if hedra_status == "queued":
            our_status = "queued"
        elif hedra_status == "processing":
            our_status = "processing"
        elif hedra_status == "complete":
            our_status = "completed"
        elif hedra_status == "error":
            our_status = "failed"
        else:
            our_status = "processing"  # Default for unknown statuses
        
        # Prepare response
        response_data = {
            "job_id": job_id,
            "status": our_status,
            "created_at": hedra_data.get("created_at"),
            "progress": str(hedra_data.get("progress", 0.0))
        }
        
        # Add result if completed
        if our_status == "completed" and hedra_data.get("url"):
            response_data["result"] = {
                "status": hedra_status,
                "video_url": hedra_data["url"],
                "type": hedra_data.get("type"),
                "created_at": hedra_data.get("created_at")
            }
            response_data["completed_at"] = hedra_data.get("updated_at") or hedra_data.get("created_at")
        
        # Add error if failed
        if our_status == "failed":
            error_msg = hedra_data.get('error_message', 'Unknown error occurred')
            response_data["error"] = f"Generation failed: {error_msg}"
            response_data["completed_at"] = hedra_data.get("updated_at") or hedra_data.get("created_at")
        
        # Add started_at if processing
        if our_status == "processing":
            response_data["started_at"] = hedra_data.get("updated_at") or hedra_data.get("created_at")
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check job status: {str(e)}"
        )

# Keep the original endpoint for backward compatibility
@router.post("", response_model=VideoGenerationResponse)
async def process_video_generation(
    request: VideoGenerationRequest,
    _: str = Depends(get_api_key)
):
    """Process video generation request (synchronous - original endpoint)"""
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