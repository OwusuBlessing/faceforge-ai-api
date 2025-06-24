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
from urllib.parse import urlparse
from io import BytesIO
import urllib.parse
import mimetypes
import subprocess
import tempfile

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

def get_content_type_from_url(url: str, default_content_type: str = None) -> str:
    """Get the MIME type from URL path or default content type"""
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Try to guess content type from file extension
    mime_type, _ = mimetypes.guess_type(path)
    
    if mime_type is None:
        # Default content types based on file extension
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif ext in ['.png']:
            return 'image/png'
        elif ext in ['.mp3']:
            return 'audio/mpeg'
        elif ext in ['.wav']:
            return 'audio/wav'
        elif ext in ['.m4a']:
            return 'audio/mp4'
        elif ext in ['.aac']:
            return 'audio/aac'
        elif ext in ['.ogg']:
            return 'audio/ogg'
        else:
            return default_content_type or 'application/octet-stream'
    return mime_type

def validate_url_accessibility(url: str, file_type: str = "file") -> None:
    """Validate that a URL is accessible and provide helpful error messages for common issues"""
    if 's3.' in url or 'amazonaws.com' in url:
        logger.info(f"Validating S3 {file_type} URL: {url}")
        
        # Check for common S3 URL issues
        if '?' in url and 'X-Amz-' in url:
            logger.warning("Detected pre-signed S3 URL - these may expire quickly")
        elif not url.startswith('https://'):
            logger.warning("S3 URL should use HTTPS for security")
        
        # Provide helpful guidance for S3 URLs
        logger.info("S3 URL detected. Common issues:")
        logger.info("1. Pre-signed URLs may expire")
        logger.info("2. URLs may require specific authentication")
        logger.info("3. File may not exist or be accessible")
        logger.info("4. Bucket permissions may be restrictive")
    
    elif 'githubusercontent.com' in url:
        logger.info(f"GitHub raw content URL detected for {file_type}")
        # GitHub raw URLs are generally reliable
    else:
        logger.info(f"Standard URL detected for {file_type}: {url}")

async def start_hedra_generation(request_data: dict) -> str:
    """Start video generation with Hedra API and return generation ID"""
    try:
        api_key = Config.HEDRA_API_KEY
        if not api_key:
            raise ValueError("HEDRA_API_KEY not found in environment variables")

        session = Session(api_key=api_key)

        # Get model ID with proper error handling
        try:
            model_response = session.get("/models")
            model_response.raise_for_status()
            model_id = model_response.json()[0]["id"]
            logger.info(f"Retrieved model ID: {model_id}")
            model_id = "d1dd37a3-e39a-4854-a298-6510289f9cf2"  # Override with specific model
        except Exception as e:
            logger.error(f"Failed to get model ID: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve model ID: {str(e)}"
            )

        # Download and upload image
        image_url = request_data["image_url"]
        image_filename = os.path.basename(urlparse(image_url).path) or "input.jpg"
        logger.info(f"Downloading image from: {image_url}")
        
        # Validate URL accessibility
        validate_url_accessibility(image_url, "image")
        
        try:
            # Add headers to handle potential redirects and authentication
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; FaceForge-AI/1.0)',
                'Accept': 'image/*, */*'
            }
            
            image_response = requests.get(image_url, headers=headers, allow_redirects=True, timeout=30)
            image_response.raise_for_status()
            image_data = image_response.content
            image_content_type = image_response.headers.get("Content-Type", "image/jpeg")
            
            # Validate file size - image files should be larger than a few bytes
            if len(image_data) < 100:  # Less than 100 bytes is suspicious
                logger.error(f"Image file too small: {len(image_data)} bytes. This might be an error response.")
                logger.error(f"Response content: {image_data[:200]}")  # Log first 200 chars for debugging
                raise HTTPException(
                    status_code=400,
                    detail=f"Image file appears to be invalid or inaccessible. File size: {len(image_data)} bytes. "
                           f"This might be due to authentication issues, expired URLs, or the file not existing. "
                           f"Please check the image URL: {image_url}"
                )
            
            # Use our content type detection as fallback
            if not image_content_type or image_content_type == "application/octet-stream":
                image_content_type = get_content_type_from_url(image_url, "image/jpeg")
            
            # Enhanced image format detection and correction
            # Check file magic bytes to determine actual format
            if len(image_data) >= 4:
                magic_bytes = image_data[:4]
                
                # JPEG file signature: FF D8 FF
                if magic_bytes.startswith(b'\xff\xd8\xff'):
                    logger.info("Detected JPEG file by magic bytes")
                    image_content_type = "image/jpeg"
                    if not image_filename.lower().endswith(('.jpg', '.jpeg')):
                        image_filename = "image.jpg"
                
                # PNG file signature: 89 50 4E 47
                elif magic_bytes.startswith(b'\x89PNG'):
                    logger.info("Detected PNG file by magic bytes")
                    image_content_type = "image/png"
                    if not image_filename.lower().endswith('.png'):
                        image_filename = "image.png"
                
                # WebP file signature: RIFF....WEBP
                elif magic_bytes.startswith(b'RIFF') and len(image_data) > 12 and image_data[8:12] == b'WEBP':
                    logger.info("Detected WebP file by magic bytes")
                    image_content_type = "image/webp"
                    if not image_filename.lower().endswith('.webp'):
                        image_filename = "image.webp"
                
                # GIF file signature: GIF87a or GIF89a
                elif magic_bytes.startswith(b'GIF8'):
                    logger.info("Detected GIF file by magic bytes")
                    image_content_type = "image/gif"
                    if not image_filename.lower().endswith('.gif'):
                        image_filename = "image.gif"
            
            logger.info(f"Image downloaded: {len(image_data)} bytes, content-type: {image_content_type}, filename: {image_filename}")
            
            # Check if we need to convert the image format for Hedra compatibility
            # Hedra works best with JPEG and PNG formats
            if image_content_type not in ["image/jpeg", "image/jpg", "image/png"]:
                logger.info(f"Converting image from {image_content_type} to JPEG for Hedra compatibility")
                image_data, image_filename = convert_image_to_jpeg(image_data, image_filename)
                image_content_type = "image/jpeg"
                logger.info(f"Image converted to JPEG: {len(image_data)} bytes")
            
            # Additional validation for S3 URLs
            if 's3.' in image_url or 'amazonaws.com' in image_url:
                logger.info("Detected S3 URL - performing additional validation")
                # Check if response looks like an S3 error page
                if b'<Error>' in image_data or b'AccessDenied' in image_data or b'NoSuchKey' in image_data:
                    logger.error("S3 error detected in response")
                    raise HTTPException(
                        status_code=400,
                        detail=f"S3 access error. The image file may require authentication, "
                               f"the URL may have expired, or the file may not exist. "
                               f"Please check the S3 URL: {image_url}"
                    )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            if 's3.' in image_url or 'amazonaws.com' in image_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to access S3 image file: {str(e)}. "
                           f"This might be due to authentication issues, expired URLs, or the file not existing. "
                           f"Please check the S3 URL: {image_url}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image: {str(e)}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading image: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download image: {str(e)}"
            )

        # Create image asset
        logger.info("Creating image asset...")
        try:
            image_upload_response = session.post(
                "/assets",
                json={"name": image_filename, "type": "image"},
            )
            if not image_upload_response.ok:
                error_text = image_upload_response.text
                logger.error(f"Image asset creation failed: {image_upload_response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Image asset creation failed: {error_text}"
                )
            image_upload_response.raise_for_status()
            image_id = image_upload_response.json()["id"]
            logger.info(f"Image asset created with ID: {image_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create image asset: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create image asset: {str(e)}"
            )
        
        # Upload image file
        try:
            image_file = BytesIO(image_data)
            image_file.name = image_filename
            logger.info(f"Uploading image file: {image_filename}, size: {len(image_data)} bytes")
            logger.info(f"Upload content type: {image_content_type}")
            
            # Explicitly set content type to ensure it's recognized as image
            upload_response = session.post(
                f"/assets/{image_id}/upload", 
                files={"file": (image_filename, image_file, image_content_type)}
            )
            logger.info(f"Image upload response status: {upload_response.status_code}")
            
            if not upload_response.ok:
                error_text = upload_response.text
                logger.error(f"Image upload failed: {upload_response.status_code} - {error_text}")
                
                # If the upload failed due to unsupported format, try converting to JPEG
                if "unsupported" in error_text.lower() or "invalid" in error_text.lower():
                    logger.info("Attempting to convert image to JPEG format and retry upload")
                    converted_image_data, converted_filename = convert_image_to_jpeg(image_data, image_filename)
                    
                    if converted_image_data != image_data:  # Conversion was successful
                        logger.info("Retrying upload with converted JPEG file")
                        image_file = BytesIO(converted_image_data)
                        image_file.name = converted_filename
                        
                        retry_response = session.post(
                            f"/assets/{image_id}/upload", 
                            files={"file": (converted_filename, image_file, "image/jpeg")}
                        )
                        
                        if retry_response.ok:
                            logger.info("Image upload successful after conversion")
                            upload_response = retry_response
                        else:
                            logger.error(f"Image upload still failed after conversion: {retry_response.status_code} - {retry_response.text}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"Image upload failed even after format conversion: {retry_response.text}"
                            )
                    else:
                        # Conversion failed, raise original error
                        raise HTTPException(
                            status_code=400,
                            detail=f"Image upload failed: {error_text}"
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Image upload failed: {error_text}"
                    )
            
            upload_response.raise_for_status()
            logger.info("Image upload successful")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload image file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image file: {str(e)}"
            )

        # Download and upload audio
        audio_url = request_data["audio_url"]
        audio_filename = os.path.basename(urlparse(audio_url).path) or "input.mp3"
        logger.info(f"Downloading audio from: {audio_url}")
        
        # Validate URL accessibility
        validate_url_accessibility(audio_url, "audio")
        
        try:
            # Add headers to handle potential redirects and authentication
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; FaceForge-AI/1.0)',
                'Accept': 'audio/*, */*'
            }
            
            audio_response = requests.get(audio_url, headers=headers, allow_redirects=True, timeout=30)
            audio_response.raise_for_status()
            audio_data = audio_response.content
            audio_content_type = audio_response.headers.get("Content-Type", "audio/mpeg")
            
            # Validate file size - audio files should be larger than a few bytes
            if len(audio_data) < 100:  # Less than 100 bytes is suspicious
                logger.error(f"Audio file too small: {len(audio_data)} bytes. This might be an error response.")
                logger.error(f"Response content: {audio_data[:200]}")  # Log first 200 chars for debugging
                raise HTTPException(
                    status_code=400,
                    detail=f"Audio file appears to be invalid or inaccessible. File size: {len(audio_data)} bytes. "
                           f"This might be due to authentication issues, expired URLs, or the file not existing. "
                           f"Please check the audio URL: {audio_url}"
                )
            
            # Use our content type detection as fallback
            if not audio_content_type or audio_content_type == "application/octet-stream":
                audio_content_type = get_content_type_from_url(audio_url, "audio/mpeg")
            
            logger.info(f"Original audio content type from server: {audio_content_type}")
            logger.info(f"Audio file size: {len(audio_data)} bytes")
            
            # Additional validation for S3 URLs
            if 's3.' in audio_url or 'amazonaws.com' in audio_url:
                logger.info("Detected S3 URL - performing additional validation")
                # Check if response looks like an S3 error page
                if b'<Error>' in audio_data or b'AccessDenied' in audio_data or b'NoSuchKey' in audio_data:
                    logger.error("S3 error detected in response")
                    raise HTTPException(
                        status_code=400,
                        detail=f"S3 access error. The audio file may require authentication, "
                               f"the URL may have expired, or the file may not exist. "
                               f"Please check the S3 URL: {audio_url}"
                    )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download audio: {e}")
            if 's3.' in audio_url or 'amazonaws.com' in audio_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to access S3 audio file: {str(e)}. "
                           f"This might be due to authentication issues, expired URLs, or the file not existing. "
                           f"Please check the S3 URL: {audio_url}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download audio: {str(e)}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading audio: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download audio: {str(e)}"
            )
        
        # Fix audio filename and content type if needed
        if not audio_filename.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
            if 'audio/wav' in audio_content_type:
                audio_filename = "audio.wav"
            elif 'audio/mpeg' in audio_content_type or 'audio/mp3' in audio_content_type:
                audio_filename = "audio.mp3"
            elif 'audio/mp4' in audio_content_type or 'audio/m4a' in audio_content_type:
                audio_filename = "audio.m4a"
            elif 'audio/aac' in audio_content_type:
                audio_filename = "audio.aac"
            elif 'audio/ogg' in audio_content_type:
                audio_filename = "audio.ogg"
            else:
                audio_filename = "audio.mp3"  # Default fallback
                audio_content_type = "audio/mpeg"
        
        # Enhanced content type detection and correction
        # Check file magic bytes to determine actual format
        if len(audio_data) >= 4:
            magic_bytes = audio_data[:4]
            
            # WAV file signature: RIFF
            if magic_bytes.startswith(b'RIFF'):
                logger.info("Detected WAV file by magic bytes")
                audio_content_type = "audio/wav"
                if not audio_filename.lower().endswith('.wav'):
                    audio_filename = "audio.wav"
            
            # MP3 file signature: ID3 or MPEG sync
            elif magic_bytes.startswith(b'ID3') or magic_bytes.startswith(b'\xff\xfb') or magic_bytes.startswith(b'\xff\xf3'):
                logger.info("Detected MP3 file by magic bytes")
                audio_content_type = "audio/mpeg"
                if not audio_filename.lower().endswith('.mp3'):
                    audio_filename = "audio.mp3"
            
            # WebM file signature: EBML
            elif magic_bytes.startswith(b'\x1a\x45\xdf\xa3'):
                logger.info("Detected WebM file by magic bytes")
                # WebM can contain audio, but Hedra might not support it
                # Force it to be treated as audio/mpeg for compatibility
                audio_content_type = "audio/mpeg"
                if not audio_filename.lower().endswith('.mp3'):
                    audio_filename = "audio.mp3"
                logger.warning("WebM file detected - converting to MP3 format for Hedra compatibility")
        
        # Ensure content type is audio, not video - force audio/mpeg for any video content type
        if audio_content_type.startswith('video/'):
            logger.warning(f"Detected video content type for audio file: {audio_content_type}, forcing to audio/mpeg")
            audio_content_type = "audio/mpeg"
            if not audio_filename.lower().endswith('.mp3'):
                audio_filename = "audio.mp3"
        
        # Additional safety check - if content type is still not audio, force it
        if not audio_content_type.startswith('audio/'):
            logger.warning(f"Non-audio content type detected: {audio_content_type}, forcing to audio/mpeg")
            audio_content_type = "audio/mpeg"
            if not audio_filename.lower().endswith('.mp3'):
                audio_filename = "audio.mp3"
        
        # Final validation - ensure filename extension matches content type
        if audio_content_type == "audio/wav" and not audio_filename.lower().endswith('.wav'):
            audio_filename = "audio.wav"
        elif audio_content_type == "audio/mpeg" and not audio_filename.lower().endswith('.mp3'):
            audio_filename = "audio.mp3"
        elif audio_content_type == "audio/mp4" and not audio_filename.lower().endswith('.m4a'):
            audio_filename = "audio.m4a"
        
        # Check if we need to convert the audio format for Hedra compatibility
        # Hedra seems to have issues with certain audio formats, so convert to MP3 if needed
        if audio_content_type not in ["audio/mpeg", "audio/mp3"]:
            logger.info(f"Converting audio from {audio_content_type} to MP3 for Hedra compatibility")
            audio_data, audio_filename = convert_audio_to_mp3(audio_data, audio_filename)
            audio_content_type = "audio/mpeg"
            logger.info(f"Audio converted to MP3: {len(audio_data)} bytes")
        
        logger.info(f"Final audio content type: {audio_content_type}, filename: {audio_filename}")
        logger.info(f"Audio downloaded: {len(audio_data)} bytes, content-type: {audio_content_type}, filename: {audio_filename}")

        # Create audio asset
        logger.info("Creating audio asset...")
        try:
            audio_upload_response = session.post(
                "/assets", json={"name": audio_filename, "type": "audio"}
            )
            if not audio_upload_response.ok:
                error_text = audio_upload_response.text
                logger.error(f"Audio asset creation failed: {audio_upload_response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Audio asset creation failed: {error_text}"
                )
            audio_upload_response.raise_for_status()
            audio_id = audio_upload_response.json()["id"]
            logger.info(f"Audio asset created with ID: {audio_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create audio asset: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create audio asset: {str(e)}"
            )
        
        # Upload audio file
        try:
            audio_file = BytesIO(audio_data)
            audio_file.name = audio_filename
            logger.info(f"Uploading audio file: {audio_filename}, size: {len(audio_data)} bytes")
            logger.info(f"Upload content type: {audio_content_type}")
            
            # Explicitly set content type to ensure it's recognized as audio
            audio_upload_response = session.post(
                f"/assets/{audio_id}/upload", 
                files={"file": (audio_filename, audio_file, audio_content_type)}
            )
            logger.info(f"Audio upload response status: {audio_upload_response.status_code}")
            
            if not audio_upload_response.ok:
                error_text = audio_upload_response.text
                logger.error(f"Audio upload failed: {audio_upload_response.status_code} - {error_text}")
                
                # If the upload failed due to unsupported format, try converting to MP3
                if "unsupported audio mime type" in error_text.lower() or "unsupported" in error_text.lower():
                    logger.info("Attempting to convert audio to MP3 format and retry upload")
                    converted_audio_data, converted_filename = convert_audio_to_mp3(audio_data, audio_filename)
                    
                    if converted_audio_data != audio_data:  # Conversion was successful
                        logger.info("Retrying upload with converted MP3 file")
                        audio_file = BytesIO(converted_audio_data)
                        audio_file.name = converted_filename
                        
                        retry_response = session.post(
                            f"/assets/{audio_id}/upload", 
                            files={"file": (converted_filename, audio_file, "audio/mpeg")}
                        )
                        
                        if retry_response.ok:
                            logger.info("Audio upload successful after conversion")
                            audio_upload_response = retry_response
                        else:
                            logger.error(f"Audio upload still failed after conversion: {retry_response.status_code} - {retry_response.text}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"Audio upload failed even after format conversion: {retry_response.text}"
                            )
                    else:
                        # Conversion failed, raise original error
                        raise HTTPException(
                            status_code=400,
                            detail=f"Audio upload failed: {error_text}"
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Audio upload failed: {error_text}"
                    )
            
            audio_upload_response.raise_for_status()
            logger.info("Audio upload successful")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload audio file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload audio file: {str(e)}"
            )

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
        try:
            generation_response = session.post("/generations", json=generation_request_data)
            if not generation_response.ok:
                error_text = generation_response.text
                logger.error(f"Generation creation failed: {generation_response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Generation creation failed: {error_text}"
                )
            generation_response.raise_for_status()
            generation_data = generation_response.json()
            logger.info(f"Generation started successfully: {generation_data}")
            return generation_data["id"]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start generation: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start generation: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start Hedra generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Hedra generation: {str(e)}"
        )

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
        # Clean up the job_id - remove any URL encoding and extra quotes
        job_id = urllib.parse.unquote(job_id)
        job_id = job_id.strip('"\'')  # Remove any surrounding quotes
        
        logger.info(f"Checking status for job ID: {job_id}")
        
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
        
        if status_response.status_code == 422:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid job ID format: {job_id}"
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

def convert_audio_to_mp3(audio_data: bytes, original_filename: str) -> tuple[bytes, str]:
    """
    Convert audio data to MP3 format using ffmpeg if available.
    Returns (converted_data, new_filename)
    """
    try:
        # Check if ffmpeg is available
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("ffmpeg not available, cannot convert audio format")
            return audio_data, original_filename
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(original_filename)[1], delete=False) as input_file:
            input_file.write(audio_data)
            input_path = input_file.name
        
        output_path = input_path + ".mp3"
        
        try:
            # Convert to MP3
            cmd = [
                'ffmpeg', '-i', input_path, 
                '-acodec', 'libmp3lame', '-ab', '128k',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    converted_data = f.read()
                
                logger.info(f"Successfully converted audio to MP3: {len(converted_data)} bytes")
                return converted_data, "audio.mp3"
            else:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                return audio_data, original_filename
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error during audio conversion: {e}")
        return audio_data, original_filename

def convert_image_to_jpeg(image_data: bytes, original_filename: str) -> tuple[bytes, str]:
    """
    Convert image data to JPEG format using ffmpeg if available.
    Returns (converted_data, new_filename)
    """
    try:
        # Check if ffmpeg is available
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("ffmpeg not available, cannot convert image format")
            return image_data, original_filename
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(original_filename)[1], delete=False) as input_file:
            input_file.write(image_data)
            input_path = input_file.name
        
        output_path = input_path + ".jpg"
        
        try:
            # Convert to JPEG
            cmd = [
                'ffmpeg', '-i', input_path, 
                '-q:v', '2',  # High quality JPEG
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    converted_data = f.read()
                
                logger.info(f"Successfully converted image to JPEG: {len(converted_data)} bytes")
                return converted_data, "image.jpg"
            else:
                logger.error(f"ffmpeg image conversion failed: {result.stderr}")
                return image_data, original_filename
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error during image conversion: {e}")
        return image_data, original_filename