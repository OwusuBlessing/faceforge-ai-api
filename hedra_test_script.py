import argparse
import os
import time
import logging
from dotenv import load_dotenv
from typing import override
import mimetypes

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


def get_content_type(file_path: str) -> str:
    """Get the MIME type of a file based on its extension"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # Default content types based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif ext in ['.png']:
            return 'image/png'
        elif ext in ['.mp3']:
            return 'audio/mpeg'
        elif ext in ['.wav']:
            return 'audio/wav'
        elif ext in ['.m4a']:
            return 'audio/mp4'
        else:
            return 'application/octet-stream'
    return mime_type


def main():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("HEDRA_API_KEY")

    if not api_key:
        # If api_key is still None, it means it wasn't set in the environment
        # AND it wasn't found/loaded from the .env file.
        print("Error: HEDRA_API_KEY not found in environment variables or .env file.")
        return

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate video using Hedra API.")
    parser.add_argument(
        '--aspect_ratio',
        type=str,
        required=True,
        choices=['16:9', '9:16', '1:1'],
        help='Aspect ratio for the video (e.g., 16:9, 9:16, 1:1).'
    )
    parser.add_argument(
        '--resolution',
        type=str,
        required=True,
        choices=['540p', '720p'],
        help='Resolution for the video (e.g., 540p, 720p).'
    )
    parser.add_argument(
        '--text_prompt',
        type=str,
        required=True,
        help='Text prompt describing the desired video content.'
    )
    parser.add_argument(
        '--audio_file',
        type=str,
        required=True,
        help='Path to the input audio file.'
    )
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Path to the input image file.'
    )
    parser.add_argument(
        '--duration',
        type=float,
        required=False,
        default=None,
        help='Optional duration for the video in seconds (float).'
    )
    parser.add_argument(
        '--seed',
        type=int,
        required=False,
        default=None,
        help='Optional seed for generation (integer).'
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate file existence
    if not os.path.exists(args.image):
        print(f"Error: Image file not found: {args.image}")
        return
    
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file not found: {args.audio_file}")
        return

    # Initialize Hedra client
    session = Session(api_key=api_key)

    logger.info("testing against %s", session.base_url)
    
    # Get model ID
    try:
        model_response = session.get("/models")
        model_response.raise_for_status()
        model_id = model_response.json()[0]["id"]
        logger.info("got model id %s", model_id)
        model_id = "d1dd37a3-e39a-4854-a298-6510289f9cf2"  # Override with specific model
    except Exception as e:
        logger.error(f"Failed to get model ID: {e}")
        return

    # Get content types
    image_content_type = get_content_type(args.image)
    audio_content_type = get_content_type(args.audio_file)
    
    logger.info(f"Image content type: {image_content_type}")
    logger.info(f"Audio content type: {audio_content_type}")

    # Upload image
    try:
        image_response = session.post(
            "/assets",
            json={"name": os.path.basename(args.image), "type": "image"},
        )
        if not image_response.ok:
            logger.error(
                "error creating image asset: %d %s",
                image_response.status_code,
                image_response.text,
            )
            return
        image_id = image_response.json()["id"]
        
        with open(args.image, "rb") as f:
            upload_response = session.post(
                f"/assets/{image_id}/upload", 
                files={"file": (os.path.basename(args.image), f, image_content_type)}
            )
            upload_response.raise_for_status()
        logger.info("uploaded image %s", image_id)
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        return

    # Upload audio
    try:
        audio_response = session.post(
            "/assets", 
            json={"name": os.path.basename(args.audio_file), "type": "audio"}
        )
        if not audio_response.ok:
            logger.error(
                "error creating audio asset: %d %s",
                audio_response.status_code,
                audio_response.text,
            )
            return
        audio_id = audio_response.json()["id"]
        
        with open(args.audio_file, "rb") as f:
            upload_response = session.post(
                f"/assets/{audio_id}/upload", 
                files={"file": (os.path.basename(args.audio_file), f, audio_content_type)}
            )
            upload_response.raise_for_status()
        logger.info("uploaded audio %s", audio_id)
    except Exception as e:
        logger.error(f"Failed to upload audio: {e}")
        return

    # Prepare generation request
    generation_request_data = {
        "type": "video",
        "ai_model_id": model_id,
        "start_keyframe_id": image_id,
        "audio_id": audio_id,
        "generated_video_inputs": {
            "text_prompt": args.text_prompt,
            "resolution": args.resolution,
            "aspect_ratio": args.aspect_ratio,
        },
    }

    # Add optional parameters if provided
    if args.duration is not None:
        generation_request_data["generated_video_inputs"]["duration_ms"] = int(args.duration * 1000)
    if args.seed is not None:
        generation_request_data["generated_video_inputs"]["seed"] = args.seed

    # Start generation
    try:
        generation_response = session.post("/generations", json=generation_request_data)
        generation_response.raise_for_status()
        generation_data = generation_response.json()
        logger.info(f"Generation started: {generation_data}")
        generation_id = generation_data["id"]
    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        return

    # Poll for status
    while True:
        try:
            status_response = session.get(f"/generations/{generation_id}/status")
            status_response.raise_for_status()
            status_data = status_response.json()
            logger.info("status response %s", status_data)
            status = status_data["status"]

            # --- Check for completion or error to break the loop ---
            if status in ["complete", "error"]:
                break

            time.sleep(5)
        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            return

    # --- Process final status (download or log error) ---
    if status == "complete" and status_data.get("url"):
        download_url = status_data["url"]
        # Use asset_id for filename if available, otherwise use generation_id
        output_filename_base = status_data.get("asset_id", generation_id)
        output_filename = f"{output_filename_base}.mp4"
        logger.info(f"Generation complete. Downloading video from {download_url} to {output_filename}")
        try:
            # Use a fresh requests get, not the session, as the URL is likely presigned S3
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status() # Check if the request was successful
                with open(output_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Successfully downloaded video to {output_filename}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download video: {e}")
        except IOError as e:
            logger.error(f"Failed to save video file: {e}")
    elif status == "error":
        logger.error(f"Video generation failed: {status_data.get('error_message', 'Unknown error')}")
    else:
        # This case might happen if loop breaks unexpectedly or API changes
        logger.warning(f"Video generation finished with status '{status}' but no download URL was found.")


if __name__ == "__main__":
    main() 