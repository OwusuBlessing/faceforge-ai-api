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

class EditSection(Enum):
    HAIR = "hair"
    BACKGROUND = "background"
    CLOTHES = "clothes"

class Masker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.segmind.com/v1/automatic-mask-generator"
        self.headers = {'x-api-key': self.api_key}
        
    def _image_url_to_base64(self, image_url: str) -> str:
        """Convert an image URL to base64 string."""
        response = requests.get(image_url)
        image_data = response.content
        return base64.b64encode(image_data).decode('utf-8')
    
    def generate_mask(self, 
                  image: Union[str, bytes], 
                  mask_type: str = "hair",
                  threshold: float = 0.2,
                  invert_mask: bool = False,
                  return_mask: bool = True,
                  return_alpha: bool = False,
                  grow_mask: int = 10,
                  seed: int = 468685) -> bytes:
        """Generate a mask for the given image."""
        print(f"Generating {mask_type} mask...")
        
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            image_base64 = self._image_url_to_base64(image)
        else:
            raise ValueError("Only URL images are supported")
        
        data = {
            "prompt": mask_type,
            "image": image_base64,
            "threshold": threshold,
            "invert_mask": invert_mask,
            "return_mask": return_mask,
            "return_alpha": return_alpha,
            "grow_mask": grow_mask,
            "seed": seed,
            "base64": False
        }

        response = requests.post(self.base_url, json=data, headers=self.headers)

        if response.status_code == 200:
            print("✅ Mask generated successfully!")

            print(f"Mask size: {len(response.content)} bytes")
            return response.content
        
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return b""



# Example usage:
if __name__ == "__main__":
    # Initialize the masker with your API key
    masker = Masker(api_key="SG_28b00087ea064e64")
    
    try:
        # Check if sample.png exists
        import os
        if not os.path.exists("sample.png"):
            print("❌ Error: sample.png not found!")
            print("Please make sure sample.png exists in the current directory.")
        else:
            print("📸 Found sample.png, generating background mask...")
            
            # Generate a mask from the local file
            with open("sample.png", "rb") as f:
                image_bytes = f.read()
                mask = masker.generate_mask(
                    image=image_bytes,
                    mask_type="background"
                )
            
            # Save the mask if generation was successful
            if mask:
                output_file = "background_mask.png"
                with open(output_file, "wb") as f:
                    f.write(mask)
                print(f"💾 Mask saved as {output_file}")
                print(f"📊 Mask size: {len(mask)} bytes")
            else:
                print("❌ Failed to generate mask")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Alternative example with URL (uncomment to test)
    # print("\n🌐 Testing with URL...")
    # try:
    #     mask = masker.generate_mask(
    #         image="https://segmind-sd-models.s3.amazonaws.com/display_images/automask-ip.jpg",
    #         mask_type="hair"
    #     )
    #     
    #     if mask:
    #         with open("hair_mask.png", "wb") as f:
    #             f.write(mask)
    #         print("💾 Hair mask saved as hair_mask.png")
    # except Exception as e:
    #     print(f"❌ URL test failed: {e}")