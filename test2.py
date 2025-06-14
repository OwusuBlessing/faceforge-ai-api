import requests
import base64
from typing import Union, List


class Masker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.segmind.com/v1/automatic-mask-generator"
        self.headers = {'x-api-key': self.api_key}
        
    def _image_file_to_base64(self, image_path: str) -> str:
        """Convert an image file to base64 string."""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    
    def _image_url_to_base64(self, image_url: str) -> str:
        """Convert an image URL to base64 string."""
        response = requests.get(image_url)
        image_data = response.content
        return base64.b64encode(image_data).decode('utf-8')
    
    def _urls_to_base64(self, image_urls: List[str]) -> List[str]:
        """Convert multiple image URLs to base64 strings."""
        return [self._image_url_to_base64(url) for url in image_urls]
    
    def _decode_base64(self, base64_string: str) -> bytes:
        """Decode a base64 string back to bytes."""
        return base64.b64decode(base64_string)
    
    def load_image_to_base64(self, image_source: Union[str, bytes]) -> str:
        """
        Load an image from various sources and convert it to base64.
        
        Args:
            image_source: Can be:
                - A file path (str)
                - A URL (str starting with http:// or https://)
                - Direct base64 string (str)
                - Raw image bytes (bytes)
                
        Returns:
            str: Base64 encoded string of the image
        """
        if isinstance(image_source, bytes):
            return base64.b64encode(image_source).decode('utf-8')
        elif isinstance(image_source, str):
            if image_source.startswith(('http://', 'https://')):
                return self._image_url_to_base64(image_source)
            elif image_source.startswith('data:image'):  # Already base64
                return image_source
            else:  # Assume it's a file path
                return self._image_file_to_base64(image_source)
        else:
            raise ValueError("Unsupported image source type")
    
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
        
        image_base64 = self.load_image_to_base64(image)
        
        data = {
            "prompt": mask_type,
            "image": image_base64,
            "threshold": threshold,
            "invert_mask": invert_mask,
            "return_mask": return_mask,
            "return_alpha": return_alpha,
            "grow_mask": grow_mask,
            "seed": seed,
            "base64": False  # Let the API return image bytes
        }

        response = requests.post(self.base_url, json=data, headers=self.headers)

        if response.status_code == 200:
            print("✅ Mask generated successfully!")
            return response.content
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return b""


# Example usage:
if __name__ == "__main__":
    # Initialize the masker with your API key
    masker = Masker(api_key="SG_28b00087ea064e64")
    
    try:
        print("🌐 Testing with provided image URL...")
        image_url = "https://ik.imagekit.io/sz509xr3s/sample.png?updatedAt=1749597377172"
        
        mask = masker.generate_mask(
            image=image_url,
            mask_type="hair",
            grow_mask=10,
            threshold=0.2,
            invert_mask=False,
            return_mask=True,
            return_alpha=False
        )
        
        if mask:
            output_file = "hair_mask_from_url.png"
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