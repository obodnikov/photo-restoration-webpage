"""Model management routes."""
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.schemas.model import ModelInfo, ModelListResponse
from app.core.config import Settings, get_settings
from app.core.security import get_current_user

router = APIRouter(prefix="/models", tags=["models"])
security = HTTPBearer(auto_error=False)


def get_cached_models(settings: Settings) -> list[ModelInfo]:
    """
    Get the list of available models from configuration.

    Args:
        settings: Application settings instance

    Returns:
        List of ModelInfo objects
    """
    models_data = settings.get_models()
    return [ModelInfo(**model) for model in models_data]


async def check_auth_if_required(
    settings: Settings,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """
    Check authentication if required by settings.

    Args:
        settings: Application settings
        credentials: Optional HTTP bearer credentials

    Returns:
        Username if authenticated, None if auth not required

    Raises:
        HTTPException: If auth required but not provided/invalid
    """
    if not settings.models_require_auth:
        # Auth not required
        return None

    # Auth is required
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the token using existing security function
    from app.core.security import verify_token

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username


@router.get(
    "",
    response_model=ModelListResponse,
    summary="List available AI models",
    description="""
    Get a list of all available AI models for image processing.

    **Model Information Includes:**
    - Model ID (for use in restoration requests)
    - Display name
    - Provider (HuggingFace or Replicate)
    - Category (upscale, enhance, restore)
    - Description
    - Enabled status
    - Default parameters

    **Authentication:**
    - Optional (configurable via MODELS_REQUIRE_AUTH)
    - By default, models list is public

    **Example Response:**
    ```json
    {
        "models": [
            {
                "id": "swin2sr-2x",
                "name": "Swin2SR 2x Upscale",
                "provider": "huggingface",
                "category": "upscale",
                "description": "Fast 2x upscaling for images",
                "enabled": true
            }
        ],
        "total": 4
    }
    ```
    """,
    responses={
        200: {
            "description": "List of available models",
            "content": {
                "application/json": {
                    "example": {
                        "models": [
                            {
                                "id": "swin2sr-2x",
                                "name": "Swin2SR 2x Upscale",
                                "model": "caidas/swin2SR-classical-sr-x2-64",
                                "provider": "huggingface",
                                "category": "upscale",
                                "description": "Fast 2x upscaling for images",
                                "enabled": True,
                                "parameters": {"scale": 2}
                            }
                        ],
                        "total": 1
                    }
                }
            }
        },
        403: {
            "description": "Authentication required (if MODELS_REQUIRE_AUTH=true)",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication required"}
                }
            }
        }
    }
)
async def list_models(
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
):
    """
    List all available AI models.

    Returns a list of all configured models with their metadata.
    Authentication is optional and controlled by MODELS_REQUIRE_AUTH setting.

    Returns:
        ModelListResponse: List of models with total count
    """
    # Check auth if required
    await check_auth_if_required(settings, credentials)

    models = get_cached_models(settings)
    return ModelListResponse(models=models, total=len(models))


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(
    model_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
):
    """
    Get details for a specific model by ID.

    Args:
        model_id: Unique model identifier

    Returns:
        ModelInfo: Model details

    Raises:
        HTTPException: 404 if model not found
    """
    # Check auth if required
    await check_auth_if_required(settings, credentials)

    models = get_cached_models(settings)

    for model in models:
        if model.id == model_id:
            return model

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Model '{model_id}' not found",
    )
