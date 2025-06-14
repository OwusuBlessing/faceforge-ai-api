"""Handler file for RunPod serverless endpoints."""

import runpod
import asyncio
import multiprocessing
from src.components.avatar_theme import ThemeStyle, theme_generation
from src.components.image_edit_mask import ImageEditingPipeline, EditSection
from src.components.hedra_video import generate_video
from typing import Dict, Any, AsyncGenerator
from config import Config

# Initialize the image editing pipeline
image_pipeline = ImageEditingPipeline()

def validate_api_key(api_key: str) -> bool:
    """Validate if the provided API key matches the configured key."""
    return api_key == Config.API_KEY_ACCESS

def validate_theme(theme: str) -> ThemeStyle:
    """Validate and convert theme string to ThemeStyle enum."""
    try:
        return ThemeStyle(theme.lower())
    except ValueError:
        valid_themes = [t.value for t in ThemeStyle]
        raise ValueError(f"Invalid theme. Must be one of: {valid_themes}")

def validate_edit_section(section: str) -> EditSection:
    """Validate and convert section string to EditSection enum."""
    try:
        return EditSection(section.lower())
    except ValueError:
        valid_sections = [s.value for s in EditSection]
        raise ValueError(f"Invalid section. Must be one of: {valid_sections}")

async def process_avatar_theme(job: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Process avatar theme generation request."""
    try:
        job_input = job["input"]
        image_url = job_input.get("image_url")
        theme = job_input.get("theme")
        
        if not image_url:
            yield {
                "status": "error",
                "error": "image_url is required"
            }
            return
            
        if not theme:
            yield {
                "status": "error",
                "error": "theme is required"
            }
            return
            
        theme_enum = validate_theme(theme)
        result = theme_generation(image_url=image_url, theme=theme_enum)
        
        yield {
            "status": "success",
            "data": result
        }
    except Exception as e:
        yield {
            "status": "error",
            "error": str(e)
        }

async def process_image_edit(job: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Process image editing request."""
    try:
        job_input = job["input"]
        image_url = job_input.get("image_url")
        section = job_input.get("section")
        prompt = job_input.get("prompt")
        mask_url = job_input.get("mask_url")  # Optional
        
        if not image_url:
            yield {
                "status": "error",
                "error": "image_url is required"
            }
            return
            
        if not section:
            yield {
                "status": "error",
                "error": "section is required"
            }
            return
            
        if not prompt:
            yield {
                "status": "error",
                "error": "prompt is required"
            }
            return
            
        section_enum = validate_edit_section(section)
        result = await image_pipeline.process_image(
            image_url=image_url,
            section=section_enum,
            prompt=prompt,
            mask_url=mask_url
        )
        
        yield {
            "status": "success",
            "data": result
        }
    except Exception as e:
        yield {
            "status": "error",
            "error": str(e)
        }

async def process_video_generation(job: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Process video generation request."""
    try:
        job_input = job["input"]
        image_url = job_input.get("image_url")
        audio_url = job_input.get("audio_url")
        text_prompt = job_input.get("text_prompt")
        
        # Optional parameters with defaults
        aspect_ratio = job_input.get("aspect_ratio", "16:9")
        resolution = job_input.get("resolution", "720p")
        duration = job_input.get("duration")
        seed = job_input.get("seed", 42)
        
        if not image_url:
            yield {
                "status": "error",
                "error": "image_url is required"
            }
            return
            
        if not audio_url:
            yield {
                "status": "error",
                "error": "audio_url is required"
            }
            return
            
        if not text_prompt:
            yield {
                "status": "error",
                "error": "text_prompt is required"
            }
            return
            
        result = generate_video(
            image_url=image_url,
            audio_url=audio_url,
            text_prompt=text_prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            duration=duration,
            seed=seed
        )
        
        yield {
            "status": "success",
            "data": result
        }
    except Exception as e:
        yield {
            "status": "error",
            "error": str(e)
        }

async def async_handler(job: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Handler function that will be used to process jobs."""
    job_input = job["input"]
    
    # Validate API key
    api_key = job_input.get("api_key")
    if not api_key:
        yield {
            "status": "error",
            "error": "API key is required"
        }
        return
        
    if not validate_api_key(api_key):
        yield {
            "status": "error",
            "error": "Invalid API key"
        }
        return
    
    process_type = job_input.get("process_type")

    if process_type == "avatar_theme":
        #runpod.serverless.progress_update(job, "Processing avatar theme generation...")
        async for result in process_avatar_theme(job):
            yield result
    elif process_type == "image_edit":
        #runpod.serverless.progress_update(job, "Processing image edit...")
        async for result in process_image_edit(job):
            yield result
    elif process_type == "video_generation":
        #runpod.serverless.progress_update(job, "Processing video generation...")
        async for result in process_video_generation(job):
            yield result
    else:
        yield {
            "status": "error",
            "error": f"Invalid process_type. Must be either 'avatar_theme', 'image_edit', or 'video_generation'"
        }


    # Start the serverless function

# Start the Serverless function when the script is run
runpod.serverless.start({
    "handler": async_handler,
    "return_aggregate_stream": True
})