"""API v1 routes."""
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.models import router as models_router
from app.api.v1.routes.restoration import router as restoration_router

__all__ = ["auth_router", "models_router", "restoration_router"]
