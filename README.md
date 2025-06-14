# FaceForge AI API Handler

This handler provides endpoints for various AI-powered image and video processing capabilities including avatar theme generation, image editing, and video generation.

## API Endpoints

All endpoints accept POST requests with a JSON payload containing a `process_type` and specific parameters for each process type.

### Common Response Format

All responses follow this format:
```json
{
    "status": "success" | "error",
    "data": { ... } | null,
    "error": "error message" | null
}
```

## Process Types

### 1. Avatar Theme Generation

Transforms an image into a themed avatar based on the specified theme.

**Valid Themes:**
- `realistic portrait`
- `anime`
- `cyberpunk`
- `toy`
- `ghibli`
- `emoji`

**Payload:**
```json
{
    "input": {
        "api_key": "your-api-key-here",
        "process_type": "avatar_theme",
        "image_url": "https://example.com/image.jpg",
        "theme": "anime"  // Must be one of the valid themes listed above
    }
}
```

**Sample Success Response:**
```json
{
    "status": "success",
    "data": {
        "image_url": "https://example.com/generated_avatar.jpg"
    }
}
```

**Sample Error Response:**
```json
{
    "status": "error",
    "error": "Invalid theme. Must be one of: ['realistic portrait', 'anime', 'cyberpunk', 'toy', 'ghibli', 'emoji']"
}
```

### 2. Image Edit

Edits specific sections of an image based on a text prompt.

**Valid Sections:**
- `hair`
- `background`
- `clothes`

**Payload:**
```json
{
    "input": {
        "api_key": "your-api-key-here",
        "process_type": "image_edit",
        "image_url": "https://example.com/image.jpg",
        "section": "background",  // Must be one of the valid sections listed above
        "prompt": "A beautiful sunset over mountains",
        "mask_url": "https://example.com/mask.png"  // Optional
    }
}
```

**Sample Success Response:**
```json
{
    "status": "success",
    "data": {
        "image_url": "https://example.com/edited_image.jpg"
    }
}
```

**Sample Error Response:**
```json
{
    "status": "error",
    "error": "Invalid section. Must be one of: ['hair', 'background', 'clothes']"
}
```

### 3. Video Generation

Generates a video from an image, audio, and text prompt using AI.

**Payload:**
```json
{
    "input": {
        "api_key": "your-api-key-here",
        "process_type": "video_generation",
        "image_url": "https://example.com/image.jpg",
        "audio_url": "https://example.com/audio.mp3",
        "text_prompt": "A beautiful sunset over mountains",
        "aspect_ratio": "16:9",  // Optional, default: "16:9"
        "resolution": "720p",    // Optional, default: "720p"
        "duration": 10.0,        // Optional, duration in seconds
        "seed": 42              // Optional, default: 42
    }
}
```

**Sample Success Response:**
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

**Sample Error Response:**
```json
{
    "status": "error",
    "error": "audio_url is required"
}
```

## Error Handling

The API returns appropriate error messages for:
- Missing required parameters
- Invalid process types
- Invalid parameter values (including invalid themes and sections)
- Processing failures

## Rate Limiting

Please note that this API may have rate limits depending on your subscription level. Contact support for more information about rate limits and quotas.

## Authentication

All requests require an API key for authentication. The API key must be included in the request payload for every endpoint.

**API Key Format:**
```json
{
    "input": {
        "api_key": "your-api-key-here",
        // ... other parameters ...
    }
}
```

If the API key is missing or invalid, the API will return an error response:
```json
{
    "status": "error",
    "error": "API key is required"
}
```
or
```json
{
    "status": "error",
    "error": "Invalid API key"
}
```

Contact support to obtain your API credentials.

## Support

For any questions or issues, please contact support at support@faceforge.ai 