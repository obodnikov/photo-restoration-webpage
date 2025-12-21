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
    Dependency to get the current authenticated user from JWT token.

    This dependency extracts and validates the JWT token from the
    Authorization header. Use this to protect routes that require
    authentication.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        User data from token payload

    Raises:
        HTTPException: If token is invalid or expired

    Example:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['username']}"}
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
