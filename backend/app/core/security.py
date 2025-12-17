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
    session_id: str = payload.get("session_id")

    logger.info(f"Token verified - username: {username}, session_id: {session_id}")

    if username is None:
        logger.error("Token payload missing 'sub' (username)")
        raise credentials_exception

    # For MVP, we return minimal user data including session_id
    # In Phase 2.x, this will query the database
    return {
        "username": username,
        "session_id": session_id
    }


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password.

    For MVP: Uses hardcoded credentials from environment variables.
    Phase 2.x: Will query database for user credentials.

    Args:
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        User dict if authentication successful, None otherwise
    """
    settings = get_settings()

    # MVP: Check against hardcoded credentials from .env
    if username != settings.auth_username:
        return None

    # For MVP with hardcoded credentials, do simple password comparison
    # In production Phase 2.x, passwords will be pre-hashed in database
    # and we'll use verify_password(password, user.hashed_password)
    if password != settings.auth_password:
        return None

    return {"username": username}
