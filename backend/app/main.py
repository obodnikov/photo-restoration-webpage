"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.routes import auth_router, models_router, restoration_router
from app.api.v1.routes.admin import router as admin_router
from app.api.v1.routes.users import router as users_router
from app.db.database import init_db, close_db
from app.services.cleanup import (
    start_cleanup_scheduler,
    stop_cleanup_scheduler,
    cleanup_old_sessions,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")

    config_source = 'JSON config files' if settings.is_using_json_config() else '.env only (DEPRECATED)'
    logger.info(f"Configuration source: {config_source}")

    logger.info(f"HuggingFace API configured: {bool(settings.hf_api_key)}")

    models = settings.get_models()
    logger.info(f"Available models: {len(models)}")

    if settings.debug:
        logger.debug("=== DEBUG MODE ENABLED ===")
        logger.debug(f"Config directory: {settings.upload_dir.parent}")
        logger.debug(f"Upload directory: {settings.upload_dir}")
        logger.debug(f"Processed directory: {settings.processed_dir}")
        logger.debug(f"Database URL: {settings.database_url}")
        logger.debug(f"CORS origins: {settings.cors_origins}")
        logger.debug("Models configuration:")
        for model in models:
            logger.debug(f"  - {model['id']}: {model['name']} ({model['provider']})")

    # Ensure data directories exist
    logger.debug(f"Creating data directories if they don't exist...")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Data directories ready")

    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")

    # Run initial cleanup
    logger.info("Running initial session cleanup...")
    await cleanup_old_sessions()
    logger.info("Initial cleanup completed")

    # Start cleanup scheduler
    logger.info(
        f"Starting cleanup scheduler (interval: {settings.session_cleanup_interval_hours}h, "
        f"cleanup threshold: {settings.session_cleanup_hours}h)"
    )
    start_cleanup_scheduler()
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    stop_cleanup_scheduler()
    logger.debug("Cleanup scheduler stopped")
    await close_db()
    logger.info("Application shutdown complete")


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
app.include_router(admin_router, prefix="/api/v1")  # Admin user management
app.include_router(users_router, prefix="/api/v1")  # User profile management


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

