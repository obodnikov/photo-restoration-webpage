"""API v1 routes."""
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.models import router as models_router

__all__ = ["auth_router", "models_router"]
