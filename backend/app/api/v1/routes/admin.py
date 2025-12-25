"""
Admin routes for user management.

This module provides admin-only endpoints for managing users.
Only users with 'admin' role can access these endpoints.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.model import (
    AvailableTagsResponse,
    ModelConfigCreate,
    ModelConfigDetail,
    ModelConfigListItem,
    ModelConfigSource,
    ModelConfigUpdate,
    ModelConfigValidationResponse,
    ValidationError,
)
from app.api.v1.schemas.user import (
    PasswordReset,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.core.authorization import require_admin
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.database import get_db
from app.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin - User Management"])


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user (Admin only)",
    description="""
    Create a new user account. Only accessible to admin users.

    **Admin Only**: This endpoint requires admin role.

    **Password Policy**:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    **Note**: By default, `password_must_change` is set to `true`, requiring
    the user to change their password on first login.
    """,
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user (admin only).

    Args:
        user_data: User creation data
        db: Database session
        current_user: Current admin user

    Returns:
        Created user information

    Raises:
        HTTPException 400: If username or email already exists
        HTTPException 403: If user is not admin
    """
    logger.info(
        f"Admin {current_user['username']} creating new user: {user_data.username}"
    )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists",
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True,
        password_must_change=user_data.password_must_change,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(
            f"User {new_user.username} (ID: {new_user.id}) created by admin {current_user['username']}"
        )

        return UserResponse.model_validate(new_user)

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User creation failed due to database constraint",
        )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users (Admin only)",
    description="Get list of all users. Only accessible to admin users.",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    role: Optional[str] = Query(None, description="Filter by role (admin or user)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserListResponse:
    """
    Get list of all users (admin only).

    Args:
        skip: Number of users to skip (pagination)
        limit: Maximum number of users to return
        role: Optional role filter
        is_active: Optional active status filter
        db: Database session
        current_user: Current admin user

    Returns:
        List of users with total count
    """
    logger.debug(
        f"Admin {current_user['username']} listing users (skip={skip}, limit={limit})"
    )

    # Build base query
    query = select(User)

    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count efficiently using SQL COUNT
    from sqlalchemy import func
    count_query = select(func.count(User.id))
    if role:
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get paginated results
    paginated_query = query.offset(skip).limit(limit)
    result = await db.execute(paginated_query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users], total=total
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user details (Admin only)",
    description="Get detailed information about a specific user. Only accessible to admin users.",
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        db: Database session
        current_user: Current admin user

    Returns:
        User information

    Raises:
        HTTPException 404: If user not found
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return UserResponse.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin only)",
    description="Update user information. Only accessible to admin users.",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    """
    Update user information (admin only).

    Args:
        user_id: User ID to update
        user_data: Update data
        db: Database session
        current_user: Current admin user

    Returns:
        Updated user information

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If email already exists
    """
    logger.info(f"Admin {current_user['username']} updating user ID: {user_id}")

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Check email uniqueness if changing email
    if user_data.email and user_data.email != user.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' already exists",
            )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.username} (ID: {user.id}) updated by admin")

        return UserResponse.model_validate(user)

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User update failed due to database constraint",
        )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (Admin only)",
    description="""
    Delete a user account. Only accessible to admin users.

    **Warning**: This will permanently delete the user and all associated data
    (sessions, processed images, etc.) due to cascade deletion.
    """,
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> None:
    """
    Delete user (admin only).

    Args:
        user_id: User ID to delete
        db: Database session
        current_user: Current admin user

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If trying to delete self
    """
    logger.warning(f"Admin {current_user['username']} deleting user ID: {user_id}")

    # Prevent admin from deleting themselves
    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Delete user (cascade will delete sessions and images)
    await db.delete(user)
    await db.commit()

    logger.info(f"User {user.username} (ID: {user.id}) deleted by admin")


@router.put(
    "/users/{user_id}/reset-password",
    response_model=UserResponse,
    summary="Reset user password (Admin only)",
    description="""
    Reset a user's password. Only accessible to admin users.

    By default, sets `password_must_change` to `true`, requiring the user
    to change their password on next login.
    """,
)
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    """
    Reset user password (admin only).

    Args:
        user_id: User ID
        password_data: New password data
        db: Database session
        current_user: Current admin user

    Returns:
        Updated user information

    Raises:
        HTTPException 404: If user not found
    """
    logger.info(
        f"Admin {current_user['username']} resetting password for user ID: {user_id}"
    )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.password_must_change = password_data.password_must_change

    await db.commit()
    await db.refresh(user)

    logger.info(f"Password reset for user {user.username} (ID: {user.id}) by admin")

    return UserResponse.model_validate(user)


# ===== Model Configuration Management =====


@router.get(
    "/models/config",
    summary="List all model configurations (Admin only)",
    description="""
    Get list of all model configurations with their source information.

    **Admin Only**: This endpoint requires admin role.

    Returns model configurations from all sources (default, environment, local).
    Each model includes a 'source' field indicating which config file it comes from.
    """,
)
async def list_model_configs(
    current_user: dict = Depends(require_admin),
) -> list:
    """
    List all model configurations with source information.

    Args:
        current_user: Current admin user

    Returns:
        List of model configurations with source metadata
    """
    settings = get_settings()
    models = settings.get_models()

    result = []
    for model in models:
        source = settings.get_model_source(model["id"])
        result.append(
            ModelConfigListItem(
                id=model["id"],
                name=model["name"],
                provider=model["provider"],
                category=model["category"],
                enabled=model.get("enabled", True),
                source=ModelConfigSource(source),
                tags=model.get("tags", []),
                version=model.get("version"),
            )
        )

    logger.info(f"Admin {current_user['username']} listed model configs ({len(result)} total)")
    return result


@router.get(
    "/models/config/{model_id}",
    summary="Get model configuration details (Admin only)",
    description="""
    Get full configuration details for a specific model.

    **Admin Only**: This endpoint requires admin role.

    Returns complete model configuration including replicate_schema, custom, and parameters.
    """,
)
async def get_model_config(
    model_id: str,
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Get detailed configuration for a specific model.

    Args:
        model_id: Model identifier
        current_user: Current admin user

    Returns:
        Full model configuration

    Raises:
        HTTPException 404: If model not found
    """
    settings = get_settings()
    model = settings.get_model_by_id(model_id)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found",
        )

    source = settings.get_model_source(model_id)

    result = ModelConfigDetail(
        id=model["id"],
        name=model["name"],
        model=model["model"],
        provider=model["provider"],
        category=model["category"],
        description=model.get("description", ""),
        enabled=model.get("enabled", True),
        tags=model.get("tags", []),
        version=model.get("version"),
        replicate_schema=model.get("replicate_schema"),
        custom=model.get("custom"),
        parameters=model.get("parameters", {}),
        source=ModelConfigSource(source),
    )

    logger.info(f"Admin {current_user['username']} retrieved config for model '{model_id}'")
    return result.model_dump()


@router.post(
    "/models/config",
    status_code=status.HTTP_201_CREATED,
    summary="Create new model configuration (Admin only)",
    description="""
    Create a new model configuration in local.json.

    **Admin Only**: This endpoint requires admin role.

    The new configuration will be saved to local.json and will override
    any existing configuration with the same ID from default/environment files.
    """,
)
async def create_model_config(
    config_data: dict,
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Create a new model configuration.

    Args:
        config_data: Model configuration data
        current_user: Current admin user

    Returns:
        Created configuration

    Raises:
        HTTPException 400: If configuration is invalid
        HTTPException 409: If model ID already exists in local.json
    """
    settings = get_settings()

    # Validate configuration
    try:
        validated_config = ModelConfigCreate(**config_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}",
        )

    # Check if model already exists in local.json
    if settings.get_model_source(validated_config.id) == "local":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model '{validated_config.id}' already exists in local.json. Use PUT to update.",
        )

    # Save to local.json
    try:
        settings.save_local_model_config(validated_config.model_dump(exclude_none=True))
        settings.reload_config()
    except Exception as e:
        logger.error(f"Error saving model config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}",
        )

    logger.info(f"Admin {current_user['username']} created model config '{validated_config.id}'")
    return validated_config.model_dump()


@router.put(
    "/models/config/{model_id}",
    summary="Update model configuration (Admin only)",
    description="""
    Update an existing model configuration in local.json.

    **Admin Only**: This endpoint requires admin role.

    If the model exists in default/environment files, this creates an override in local.json.
    Updates are partial - only provided fields will be updated.
    """,
)
async def update_model_config(
    model_id: str,
    config_data: dict,
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Update model configuration.

    Args:
        model_id: Model identifier
        config_data: Updated configuration data
        current_user: Current admin user

    Returns:
        Updated configuration

    Raises:
        HTTPException 400: If configuration is invalid
        HTTPException 404: If model not found
    """
    settings = get_settings()

    # Check if model exists
    existing_model = settings.get_model_by_id(model_id)
    if not existing_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found",
        )

    # Validate update data
    try:
        validated_update = ModelConfigUpdate(**config_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}",
        )

    # Define allowed update fields
    ALLOWED_UPDATE_FIELDS = {
        "name",
        "model",
        "provider",
        "category",
        "description",
        "enabled",
        "tags",
        "version",
        "replicate_schema",
        "custom",
        "parameters",
    }

    # Merge with existing config
    updated_config = {**existing_model}
    update_dict = validated_update.model_dump(exclude_none=True)

    # Validate only allowed fields are being updated
    invalid_fields = set(update_dict.keys()) - ALLOWED_UPDATE_FIELDS
    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update fields: {', '.join(sorted(invalid_fields))}",
        )

    updated_config.update(update_dict)
    updated_config["id"] = model_id  # Ensure ID is preserved

    # Save to local.json
    try:
        settings.save_local_model_config(updated_config)
        settings.reload_config()
    except Exception as e:
        logger.error(f"Error updating model config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )

    logger.info(f"Admin {current_user['username']} updated model config '{model_id}'")
    return updated_config


@router.delete(
    "/models/config/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete model configuration from local.json (Admin only)",
    description="""
    Delete a model configuration from local.json.

    **Admin Only**: This endpoint requires admin role.

    **Important**: This only deletes the configuration from local.json.
    If the model exists in default/environment files, it will revert to that configuration.
    Models from default/environment files cannot be completely deleted, only overridden.
    """,
)
async def delete_model_config(
    model_id: str,
    current_user: dict = Depends(require_admin),
) -> None:
    """
    Delete model configuration from local.json.

    Args:
        model_id: Model identifier
        current_user: Current admin user

    Raises:
        HTTPException 404: If model not found in local.json
    """
    settings = get_settings()

    # Check if model exists in local.json
    if settings.get_model_source(model_id) != "local":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found in local.json. Cannot delete models from default/environment files.",
        )

    # Delete from local.json
    try:
        deleted = settings.delete_local_model_config(model_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_id}' not found in local.json",
            )
        settings.reload_config()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}",
        )

    logger.info(f"Admin {current_user['username']} deleted model config '{model_id}'")


@router.get(
    "/models/tags",
    summary="Get available tags and categories (Admin only)",
    description="""
    Get list of predefined tags and categories for model configuration.

    **Admin Only**: This endpoint requires admin role.

    Returns available tags and categories from config file (model_configuration section).
    """,
)
async def get_available_tags(
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Get available tags and categories.

    Args:
        current_user: Current admin user

    Returns:
        Available tags and categories
    """
    settings = get_settings()

    result = AvailableTagsResponse(
        tags=settings.get_available_tags(),
        categories=settings.get_available_categories(),
    )

    return result.model_dump()


@router.post(
    "/models/validate",
    summary="Validate model configuration (Admin only)",
    description="""
    Validate a model configuration without saving it.

    **Admin Only**: This endpoint requires admin role.

    Returns validation status and any errors found in the configuration.
    """,
)
async def validate_model_config(
    config_data: dict,
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Validate model configuration.

    Args:
        config_data: Model configuration to validate
        current_user: Current admin user

    Returns:
        Validation result with errors if any
    """
    errors = []

    try:
        # Validate using Pydantic model
        ModelConfigCreate(**config_data)

        # Additional validations can be added here
        # For example: check if replicate_schema is valid JSON structure

        return ModelConfigValidationResponse(valid=True, errors=[]).model_dump()
    except Exception as e:
        # Parse Pydantic validation errors
        if hasattr(e, "errors"):
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(
                    ValidationError(
                        field=field,
                        message=error["msg"],
                    )
                )
        else:
            errors.append(
                ValidationError(
                    field="general",
                    message=str(e),
                )
            )

        return ModelConfigValidationResponse(valid=False, errors=errors).model_dump()


@router.post(
    "/models/reload",
    summary="Reload model configurations (Admin only)",
    description="""
    Reload model configurations from files without restarting the server.

    **Admin Only**: This endpoint requires admin role.

    This triggers a hot reload of all configuration files (default, environment, local).
    Useful after manually editing configuration files.
    """,
)
async def reload_model_configs(
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Reload model configurations.

    Args:
        current_user: Current admin user

    Returns:
        Reload status

    Raises:
        HTTPException 500: If reload fails
    """
    settings = get_settings()

    try:
        settings.reload_config()
        models_count = len(settings.get_models())

        logger.info(f"Admin {current_user['username']} triggered config reload ({models_count} models loaded)")

        return {
            "success": True,
            "message": f"Configuration reloaded successfully. {models_count} models loaded.",
        }
    except Exception as e:
        logger.error(f"Error reloading configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}",
        )
