import requests
import base64
from config import Config
from imagekitio import ImageKit
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

from config import Config
from PIL import Image
import io

# Initialize ImageKit
imagekit = ImageKit(
    private_key=Config.IMAGEKIT_PRIVATE_KEY,
    public_key=Config.IMAGEKIT_PUBLIC_KEY,
    url_endpoint=Config.IMAGEKIT_URL_ENDPOINT
)

def image_file_to_base64(image_path):
    """Convert an image file to base64 string."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')

def upload_to_imagekit(file_path: str, user_id: str = "default") -> str:
        """Upload file to ImageKit and return the URL"""
        try:
            hex_string = secrets.token_hex(16)
            file_name = f"{user_id}_{hex_string}.jpg"
            
            with open(file_path, 'rb') as file:
                upload = imagekit.upload_file(
                    file=file,
                    file_name=file_name,
                    options=UploadFileRequestOptions(
                        response_fields=["is_private_file", "tags"],
                        tags=["masked_image"]
                    )
                )
            
            return upload.response_metadata.raw["url"]
        except Exception as e:
            raise Exception(f"Failed to upload file to ImageKit: {str(e)}")

def edit_background(image_path: str, prompt: str, api_key: str = Config.DEEPAI_API_KEY) -> dict:
    """
    Edit image background using DeepAI's image editor API.
    
    Args:
        image_path (str): Local path to the image file
        prompt (str): Text prompt describing the background change
        api_key (str): DeepAI API key
        
    Returns:
        dict: API response containing the edited image
    """
    # First upload the image to ImageKit
    image_url = upload_to_imagekit(image_path)
    
    # Then use DeepAI to edit the background
    response = requests.post(
        "https://api.deepai.org/api/image-editor",
        data={
            'image': image_url,
            'text': prompt,
        },
        headers={'api-key': api_key}
    )
    return response.json()

# Example usage:
if __name__ == "__main__":
    # Example with local image path
    result = edit_background(
        image_path="data/sample_pics/sample.png",
        prompt="change background to a beach scene"
    )
    print(result)