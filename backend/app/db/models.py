"""
Database models for photo restoration application.

This module defines SQLAlchemy ORM models for:
- Session: User session tracking
- ProcessedImage: Processed image metadata and history
"""
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Session(Base):
    """
    User session model.

    Tracks user sessions for storing processed images and history.
    Sessions are cleaned up after 24 hours of inactivity.
    """

    __tablename__ = "sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

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
            f"created_at={self.created_at})>"
        )

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "image_count": len(self.processed_images) if self.processed_images else 0,
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
