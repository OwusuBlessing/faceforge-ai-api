"""Handler file for RunPod serverless endpoints."""

import runpod
import asyncio
import multiprocessing
from src.components.avatar_theme import ThemeStyle, theme_generation
from src.components.image_edit_mask import ImageEditingPipeline, EditSection
from typing import Dict, Any, AsyncGenerator

# Initialize the image editing pipeline
image_pipeline = ImageEditingPipeline()

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
            
        # Send progress update
        runpod.serverless.progress_update(job, "Validating theme...")
        theme_enum = validate_theme(theme)
        
        # Send progress update
        runpod.serverless.progress_update(job, "Generating themed avatar...")
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
            
        # Send progress update
        runpod.serverless.progress_update(job, "Validating section...")
        section_enum = validate_edit_section(section)
        
        # Send progress update
        runpod.serverless.progress_update(job, "Processing image...")
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

async def handler(job: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Handler function that will be used to process jobs."""
    job_input = job["input"]
    process_type = job_input.get("process_type")

    if process_type == "avatar_theme":
        async for result in process_avatar_theme(job):
            yield result
    elif process_type == "image_edit":
        async for result in process_image_edit(job):
            yield result
    else:
        yield {
            "status": "error",
            "error": f"Invalid process_type. Must be either 'avatar_theme' or 'image_edit'"
        }

# Main execution block - required for multiprocessing on macOS/Windows
if __name__ == '__main__':
    # Add freeze_support for multiprocessing compatibility
    multiprocessing.freeze_support()
    
    # Start the serverless function
    runpod.serverless.start({"handler": handler})