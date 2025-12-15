"""Restoration API schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class RestoreResponse(BaseModel):
    """Response schema for image restoration endpoint."""

    id: int = Field(..., description="Processed image database ID")
    session_id: str = Field(..., description="Session identifier")
    original_url: str = Field(..., description="URL to access original image")
    processed_url: str = Field(..., description="URL to access processed image")
    model_id: str = Field(..., description="Model used for processing")
    original_filename: str = Field(..., description="Original filename")
    timestamp: datetime = Field(..., description="Processing timestamp")


class HistoryItemResponse(BaseModel):
    """Single history item response schema."""

    id: int = Field(..., description="Processed image database ID")
    original_filename: str = Field(..., description="Original filename")
    model_id: str = Field(..., description="Model used for processing")
    original_url: str = Field(..., description="URL to access original image")
    processed_url: str = Field(..., description="URL to access processed image")
    created_at: datetime = Field(..., description="Processing timestamp")
    model_parameters: str | None = Field(None, description="Model parameters used (JSON)")


class HistoryResponse(BaseModel):
    """Response schema for history list endpoint."""

    items: list[HistoryItemResponse] = Field(..., description="List of processed images")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class ImageDetailResponse(BaseModel):
    """Detailed response for a single processed image."""

    id: int = Field(..., description="Processed image database ID")
    session_id: int = Field(..., description="Database session ID")
    original_filename: str = Field(..., description="Original filename")
    model_id: str = Field(..., description="Model used for processing")
    original_url: str = Field(..., description="URL to access original image")
    processed_url: str = Field(..., description="URL to access processed image")
    original_path: str = Field(..., description="Relative path to original image")
    processed_path: str = Field(..., description="Relative path to processed image")
    model_parameters: str | None = Field(None, description="Model parameters used (JSON)")
    created_at: datetime = Field(..., description="Processing timestamp")


class DeleteResponse(BaseModel):
    """Response schema for delete endpoint."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
    files_deleted: int = Field(..., description="Number of files deleted")
