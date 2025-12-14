"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Debug mode: {settings.debug}")
    print(f"HuggingFace API configured: {bool(settings.hf_api_key)}")
    print(f"Available models: {len(settings.get_models())}")

    # Ensure data directories exist
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered photo restoration service using HuggingFace models",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded and processed images
app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_dir)),
    name="uploads",
)
app.mount(
    "/processed",
    StaticFiles(directory=str(settings.processed_dir)),
    name="processed",
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Photo Restoration API",
        "version": settings.app_version,
        "docs": "/api/docs",
    }


# Import and include routers (will be added in next phases)
# from app.api.v1.routes import auth, models, restoration
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
# app.include_router(restoration.router, prefix="/api/v1/restore", tags=["restoration"])
