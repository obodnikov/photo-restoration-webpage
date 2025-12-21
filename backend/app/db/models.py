"""
Database models for photo restoration application.

This module defines SQLAlchemy ORM models for:
- User: User accounts with authentication
- Session: User session tracking
- ProcessedImage: Processed image metadata and history
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class User(Base):
    """
    User model for authentication and authorization.

    Stores user credentials, profile information, and role.
    Users can be either 'admin' (can manage users) or 'user' (can only use the app).
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication credentials
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role and status
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user"
    )  # 'admin' or 'user'
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    password_must_change: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return (
            f"<User(id={self.id}, username={self.username}, "
            f"email={self.email}, role={self.role})>"
        )

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary.

        Args:
            include_sensitive: If True, include sensitive fields like password_must_change

        Returns:
            Dictionary representation of user
        """
        user_dict = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

        if include_sensitive:
            user_dict["password_must_change"] = self.password_must_change

        return user_dict


class Session(Base):
    """
    User session model.

    Tracks user sessions for storing processed images and history.
    Sessions are cleaned up after 24 hours of inactivity.
    Each session is linked to a specific user.
    """

    __tablename__ = "sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Session identifier (UUID)
    session_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    processed_images: Mapped[List["ProcessedImage"]] = relationship(
        "ProcessedImage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of Session."""
        return (
            f"<Session(id={self.id}, session_id={self.session_id}, "
            f"user_id={self.user_id}, created_at={self.created_at})>"
        )

    @property
    def image_count(self) -> int:
        """Get count of processed images in this session."""
        return len(self.processed_images) if self.processed_images else 0

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "image_count": self.image_count,
        }


class ProcessedImage(Base):
    """
    Processed image metadata model.

    Stores information about images that have been processed through
    AI models, including original and processed file paths.
    """

    __tablename__ = "processed_images"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to session
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Image metadata
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # File paths (relative to storage directory)
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    processed_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Optional: Store model parameters used
    model_parameters: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session", back_populates="processed_images"
    )

    def __repr__(self) -> str:
        """String representation of ProcessedImage."""
        return (
            f"<ProcessedImage(id={self.id}, session_id={self.session_id}, "
            f"filename={self.original_filename}, model={self.model_id})>"
        )

    def to_dict(self) -> dict:
        """Convert processed image to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "original_filename": self.original_filename,
            "model_id": self.model_id,
            "original_path": self.original_path,
            "processed_path": self.processed_path,
            "model_parameters": self.model_parameters,
            "created_at": self.created_at.isoformat(),
        }
