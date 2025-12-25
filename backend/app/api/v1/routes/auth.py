"""
Authentication routes for user login and token management.

This module provides endpoints for:
- User login (JWT token generation)
- Token validation
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    TokenValidateResponse,
)
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_user_validated,
)
from app.core.config import get_settings
from app.db.database import get_db
from app.services.session_manager import SessionManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="""
    Authenticate user with username and password, returns JWT access token.

    **Authentication Flow:**
    1. Submit username and password
    2. Receive JWT access token
    3. Include token in subsequent requests: `Authorization: Bearer {token}`

    **Token Expiration:**
    - Standard login: 24 hours (1440 minutes)
    - Remember Me: 7 days

    **Example Request:**
    ```json
    {
        "username": "admin",
        "password": "your_password",
        "remember_me": false
    }
    ```

    **Example Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 86400
    }
    ```
    """,
    responses={
        200: {
            "description": "Successfully authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 86400
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid credentials"}
                }
            }
        }
    }
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.

    For MVP: Validates against hardcoded credentials from environment.
    Phase 2.x: Will validate against database users.

    Creates a new session for each login.

    Args:
        credentials: Login credentials (username, password, remember_me)
        db: Database session

    Returns:
        TokenResponse with JWT access token and session_id

    Raises:
        HTTPException 401: If credentials are invalid
    """
    settings = get_settings()

    # Log login attempt (don't log password!)
    logger.info(f"Login attempt for user: {credentials.username}")

    # Authenticate user against database
    user = await authenticate_user(credentials.username, credentials.password, db)

    if user is None:
        # Log failed attempt with details for debugging
        logger.warning(
            f"Failed login attempt for user: {credentials.username} - Invalid credentials"
        )
        # Generic error message for security (don't reveal if user exists)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    from sqlalchemy import select, update
    from app.db.models import User as UserModel
    from datetime import datetime

    await db.execute(
        update(UserModel)
        .where(UserModel.id == user["id"])
        .values(last_login=datetime.utcnow())
    )
    await db.commit()

    # Create new session for this login
    session_manager = SessionManager()
    session = await session_manager.create_session(db, user["id"])
    logger.info(f"Created session {session.session_id} for user {credentials.username} (user_id={user['id']})")

    # Calculate token expiration
    # If remember_me is True, extend token lifetime (7 days for MVP)
    if credentials.remember_me:
        expires_delta = timedelta(days=7)
        expires_in_seconds = 7 * 24 * 60 * 60  # 7 days in seconds
        logger.info(f"User {credentials.username} logged in with 'Remember Me' (7 days)")
    else:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        expires_in_seconds = settings.access_token_expire_minutes * 60
        logger.info(
            f"User {credentials.username} logged in successfully "
            f"(expires in {settings.access_token_expire_minutes} minutes)"
        )

    # Create JWT token with user data and session_id
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"],
            "session_id": session.session_id,
            "password_must_change": user["password_must_change"],
        },
        expires_delta=expires_delta
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
    )


@router.post(
    "/validate",
    response_model=TokenValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate token",
    description="Validate JWT token and return user information",
)
async def validate_token(
    user: dict = Depends(get_current_user_validated())
) -> TokenValidateResponse:
    """
    Validate JWT token and return user information.

    This endpoint can be used by the frontend to check if a stored
    token is still valid without making a full API request.

    Args:
        user: Current user from token (injected by dependency)

    Returns:
        TokenValidateResponse with validation status and username
    """
    logger.debug(f"Token validated for user: {user['username']}")

    return TokenValidateResponse(
        valid=True,
        username=user["username"]
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user",
)
async def get_me(user: dict = Depends(get_current_user_validated())) -> UserResponse:
    """
    Get current authenticated user information.

    This is a protected endpoint that requires a valid JWT token.
    Useful for the frontend to get user details after login.

    Args:
        user: Current user from token (injected by dependency)

    Returns:
        UserResponse with user information
    """
    logger.debug(f"User info requested for: {user['username']}")

    return UserResponse(username=user["username"])
