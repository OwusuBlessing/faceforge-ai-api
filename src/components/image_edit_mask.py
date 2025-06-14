import os
from enum import Enum
from typing import Optional, Union
import requests
import json
import time
import base64
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import secrets
from .mask import Masker
from config import Config
from PIL import Image
import io


class EditSection(Enum):
    HAIR = "hair"
    BACKGROUND = "background"
    CLOTHES = "clothes"

    
class ImageEditingPipeline:
    def __init__(self):
    
        self.masker = Masker(api_key=Config.SEGMIND_API_KEY)
        self.imagekit = ImageKit(
            private_key=Config.IMAGEKIT_PRIVATE_KEY,
            public_key= Config.IMAGEKIT_PUBLIC_KEY,
            url_endpoint=Config.IMAGEKIT_URL_ENDPOINT
        )
        
    async def upload_to_imagekit(self, file_path: str, user_id: str = "default") -> str:
        """Upload file to ImageKit and return the URL"""
        try:
            hex_string = secrets.token_hex(16)
            file_name = f"{user_id}_{hex_string}.jpg"
            
            with open(file_path, 'rb') as file:
                upload = self.imagekit.upload_file(
                    file=file,
                    file_name=file_name,
                    options=UploadFileRequestOptions(
                        response_fields=["is_private_file", "tags"],
                        tags=["masked_image"]
                    )
                )
            
            return upload.response_metadata.raw["url"]
        except Exception as e:
            raise Exception(f"Failed to upload to ImageKit: {str(e)}")

    async def create_mask(self, image_url: str, section: EditSection) -> str:
        """Create mask for the specified section using Segmind API"""
        # Generate mask using Masker class
        mask_bytes = self.masker.generate_mask(
            image=image_url,
            mask_type=section.value,
            grow_mask=10,
            threshold=0.2,
            invert_mask=False,
            return_mask=True,
            return_alpha=False
        )
        
        if not mask_bytes:
            raise Exception("Failed to generate mask")
            
        # Save mask temporarily
        temp_mask_path = f"temp_{section.value}_mask.png"
        with open(temp_mask_path, "wb") as f:
            f.write(mask_bytes)
            
        # Upload mask to ImageKit
        mask_url = await self.upload_to_imagekit(temp_mask_path)
        
        print(f"Mask URL: {mask_url}")
        # Clean up temporary file
        os.remove(temp_mask_path)
        
        return mask_url

    async def edit_image(self, original_image_url: str, masked_image_url: str, prompt: str) -> dict:
        """Edit the image using Segmind API and upload to ImageKit"""
        # Download and validate image dimensions
        response = requests.get(original_image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download original image: {response.status_code}")
            
        img = Image.open(io.BytesIO(response.content))
        width, height = img.size
        
        # Resize if image is too small
        if width < 256 or height < 256:
            # Calculate new dimensions while maintaining aspect ratio
            ratio = max(256/width, 256/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save resized image temporarily
            temp_resized_path = f"temp_resized_{int(time.time())}.jpg"
            img.save(temp_resized_path, "JPEG")
            
            # Upload resized image to ImageKit
            resized_url = await self.upload_to_imagekit(temp_resized_path)
            os.remove(temp_resized_path)
            
            # Use resized image URL instead
            original_image_url = resized_url
            
            # Update dimensions to match resized image
            width, height = new_width, new_height

        print(f"Image dimensions: {width}x{height}")

        # Download and resize mask to match image dimensions
        mask_response = requests.get(masked_image_url)
        if mask_response.status_code != 200:
            raise Exception(f"Failed to download mask: {mask_response.status_code}")
            
        mask_img = Image.open(io.BytesIO(mask_response.content))
        print(f"Original mask dimensions: {mask_img.size}")
        
        # Only resize if dimensions don't match
        if mask_img.size != (width, height):
            print(f"Resizing mask from {mask_img.size} to {width}x{height}")
            mask_img = mask_img.resize((width, height), Image.Resampling.LANCZOS)
            print(f"Resized mask dimensions: {mask_img.size}")
            
            # Save resized mask temporarily
            temp_mask_path = f"temp_resized_mask_{int(time.time())}.png"
            mask_img.save(temp_mask_path, "PNG")
            
            # Upload resized mask to ImageKit
            resized_mask_url = await self.upload_to_imagekit(temp_mask_path)
            os.remove(temp_mask_path)
        else:
            print("Mask dimensions already match image dimensions, skipping resize")
            resized_mask_url = masked_image_url

        url = "https://api.segmind.com/v1/flux-fill-pro"
        
        data = {
            'mask': resized_mask_url,
            'image': original_image_url,
            'seed': 965222,
            'steps': 50,
            'prompt': prompt,
            'guidance': 3,
            'output_format': "jpg",
            'safety_tolerance': 2,
            'prompt_upsampling': False
        }

        headers = {'x-api-key': Config.SEGMIND_API_KEY}
        response = requests.post(url, json=data, headers=headers)

        print(f"Edited image response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            raise Exception(f"Failed to edit image: {response.text}")
        
        # Save the response content temporarily
        temp_file_path = f"temp_edited_{int(time.time())}.jpg"
        with open(temp_file_path, "wb") as f:
            f.write(response.content)
            
        try:
            # Upload to ImageKit using our proper method
            imagekit_url = await self.upload_to_imagekit(temp_file_path)
            
            return {
                "original_image_url": original_image_url,
                "mask_image_url": resized_mask_url,
                "edited_image_url": imagekit_url
            }
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    async def process_image(self, image_url: str, section: EditSection, prompt: str, mask_url: Optional[str] = None) -> dict:
        """Main pipeline to process the image
        
        Args:
            image_url: URL of the original image
            section: Section to edit (hair, background, clothes)
            prompt: Text prompt for the edit
            mask_url: Optional URL of an existing mask. If provided, will use this instead of generating a new one
            
        Returns:
            dict: Dictionary containing mask_image_url and edited_image_url
        """
        # Step 1: Use existing mask or create new one
        masked_image_url = mask_url if mask_url else await self.create_mask(image_url, section)
        
        # Step 2: Edit the image using the mask and prompt
        return await self.edit_image(image_url, masked_image_url, prompt) 