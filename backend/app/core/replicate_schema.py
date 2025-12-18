"""
Replicate model schema definitions.

This module defines the schema structure for Replicate models,
including input parameters, output types, and custom constraints.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ImageInputSchema(BaseModel):
    """Schema for image input parameter."""

    param_name: str = Field(
        ...,
        description="Replicate API parameter name for image input (e.g., 'input_image', 'image')"
    )
    type: Literal["uri"] = Field(
        "uri",
        description="Input type - always 'uri' for Replicate image inputs"
    )
    format: Literal["image"] = Field(
        "image",
        description="Format hint - 'image' for image files"
    )
    required: bool = Field(
        True,
        description="Whether image input is required (always true for image models)"
    )
    description: str = Field(
        "",
        description="Human-readable description of the image input"
    )


class ParameterSchema(BaseModel):
    """Schema for a single parameter."""

    name: str = Field(..., description="Parameter name as expected by Replicate API")
    type: Literal["string", "integer", "float", "boolean", "enum"] = Field(
        ...,
        description="Parameter data type"
    )
    required: bool = Field(
        False,
        description="Whether parameter is required"
    )
    description: str = Field(
        "",
        description="Human-readable description"
    )

    # Type-specific constraints
    default: Any | None = Field(
        None,
        description="Default value if not provided"
    )
    min: int | float | None = Field(
        None,
        description="Minimum value (for integer/float types)"
    )
    max: int | float | None = Field(
        None,
        description="Maximum value (for integer/float types)"
    )
    values: list[str] | None = Field(
        None,
        description="Allowed values (for enum type)"
    )

    # UI hints
    ui_hidden: bool = Field(
        False,
        description="Hide from frontend UI (for advanced/internal parameters)"
    )
    ui_group: str | None = Field(
        None,
        description="Group parameters in UI (e.g., 'output', 'quality', 'advanced')"
    )

    @field_validator("type")
    @classmethod
    def validate_enum_type(cls, v: str, info) -> str:
        """Validate that enum type has values."""
        # This is called before values, so we check in model_validator instead
        return v

    def model_post_init(self, __context) -> None:
        """Validate enum type has values after initialization."""
        if self.type == "enum" and not self.values:
            raise ValueError("Enum type must have 'values' list")


class InputSchema(BaseModel):
    """Schema for model input."""

    image: ImageInputSchema = Field(
        ...,
        description="Image input configuration"
    )
    parameters: list[ParameterSchema] = Field(
        default_factory=list,
        description="Additional model parameters"
    )


class OutputSchema(BaseModel):
    """Schema for model output."""

    type: Literal["uri", "base64", "json", "list"] = Field(
        ...,
        description="Output type returned by Replicate"
    )
    format: str | None = Field(
        None,
        description="Output format hint (e.g., 'image', 'text')"
    )


class CustomSchema(BaseModel):
    """Custom application-specific constraints and metadata."""

    max_file_size_mb: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum input file size in MB"
    )
    supported_formats: list[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png"],
        description="Supported input image formats"
    )
    estimated_time_seconds: int | None = Field(
        None,
        ge=1,
        description="Estimated processing time in seconds"
    )
    cost_per_run: float | None = Field(
        None,
        ge=0,
        description="Estimated cost per run in USD"
    )

    @field_validator("supported_formats")
    @classmethod
    def normalize_formats(cls, v: list[str]) -> list[str]:
        """Normalize formats to lowercase without dots."""
        return [fmt.lower().lstrip(".") for fmt in v]


class ReplicateModelSchema(BaseModel):
    """Complete schema for a Replicate model."""

    input: InputSchema = Field(
        ...,
        description="Input schema including image and parameters"
    )
    output: OutputSchema = Field(
        ...,
        description="Output schema"
    )
    custom: CustomSchema = Field(
        default_factory=CustomSchema,
        description="Custom application-specific metadata"
    )

    def get_parameter(self, name: str) -> ParameterSchema | None:
        """Get parameter schema by name."""
        for param in self.input.parameters:
            if param.name == name:
                return param
        return None

    def get_required_parameters(self) -> list[ParameterSchema]:
        """Get list of required parameters."""
        return [p for p in self.input.parameters if p.required]

    def get_ui_visible_parameters(self) -> list[ParameterSchema]:
        """Get list of parameters visible in UI."""
        return [p for p in self.input.parameters if not p.ui_hidden]

    def get_parameters_by_group(self, group: str) -> list[ParameterSchema]:
        """Get parameters in a specific UI group."""
        return [p for p in self.input.parameters if p.ui_group == group]
