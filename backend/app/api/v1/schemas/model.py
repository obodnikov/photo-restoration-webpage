"""Model schemas for API responses."""
from typing import Any

from pydantic import BaseModel, Field


class ModelParameters(BaseModel):
    """Model-specific parameters schema."""

    scale: int | None = Field(None, description="Upscaling factor (for upscale models)")
    prompt: str | None = Field(None, description="Processing prompt (for enhancement models)")
    # Additional parameters can be stored in extra fields
    model_config = {"extra": "allow"}


class ModelInfo(BaseModel):
    """Model information schema."""

    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    model: str = Field(..., description="HuggingFace model path")
    category: str = Field(..., description="Model category (upscale, enhance, etc.)")
    description: str = Field(..., description="Brief description of model capabilities")
    parameters: ModelParameters | dict[str, Any] = Field(
        default_factory=dict, description="Model-specific parameters"
    )
    tags: list[str] = Field(default_factory=list, description="Model tags for filtering/search")
    version: str | None = Field(None, description="Model version")


class ModelListResponse(BaseModel):
    """Response schema for model list endpoint."""

    models: list[ModelInfo] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")
