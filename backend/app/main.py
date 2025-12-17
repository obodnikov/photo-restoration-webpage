"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.routes import auth_router, models_router, restoration_router
from app.db.database import init_db, close_db
from app.services.cleanup import (
    start_cleanup_scheduler,
    stop_cleanup_scheduler,
    cleanup_old_sessions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.app_env}")
    print(f"Debug mode: {settings.debug}")
    print(f"Configuration source: {'JSON config files' if settings.is_using_json_config() else '.env only (DEPRECATED)'}")
    print(f"HuggingFace API configured: {bool(settings.hf_api_key)}")
    print(f"Available models: {len(settings.get_models())}")

    # Ensure data directories exist
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database
    print("Initializing database...")
    await init_db()
    print("Database initialized")

    # Run initial cleanup
    print("Running initial session cleanup...")
    await cleanup_old_sessions()

    # Start cleanup scheduler
    print(
        f"Starting cleanup scheduler (interval: {settings.session_cleanup_interval_hours}h, "
        f"cleanup threshold: {settings.session_cleanup_hours}h)..."
    )
    start_cleanup_scheduler()

    yield

    # Shutdown
    print("Shutting down...")
    stop_cleanup_scheduler()
    await close_db()


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

# Register API routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(restoration_router, prefix="/api/v1")


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

