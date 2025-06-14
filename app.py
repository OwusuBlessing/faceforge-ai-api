from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.core.config import get_settings
from api.routers import avatar, image, video

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(avatar.router, prefix=settings.API_V1_STR)
app.include_router(image.router, prefix=settings.API_V1_STR)
app.include_router(video.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Welcome to FaceForge AI API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 