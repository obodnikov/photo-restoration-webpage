"""Model schemas for API responses."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ParameterSchemaResponse(BaseModel):
    """Parameter schema for frontend."""

    name: str = Field(..., description="Parameter name")
    type: Literal["string", "integer", "float", "boolean", "enum"] = Field(
        ..., description="Parameter type"
    )
    required: bool = Field(False, description="Whether parameter is required")
    description: str = Field("", description="Parameter description")
    default: Any | None = Field(None, description="Default value")
    min: int | float | None = Field(None, description="Minimum value (for numeric types)")
    max: int | float | None = Field(None, description="Maximum value (for numeric types)")
    values: list[str] | None = Field(None, description="Allowed values (for enum type)")
    ui_group: str | None = Field(None, description="UI grouping hint")


class CustomSchemaResponse(BaseModel):
    """Custom constraints for frontend."""

    max_file_size_mb: int = Field(..., description="Maximum file size in MB")
    supported_formats: list[str] = Field(..., description="Supported image formats")
    estimated_time_seconds: int | None = Field(None, description="Estimated processing time")


class ModelSchemaResponse(BaseModel):
    """Schema information for a model (for frontend)."""

    parameters: list[ParameterSchemaResponse] = Field(
        default_factory=list,
        description="Model parameters"
    )
    custom: CustomSchemaResponse | None = Field(
        None,
        description="Custom constraints and metadata"
    )


class ModelParameters(BaseModel):
    """Model-specific parameters schema."""

    scale: int | None = Field(None, description="Upscaling factor (for upscale models)")
    prompt: str | None = Field(None, description="Processing prompt (for enhancement models)")
    # Additional parameters can be stored in extra fields
    model_config = {"extra": "allow"}


class ModelInfo(BaseModel):
    """Model information schema."""

    # Configure to use alias for serialization (API responses)
    # populate_by_name allows both 'schema' and 'model_schema' for input (deserialization)
    # FastAPI uses by_alias=True by default, which will use serialization_alias="schema"
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    model: str = Field(..., description="Model path (HuggingFace or Replicate)")
    provider: Literal["huggingface", "replicate"] = Field(
        "huggingface", description="Model provider (huggingface or replicate)"
    )
    category: str = Field(..., description="Model category (upscale, enhance, restore, etc.)")
    description: str = Field(..., description="Brief description of model capabilities")
    parameters: ModelParameters | dict[str, Any] = Field(
        default_factory=dict, description="Model-specific parameters"
    )
    tags: list[str] = Field(default_factory=list, description="Model tags for filtering/search")
    version: str | None = Field(None, description="Model version")
    model_schema: ModelSchemaResponse | None = Field(
        None,
        alias="schema",
        serialization_alias="schema",
        description="Model schema (for Replicate models with parameter validation)"
    )


class ModelListResponse(BaseModel):
    """Response schema for model list endpoint."""

    models: list[ModelInfo] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")
