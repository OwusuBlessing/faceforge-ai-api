# FaceForge AI FastAPI

This is the FastAPI implementation of the FaceForge AI API, providing endpoints for various AI-powered image and video processing capabilities.

## Getting Started

1. Install the required dependencies:
```bash
pip install fastapi uvicorn
```

2. Run the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## Endpoints

### 1. Avatar Theme Generation

Transforms an image into a themed avatar based on the specified theme.

**Endpoint:** `POST /avatar-theme`

**Valid Themes:**
- `realistic portrait`
- `anime`
- `cyberpunk`
- `toy`
- `ghibli`
- `emoji`

**Request Body:**
```json
{
    "api_key": "your-api-key-here",
    "image_url": "https://example.com/image.jpg",
    "theme": "anime"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "image_url": "https://example.com/generated_avatar.jpg"
    }
}
```

### 2. Image Edit

Edits specific sections of an image based on a text prompt.

**Endpoint:** `POST /image-edit`

**Valid Sections:**
- `hair`
- `background`
- `clothes`

**Request Body:**
```json
{
    "api_key": "your-api-key-here",
    "image_url": "https://example.com/image.jpg",
    "section": "background",
    "prompt": "A beautiful sunset over mountains",
    "mask_url": "https://example.com/mask.png"  // Optional
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "image_url": "https://example.com/edited_image.jpg"
    }
}
```

### 3. Video Generation

Generates a video from an image, audio, and text prompt using AI.

**Endpoint:** `POST /video-generation`

**Request Body:**
```json
{
    "api_key": "your-api-key-here",
    "image_url": "https://example.com/image.jpg",
    "audio_url": "https://example.com/audio.mp3",
    "text_prompt": "A beautiful sunset over mountains",
    "aspect_ratio": "16:9",  // Optional, default: "16:9"
    "resolution": "720p",    // Optional, default: "720p"
    "duration": 10.0,        // Optional
    "seed": 42              // Optional, default: 42
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "status": "complete",
        "video_url": "https://example.com/generated_video.mp4",
        "type": "video",
        "created_at": "2024-03-20T12:00:00Z"
    }
}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 500: Internal Server Error

Error responses follow this format:
```json
{
    "detail": "Error message description"
}
```

## Authentication

All endpoints require an API key for authentication. The API key must be included in the request body for every endpoint.

## Rate Limiting

Please note that this API may have rate limits depending on your subscription level. Contact support for more information about rate limits and quotas.

## Support

For any questions or issues, please contact support at support@faceforge.ai 