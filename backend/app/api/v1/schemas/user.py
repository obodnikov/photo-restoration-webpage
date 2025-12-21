"""
User management schemas for request/response models.

This module defines Pydantic models for user-related API operations.
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.password_validator import validate_password


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    password: str = Field(..., min_length=8, description="User password")
    role: str = Field(default="user", description="User role: 'admin' or 'user'")
    password_must_change: bool = Field(
        default=True,
        description="Whether user must change password on first login",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is either 'admin' or 'user'."""
        if v not in ["admin", "user"]:
            raise ValueError("Role must be either 'admin' or 'user'")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets requirements."""
        is_valid, error_message = validate_password(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.fullmatch(r"[A-Za-z0-9_-]+", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower()  # Normalize to lowercase


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: Optional[EmailStr] = Field(None, description="User email address")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, description="User role: 'admin' or 'user'")
    is_active: Optional[bool] = Field(None, description="Whether user account is active")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate role if provided."""
        if v is not None and v not in ["admin", "user"]:
            raise ValueError("Role must be either 'admin' or 'user'")
        return v


class PasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password meets requirements."""
        is_valid, error_message = validate_password(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class PasswordReset(BaseModel):
    """Schema for admin password reset."""

    new_password: str = Field(..., min_length=8, description="New password")
    password_must_change: bool = Field(
        default=True,
        description="Whether user must change password on next login",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password meets requirements."""
        is_valid, error_message = validate_password(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class UserResponse(BaseModel):
    """Schema for user information response."""

    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for list of users response."""

    users: list[UserResponse]
    total: int


class UserSessionResponse(BaseModel):
    """Schema for user session information."""

    id: int
    session_id: str
    created_at: datetime
    last_accessed: datetime
    image_count: int

    model_config = {"from_attributes": True}


class UserSessionsListResponse(BaseModel):
    """Schema for list of user sessions."""

    sessions: list[UserSessionResponse]
    total: int
