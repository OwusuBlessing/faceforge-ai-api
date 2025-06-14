import os
import time
import logging
from dotenv import load_dotenv
from typing import override, Optional

import requests

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


class Session(requests.Session):
    def __init__(self, api_key: str):
        super().__init__()

        self.base_url: str = "https://api.hedra.com/web-app/public"
        self.headers["x-api-key"] = api_key

    @override
    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        request.url = f"{self.base_url}{request.url}"

        return super().prepare_request(request)


def generate_video(
    image_url: str,
    audio_url: str,
    text_prompt: str,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration: Optional[float] = None,
    seed: Optional[int] = 42
) -> dict:
    """
    Generate a video using the Hedra API.
    
    Args:
        image_url (str): URL of the input image
        audio_url (str): URL of the input audio
        text_prompt (str): Text prompt describing the desired video content
        aspect_ratio (str, optional): Aspect ratio for the video. Defaults to "16:9"
        resolution (str, optional): Resolution for the video. Defaults to "720p"
        duration (float, optional): Duration for the video in seconds. Defaults to None
        seed (int, optional): Seed for generation. Defaults to None
    
    Returns:
        dict: Dictionary containing status, video URL, type and creation timestamp
    """
    # Load environment variables from .env file
    from config import Config
    
    api_key = Config.HEDRA_API_KEY

    if not api_key:
        raise ValueError("Error: HEDRA_API_KEY not found in environment variables or .env file.")

    # Initialize Hedra client
    session = Session(api_key=api_key)

    logger.info("testing against %s", session.base_url)
    model_id = session.get("/models").json()[0]["id"]
    logger.info("got model id %s", model_id)
    model_id = "d1dd37a3-e39a-4854-a298-6510289f9cf2"

    # Download image from URL
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    image_data = image_response.content

    # Upload image
    image_upload_response = session.post(
        "/assets",
        json={"name": "input_image.jpg", "type": "image"},
    )
    if not image_upload_response.ok:
        logger.error(
            "error creating image: %d %s",
            image_upload_response.status_code,
            image_upload_response.json(),
        )
    image_id = image_upload_response.json()["id"]
    session.post(f"/assets/{image_id}/upload", files={"file": image_data}).raise_for_status()
    logger.info("uploaded image %s", image_id)

    # Download audio from URL
    audio_response = requests.get(audio_url)
    audio_response.raise_for_status()
    audio_data = audio_response.content

    # Upload audio
    audio_id = session.post(
        "/assets", json={"name": "input_audio.mp3", "type": "audio"}
    ).json()["id"]
    session.post(f"/assets/{audio_id}/upload", files={"file": audio_data}).raise_for_status()
    logger.info("uploaded audio %s", audio_id)

    generation_request_data = {
        "type": "video",
        "ai_model_id": model_id,
        "start_keyframe_id": image_id,
        "audio_id": audio_id,
        "generated_video_inputs": {
            "text_prompt": text_prompt,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
        },
    }

    # Add optional parameters if provided
    if duration is not None:
        generation_request_data["generated_video_inputs"]["duration_ms"] = int(duration * 1000)
    if seed is not None:
        generation_request_data["generated_video_inputs"]["seed"] = seed

    generation_response = session.post(
        "/generations", json=generation_request_data
    ).json()
    logger.info(generation_response)
    generation_id = generation_response["id"]
    
    while True:
        status_response = session.get(f"/generations/{generation_id}/status").json()
        logger.info("status response %s", status_response)
        status = status_response["status"]

        if status in ["complete", "error"]:
            break

        time.sleep(5)

    if status == "complete" and status_response.get("url"):
        return {
            "status": status,
            "video_url": status_response["url"],
            "type": status_response["type"],
            "created_at": status_response["created_at"]
        }
    elif status == "error":
        error_msg = status_response.get('error_message', 'Unknown error')
        logger.error(f"Video generation failed: {error_msg}")
        raise Exception(f"Video generation failed: {error_msg}")
    else:
        raise Exception(f"Video generation finished with status '{status}' but no download URL was found.")





# Example usage:
if __name__ == "__main__":
    try:
        # Basic usage with required parameters only
        result = generate_video(
            image_url="https://ik.imagekit.io/6pxd8st0ugi/default_a3a8152eacb9d355553350e524ef5ca3_XN6sZbZnB.jpg",
            audio_url="https://raw.githubusercontent.com/OwusuBlessing/faceforge-ai-api/master/data/sample_pics/sam_voice.mp3",
            text_prompt="A beautiful sunset over mountains"
        )
        print(f"Video generation result: {result}")

    except Exception as e:
        print(f"Error generating video: {e}")