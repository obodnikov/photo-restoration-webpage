"""Model schemas for API responses."""
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelConfigSource(str, Enum):
    """Source of model configuration."""

    LOCAL = "local"
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    DEFAULT = "default"


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
    ui_hidden: bool | None = Field(None, description="Whether parameter should be hidden from UI")
    ui_group: str | None = Field(None, description="UI grouping hint")


class UIControlConfigResponse(BaseModel):
    """UI control configuration for frontend."""

    type: Literal[
        "text", "textarea", "number", "slider",
        "dropdown", "radio", "toggle", "checkbox"
    ] = Field(..., description="UI control type")
    label: str | None = Field(None, description="Display label (overrides auto-generated)")
    help: str | None = Field(None, description="Help text tooltip")
    options: list[str] | None = Field(None, description="Options for dropdown/radio")
    order: int | None = Field(None, description="Display order")
    step: int | float | None = Field(None, description="Step size for slider/number")
    marks: dict[str, str] | None = Field(None, description="Slider marks {value: label}")


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
    custom: dict[str, Any] | None = Field(
        None,
        description="Custom application-specific configuration (e.g., ui_controls for parameter UI)"
    )


class ModelListResponse(BaseModel):
    """Response schema for model list endpoint."""

    models: list[ModelInfo] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")


# ===== Model Configuration Management Schemas =====


class ModelConfigListItem(BaseModel):
    """Simplified model configuration for list view."""

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    provider: Literal["huggingface", "replicate"] = Field(..., description="Provider")
    category: str = Field(..., description="Category")
    enabled: bool = Field(True, description="Whether model is enabled")
    source: ModelConfigSource = Field(..., description="Configuration source file")
    tags: list[str] = Field(default_factory=list, description="Model tags")
    version: str | None = Field(None, description="Model version")


class ModelConfigDetail(BaseModel):
    """Full model configuration with all fields."""

    # Basic fields
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    model: str = Field(..., description="Model path")
    provider: Literal["huggingface", "replicate"] = Field(..., description="Provider")
    category: str = Field(..., description="Category")
    description: str = Field(..., description="Description")
    enabled: bool = Field(True, description="Whether model is enabled")
    tags: list[str] = Field(default_factory=list, description="Model tags")
    version: str | None = Field(None, description="Model version")

    # Complex objects (as JSON)
    replicate_schema: dict[str, Any] | None = Field(None, description="Replicate schema")
    custom: dict[str, Any] | None = Field(None, description="Custom config")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters")

    # Metadata
    source: ModelConfigSource = Field(..., description="Configuration source file")


class ModelConfigCreate(BaseModel):
    """Schema for creating a new model configuration."""

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    model: str = Field(..., description="Model path")
    provider: Literal["huggingface", "replicate"] = Field(..., description="Provider")
    category: str = Field(..., description="Category")
    description: str = Field("", description="Description")
    enabled: bool = Field(True, description="Whether model is enabled")
    tags: list[str] = Field(default_factory=list, description="Model tags")
    version: str | None = Field(None, description="Model version")
    replicate_schema: dict[str, Any] | None = Field(None, description="Replicate schema")
    custom: dict[str, Any] | None = Field(None, description="Custom config")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters")


class ModelConfigUpdate(BaseModel):
    """Schema for updating a model configuration."""

    name: str | None = Field(None, description="Model name")
    model: str | None = Field(None, description="Model path")
    provider: Literal["huggingface", "replicate"] | None = Field(None, description="Provider")
    category: str | None = Field(None, description="Category")
    description: str | None = Field(None, description="Description")
    enabled: bool | None = Field(None, description="Whether model is enabled")
    tags: list[str] | None = Field(None, description="Model tags")
    version: str | None = Field(None, description="Model version")
    replicate_schema: dict[str, Any] | None = Field(None, description="Replicate schema")
    custom: dict[str, Any] | None = Field(None, description="Custom config")
    parameters: dict[str, Any] | None = Field(None, description="Parameters")


class AvailableTagsResponse(BaseModel):
    """Available tags and categories for model configuration."""

    tags: list[str] = Field(..., description="Available tags")
    categories: list[str] = Field(..., description="Available categories")


class ValidationError(BaseModel):
    """Validation error detail."""

    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")


class ModelConfigValidationResponse(BaseModel):
    """Response for config validation."""

    valid: bool = Field(..., description="Whether config is valid")
    errors: list[ValidationError] = Field(default_factory=list, description="Validation errors")
