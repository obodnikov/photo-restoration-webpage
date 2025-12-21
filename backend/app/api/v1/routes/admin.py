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

from app.api.v1.schemas.user import (
    PasswordReset,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.core.authorization import require_admin
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

    # Build query
    query = select(User)

    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
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
