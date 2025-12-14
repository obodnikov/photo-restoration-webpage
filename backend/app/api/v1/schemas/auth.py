"""
Authentication schemas for request and response validation.

This module defines Pydantic models for authentication-related API operations.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request model for user login."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Username for authentication"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Password for authentication"
    )
    remember_me: bool = Field(
        default=False,
        description="Remember user session for extended period"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password",
                "remember_me": False
            }
        }


class TokenResponse(BaseModel):
    """Response model for successful authentication."""

    access_token: str = Field(
        ...,
        description="JWT access token for authentication"
    )
    token_type: str = Field(
        default="bearer",
        description="Type of token (always 'bearer' for JWT)"
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }


class UserResponse(BaseModel):
    """Response model for user information."""

    username: str = Field(
        ...,
        description="Username of the authenticated user"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin"
            }
        }


class TokenValidateResponse(BaseModel):
    """Response model for token validation."""

    valid: bool = Field(
        ...,
        description="Whether the token is valid"
    )
    username: Optional[str] = Field(
        None,
        description="Username from token if valid"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "username": "admin"
            }
        }
