"""
Schema validation service for Replicate models.

This module provides parameter validation, default application,
and image constraint checking for Replicate models.
"""
import logging
from typing import Any

from app.core.replicate_schema import ParameterSchema, ReplicateModelSchema

logger = logging.getLogger(__name__)


class ValidationWarning:
    """Validation warning that doesn't stop execution."""

    def __init__(self, field: str, message: str, applied_value: Any = None):
        self.field = field
        self.message = message
        self.applied_value = applied_value

    def __str__(self) -> str:
        if self.applied_value is not None:
            return f"{self.field}: {self.message} (applied: {self.applied_value})"
        return f"{self.field}: {self.message}"


class SchemaValidator:
    """Validator for Replicate model parameters and constraints."""

    def __init__(self, schema: ReplicateModelSchema):
        """
        Initialize validator with schema.

        Args:
            schema: Replicate model schema
        """
        self.schema = schema
        self.warnings: list[ValidationWarning] = []

    def validate_parameters(
        self,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate and normalize parameters against schema.

        Applies defaults for missing optional parameters.
        Logs warnings for invalid values and uses defaults.

        Args:
            parameters: User-provided parameters

        Returns:
            Validated and normalized parameters

        Raises:
            ValueError: If required parameters are missing
        """
        self.warnings = []
        validated = {}

        # Check required parameters
        for param_schema in self.schema.get_required_parameters():
            if param_schema.name not in parameters:
                raise ValueError(
                    f"Required parameter '{param_schema.name}' is missing"
                )

        # Validate each parameter in schema
        for param_schema in self.schema.input.parameters:
            param_name = param_schema.name

            if param_name in parameters:
                # Validate provided value
                value = parameters[param_name]
                validated_value = self._validate_parameter_value(
                    param_schema, value
                )
                validated[param_name] = validated_value
            elif param_schema.default is not None:
                # Apply default for optional parameter
                validated[param_name] = param_schema.default
                logger.debug(
                    f"Parameter '{param_name}' not provided, using default: "
                    f"{param_schema.default}"
                )

        # Warn about unknown parameters (not in schema)
        for param_name in parameters:
            if not self.schema.get_parameter(param_name):
                self.warnings.append(
                    ValidationWarning(
                        param_name,
                        f"Unknown parameter (not in schema), ignoring"
                    )
                )
                logger.warning(
                    f"Parameter '{param_name}' not in schema, ignoring"
                )

        # Log warnings
        if self.warnings:
            logger.warning(
                f"Validation produced {len(self.warnings)} warning(s): "
                f"{[str(w) for w in self.warnings]}"
            )

        return validated

    def _validate_parameter_value(
        self,
        param_schema: ParameterSchema,
        value: Any
    ) -> Any:
        """
        Validate a single parameter value.

        Logs warnings and applies defaults for invalid values.

        Args:
            param_schema: Parameter schema
            value: User-provided value

        Returns:
            Validated value (or default if invalid)
        """
        param_name = param_schema.name

        # Type validation
        if param_schema.type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                warning = ValidationWarning(
                    param_name,
                    f"Expected integer, got {type(value).__name__}",
                    param_schema.default
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.default

            # Min/max constraints
            if param_schema.min is not None and value < param_schema.min:
                warning = ValidationWarning(
                    param_name,
                    f"Value {value} below minimum {param_schema.min}",
                    param_schema.min
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.min

            if param_schema.max is not None and value > param_schema.max:
                warning = ValidationWarning(
                    param_name,
                    f"Value {value} above maximum {param_schema.max}",
                    param_schema.max
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.max

        elif param_schema.type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                warning = ValidationWarning(
                    param_name,
                    f"Expected float, got {type(value).__name__}",
                    param_schema.default
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.default

            # Min/max constraints
            if param_schema.min is not None and value < param_schema.min:
                warning = ValidationWarning(
                    param_name,
                    f"Value {value} below minimum {param_schema.min}",
                    param_schema.min
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.min

            if param_schema.max is not None and value > param_schema.max:
                warning = ValidationWarning(
                    param_name,
                    f"Value {value} above maximum {param_schema.max}",
                    param_schema.max
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.max

        elif param_schema.type == "boolean":
            if not isinstance(value, bool):
                warning = ValidationWarning(
                    param_name,
                    f"Expected boolean, got {type(value).__name__}",
                    param_schema.default
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.default

        elif param_schema.type == "string":
            if not isinstance(value, str):
                warning = ValidationWarning(
                    param_name,
                    f"Expected string, got {type(value).__name__}",
                    param_schema.default
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.default

        elif param_schema.type == "enum":
            if value not in param_schema.values:
                warning = ValidationWarning(
                    param_name,
                    f"Value '{value}' not in allowed values {param_schema.values}",
                    param_schema.default
                )
                self.warnings.append(warning)
                logger.warning(str(warning))
                return param_schema.default

        return value

    def validate_image_constraints(
        self,
        image_bytes: bytes,
        image_format: str
    ) -> None:
        """
        Validate image against custom constraints.

        Args:
            image_bytes: Image file bytes
            image_format: Image format (e.g., 'jpg', 'png')

        Raises:
            ValueError: If image violates constraints
        """
        custom = self.schema.custom

        # Check file size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > custom.max_file_size_mb:
            raise ValueError(
                f"Image size {size_mb:.2f}MB exceeds maximum "
                f"{custom.max_file_size_mb}MB"
            )

        # Check format
        # Normalize format (remove dot, lowercase)
        normalized_format = image_format.lower().lstrip(".")

        if normalized_format not in custom.supported_formats:
            raise ValueError(
                f"Image format '{image_format}' not supported. "
                f"Supported formats: {', '.join(custom.supported_formats)}"
            )

        logger.debug(
            f"Image constraints validated: {size_mb:.2f}MB, format={normalized_format}"
        )

    def get_warnings(self) -> list[ValidationWarning]:
        """Get list of validation warnings."""
        return self.warnings

    def has_warnings(self) -> bool:
        """Check if validation produced warnings."""
        return len(self.warnings) > 0
