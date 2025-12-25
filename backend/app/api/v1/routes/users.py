"""
User profile routes.

This module provides endpoints for users to manage their own profile and sessions.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import (
    PasswordChange,
    UserResponse,
    UserSessionResponse,
    UserSessionsListResponse,
)
from app.core.security import get_current_user, get_current_user_validated, get_password_hash, verify_password
from app.db.database import get_db
from app.db.models import Session, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get profile information for the currently authenticated user.",
)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_validated()),
) -> UserResponse:
    """
    Get current user's profile.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        User profile information

    Raises:
        HTTPException 404: If user not found (shouldn't happen with valid token)
    """
    # Get fresh user data from database
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="""
    Change the current user's password.

    Requires current password for verification.
    New password must meet complexity requirements.
    """,
)
async def change_my_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_validated()),
) -> dict:
    """
    Change current user's password.

    Args:
        password_data: Password change data (current and new password)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException 400: If current password is incorrect
        HTTPException 404: If user not found
    """
    logger.info(f"User {current_user['username']} requesting password change")

    # Get user from database
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Check if new password is same as current
    if verify_password(password_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.password_must_change = False  # Clear forced password change flag

    await db.commit()

    logger.info(f"Password changed successfully for user {user.username}")

    return {"message": "Password changed successfully"}


@router.get(
    "/me/sessions",
    response_model=UserSessionsListResponse,
    summary="Get my active sessions",
    description="""
    Get list of all active sessions for the current user.

    Useful for viewing login history and managing active sessions.
    """,
)
async def get_my_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_validated()),
) -> UserSessionsListResponse:
    """
    Get current user's active sessions.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of user's sessions
    """
    # Query user's sessions
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user["user_id"])
        .order_by(Session.last_accessed.desc())
    )
    sessions = result.scalars().all()

    return UserSessionsListResponse(
        sessions=[UserSessionResponse.model_validate(session) for session in sessions],
        total=len(sessions),
    )


@router.delete(
    "/me/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout from specific session",
    description="""
    Delete a specific session (logout from a device).

    This allows users to remotely logout from other devices.
    """,
)
async def delete_my_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_validated()),
) -> None:
    """
    Delete a specific session (remote logout).

    Args:
        session_id: Session ID to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException 404: If session not found
        HTTPException 403: If session belongs to another user
    """
    logger.info(
        f"User {current_user['username']} deleting session {session_id}"
    )

    # Get session
    result = await db.execute(
        select(Session).where(Session.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Verify session belongs to current user
    if session.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own sessions",
        )

    # Delete session
    await db.delete(session)
    await db.commit()

    logger.info(f"Session {session_id} deleted by user {current_user['username']}")
