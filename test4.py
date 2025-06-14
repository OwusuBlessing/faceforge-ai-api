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
    seed: Optional[int] = None
) -> str:
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
        str: Path to the generated video file
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
        download_url = status_response["url"]
        output_filename_base = status_response.get("asset_id", generation_id)
        output_filename = f"{output_filename_base}.mp4"
        logger.info(f"Generation complete. Downloading video from {download_url} to {output_filename}")
        try:
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(output_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Successfully downloaded video to {output_filename}")
            return output_filename
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download video: {e}")
            raise
        except IOError as e:
            logger.error(f"Failed to save video file: {e}")
            raise
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
        output_file = generate_video(
            image_url="https://example.com/image.jpg",
            audio_url="https://example.com/audio.mp3",
            text_prompt="A beautiful sunset over mountains"
        )
        print(f"Video generated successfully: {output_file}")

        # Advanced usage with all parameters
        output_file = generate_video(
            image_url="https://example.com/image.jpg",
            audio_url="https://example.com/audio.mp3",
            text_prompt="A beautiful sunset over mountains",
            aspect_ratio="9:16",  # Vertical video
            resolution="720p",
            duration=30.0,  # 30 seconds
            seed=42  # Fixed seed for reproducible results
        )
        print(f"Video generated successfully: {output_file}")
    except Exception as e:
        print(f"Error generating video: {e}")