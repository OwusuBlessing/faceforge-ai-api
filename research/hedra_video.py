import requests
import time
import os
from typing import Optional

class HedraAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://mercury.dev.dream-ai.com/api"
        self.api_key = api_key
        self.headers = {'X-API-KEY': api_key}

    def test_connection(self) -> bool:
        """Test if the API key is valid by making a ping request."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/ping",
                headers=self.headers
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"API connection test failed: {e}")
            return False

    def upload_audio(self, audio_file_path: str) -> Optional[str]:
        """Upload audio file and return the URL."""
        try:
            if not os.path.exists(audio_file_path):
                print(f"Error: Audio file not found at {audio_file_path}")
                return None
                
            print(f"Attempting to upload audio file: {audio_file_path}")
            with open(audio_file_path, 'rb') as audio_file:
                response = requests.post(
                    f"{self.base_url}/v1/audio",
                    headers=self.headers,
                    files={'file': audio_file}
                )
                if response.status_code == 403:
                    print(f"Error: Access forbidden. Response details: {response.text}")
                    print("Please check if your API key has the necessary permissions for audio uploads.")
                response.raise_for_status()
                return response.json()["url"]
        except requests.exceptions.RequestException as e:
            print(f"Error uploading audio: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response details: {e.response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error uploading audio: {e}")
            return None

    def upload_image(self, image_file_path: str, aspect_ratio: str = "1:1") -> Optional[str]:
        """Upload image file and return the URL."""
        try:
            with open(image_file_path, 'rb') as image_file:
                response = requests.post(
                    f"{self.base_url}/v1/portrait",
                    headers=self.headers,
                    params={'aspect_ratio': aspect_ratio},
                    files={'file': image_file}
                )
                response.raise_for_status()
                return response.json()["url"]
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None

    def generate_character_video(self, image_url: str, audio_url: str) -> Optional[str]:
        """Generate character video and return project ID."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/characters",
                headers=self.headers,
                json={
                    "avatarImage": image_url,
                    "audioSource": "audio",
                    "voiceUrl": audio_url
                }
            )
            response.raise_for_status()
            return response.json().get("project_id")
        except Exception as e:
            print(f"Error generating video: {e}")
            return None

    def check_project_status(self, project_id: str) -> Optional[dict]:
        """Check project status and return status information."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/projects/{project_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error checking project status: {e}")
            return None

def main():
    from config import Config
    # Replace with your actual API key
    API_KEY = Config.HEDRA_API_KEY
    
    # Initialize the API client
    hedra = HedraAPI(API_KEY)
    
    # Test API connection first
    print("Testing API connection...")
    if not hedra.test_connection():
        print("API connection test failed. Please check your API key.")
        return
    
    # File paths - replace with your actual file paths
    image_path = "data/sample_pics/img8.jpeg"
    audio_path = "data/sample_pics/sam_voice.mp3"
    
    # Step 1: Upload audio
    print("Uploading audio...")
    audio_url = hedra.upload_audio(audio_path)
    if not audio_url:
        print("Failed to upload audio")
        return
    
    # Step 2: Upload image
    print("Uploading image...")
    image_url = hedra.upload_image(image_path)
    if not image_url:
        print("Failed to upload image")
        return
    
    # Step 3: Generate character video
    print("Generating character video...")
    project_id = hedra.generate_character_video(image_url, audio_url)
    if not project_id:
        print("Failed to generate video")
        return
    
    # Step 4: Check project status
    print("Checking project status...")
    while True:
        status = hedra.check_project_status(project_id)
        if not status:
            print("Failed to check project status")
            break
            
        print(f"Project status: {status.get('status', 'unknown')}")
        
        # If the video is ready, print the URL and break
        if status.get('status') == 'completed':
            print(f"Video URL: {status.get('video_url')}")
            break
            
        # Wait for 10 seconds before checking again
        time.sleep(10)

if __name__ == "__main__":
    main()
