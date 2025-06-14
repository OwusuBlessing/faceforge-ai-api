from fastapi import APIRouter, Depends, HTTPException
from api.models.requests import ImageEditRequest
from api.models.responses import ImageEditResponse
from api.dependencies.auth import verify_api_key
from api.dependencies.validators import validate_edit_section
from src.components.image_edit_mask import ImageEditingPipeline

router = APIRouter(
    prefix="/image-edit",
    tags=["image"]
)

# Initialize the image editing pipeline
image_pipeline = ImageEditingPipeline()

@router.post("", response_model=ImageEditResponse)
async def process_image_edit(request: ImageEditRequest = Depends(verify_api_key)):
    """Process image editing request."""
    try:
        section_enum = validate_edit_section(request.section)
        result = await image_pipeline.process_image(
            image_url=str(request.image_url),
            section=section_enum,
            prompt=request.prompt,
            mask_url=str(request.mask_url) if request.mask_url else None
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