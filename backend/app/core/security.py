"""
Security utilities for JWT token generation and password hashing.

This module provides authentication and authorization functionality:
- JWT token creation and validation
- Password hashing and verification
- User authentication dependency for protected routes
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload if valid, None otherwise
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get the current authenticated user from JWT token (basic validation only).

    This function only validates the JWT token itself. For full security with
    session and user status validation, use get_current_user_validated() instead.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        User data from token payload

    Raises:
        HTTPException: If token is invalid or expired

    Note:
        This function does NOT validate against the database. Use get_current_user_validated()
        for routes that need to ensure sessions haven't been deleted and users haven't been disabled.
    """
    import logging
    logger = logging.getLogger(__name__)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    logger.info(f"Validating token: {token[:20]}...")

    payload = verify_token(token)

    if payload is None:
        logger.error(f"Token verification failed for token: {token[:20]}...")
        raise credentials_exception

    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    role: str = payload.get("role")
    session_id: str = payload.get("session_id")
    password_must_change: bool = payload.get("password_must_change", False)

    logger.info(f"Token verified - username: {username}, user_id: {user_id}, role: {role}, session_id: {session_id}")

    if username is None or user_id is None:
        logger.error("Token payload missing required fields (username or user_id)")
        raise credentials_exception

    # Return user data from token
    return {
        "username": username,
        "user_id": user_id,
        "role": role,
        "session_id": session_id,
        "password_must_change": password_must_change,
    }


def get_current_user_validated():
    """
    Factory function to create a dependency that validates user and session against database.

    SECURITY: This validates:
    1. The JWT token is valid and not expired
    2. The session referenced in the token still exists in the database
    3. The user account is still active (not disabled)

    This prevents:
    - Deleted sessions from being used (remote logout works)
    - Disabled users from accessing the API
    - Stolen/lost tokens from working indefinitely

    Returns:
        Async dependency function for FastAPI routes

    Example:
        from app.db.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession

        @app.get("/protected")
        async def protected_route(
            user: dict = Depends(get_current_user_validated()),
            db: AsyncSession = Depends(get_db)
        ):
            return {"message": f"Hello {user['username']}"}
    """
    from app.db.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    async def validate_user(
        user_data: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> dict:
        """Inner function that performs the actual validation."""
        import logging
        from sqlalchemy import select
        from app.db.models import User, Session

        logger = logging.getLogger(__name__)

        user_id = user_data["user_id"]
        username = user_data["username"]
        session_id = user_data.get("session_id")

        # Check if user still exists and is active
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"Token references non-existent user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning(f"Token used by disabled user: {username} (user_id: {user_id})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account has been disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if session still exists (not deleted via logout)
        if session_id:
            result = await db.execute(
                select(Session).where(
                    Session.session_id == session_id,
                    Session.user_id == user_id,
                )
            )
            session = result.scalar_one_or_none()

            if session is None:
                logger.warning(f"Token references deleted session: {session_id} (user: {username})")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has been terminated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
     
            logger.debug(f"Session and user validation passed for user: {username}")

        return user_data

    return validate_user


async def authenticate_user(username: str, password: str, db) -> Optional[dict]:
    """
    Authenticate a user with username and password (database-backed).

    Phase 2.4: Authenticates against database users with hashed passwords.

    Args:
        username: Username to authenticate
        password: Plain text password to verify
        db: Database session (AsyncSession)

    Returns:
        User dict with id, username, email, full_name, role if authentication successful
        None otherwise
    """
    from sqlalchemy import select
    from app.db.models import User

    # Query user from database
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        # User not found
        return None

    if not user.is_active:
        # User account is disabled
        return None

    # Verify password against hashed password
    if not verify_password(password, user.hashed_password):
        return None

    # Return user data (excluding sensitive fields)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "password_must_change": user.password_must_change,
    }
