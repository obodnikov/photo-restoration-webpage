"""Tests for schema validator."""
import pytest

from app.core.replicate_schema import (
    CustomSchema,
    ImageInputSchema,
    InputSchema,
    OutputSchema,
    ParameterSchema,
    ReplicateModelSchema,
)
from app.services.schema_validator import SchemaValidator, ValidationWarning


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing."""
    return ReplicateModelSchema(
        input=InputSchema(
            image=ImageInputSchema(param_name="input_image"),
            parameters=[
                ParameterSchema(
                    name="output_format",
                    type="enum",
                    values=["jpg", "png"],
                    default="png",
                    required=False
                ),
                ParameterSchema(
                    name="quality",
                    type="integer",
                    min=1,
                    max=100,
                    default=80,
                    required=False
                ),
                ParameterSchema(
                    name="required_param",
                    type="string",
                    required=True
                ),
                ParameterSchema(
                    name="enable_feature",
                    type="boolean",
                    default=False,
                    required=False
                )
            ]
        ),
        output=OutputSchema(type="uri"),
        custom=CustomSchema(
            max_file_size_mb=10,
            supported_formats=["jpg", "png", "webp"]
        )
    )


def test_validate_parameters_success(sample_schema):
    """Test successful parameter validation."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "required_param": "test_value",
        "output_format": "jpg",
        "quality": 90
    }

    validated = validator.validate_parameters(parameters)

    assert validated["required_param"] == "test_value"
    assert validated["output_format"] == "jpg"
    assert validated["quality"] == 90
    assert validated["enable_feature"] is False  # Default applied
    assert not validator.has_warnings()


def test_validate_parameters_missing_required(sample_schema):
    """Test validation fails for missing required parameter."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "output_format": "jpg"
    }

    with pytest.raises(ValueError, match="Required parameter 'required_param' is missing"):
        validator.validate_parameters(parameters)


def test_validate_parameters_applies_defaults(sample_schema):
    """Test that defaults are applied for missing optional parameters."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "required_param": "test"
    }

    validated = validator.validate_parameters(parameters)

    assert validated["output_format"] == "png"  # Default
    assert validated["quality"] == 80  # Default
    assert validated["enable_feature"] is False  # Default


def test_validate_integer_type_invalid(sample_schema):
    """Test integer type validation with invalid value."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "required_param": "test",
        "quality": "not_an_integer"
    }

    validated = validator.validate_parameters(parameters)

    # Should use default and produce warning
    assert validated["quality"] == 80
    assert validator.has_warnings()
    assert any("Expected integer" in str(w) for w in validator.get_warnings())


def test_validate_integer_min_max_constraints(sample_schema):
    """Test integer min/max constraints."""
    validator = SchemaValidator(sample_schema)

    # Test below minimum
    parameters = {
        "required_param": "test",
        "quality": -10
    }

    validated = validator.validate_parameters(parameters)
    assert validated["quality"] == 1  # Clamped to min
    assert validator.has_warnings()

    # Test above maximum
    validator2 = SchemaValidator(sample_schema)
    parameters = {
        "required_param": "test",
        "quality": 150
    }

    validated = validator2.validate_parameters(parameters)
    assert validated["quality"] == 100  # Clamped to max
    assert validator2.has_warnings()


def test_validate_enum_invalid_value(sample_schema):
    """Test enum validation with invalid value."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "required_param": "test",
        "output_format": "gif"  # Not in ["jpg", "png"]
    }

    validated = validator.validate_parameters(parameters)

    # Should use default and produce warning
    assert validated["output_format"] == "png"
    assert validator.has_warnings()
    assert any("not in allowed values" in str(w) for w in validator.get_warnings())


def test_validate_boolean_type_invalid(sample_schema):
    """Test boolean type validation with invalid value."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "required_param": "test",
        "enable_feature": "yes"  # Not a boolean
    }

    validated = validator.validate_parameters(parameters)

    # Should use default and produce warning
    assert validated["enable_feature"] is False
    assert validator.has_warnings()


def test_validate_unknown_parameter(sample_schema):
    """Test warning for unknown parameters."""
    validator = SchemaValidator(sample_schema)

    parameters = {
        "required_param": "test",
        "unknown_param": "value"
    }

    validated = validator.validate_parameters(parameters)

    # Unknown param should not be in validated
    assert "unknown_param" not in validated
    assert validator.has_warnings()
    assert any("Unknown parameter" in str(w) for w in validator.get_warnings())


def test_validate_image_constraints_success(sample_schema):
    """Test successful image constraint validation."""
    validator = SchemaValidator(sample_schema)

    # 1MB image
    image_bytes = b"fake_image_data" * 70000  # ~1MB
    validator.validate_image_constraints(image_bytes, "jpg")

    # Should not raise exception


def test_validate_image_constraints_size_exceeded(sample_schema):
    """Test image size constraint."""
    validator = SchemaValidator(sample_schema)

    # 15MB image (exceeds 10MB limit)
    image_bytes = b"x" * (15 * 1024 * 1024)

    with pytest.raises(ValueError, match="exceeds maximum"):
        validator.validate_image_constraints(image_bytes, "jpg")


def test_validate_image_constraints_format_invalid(sample_schema):
    """Test image format constraint."""
    validator = SchemaValidator(sample_schema)

    image_bytes = b"fake_image_data"

    with pytest.raises(ValueError, match="not supported"):
        validator.validate_image_constraints(image_bytes, "bmp")


def test_validate_image_constraints_format_normalization(sample_schema):
    """Test that image formats are normalized correctly."""
    validator = SchemaValidator(sample_schema)

    image_bytes = b"fake_image_data"

    # These should all work (normalization)
    validator.validate_image_constraints(image_bytes, ".jpg")
    validator.validate_image_constraints(image_bytes, "JPG")
    validator.validate_image_constraints(image_bytes, ".PNG")
    validator.validate_image_constraints(image_bytes, "webp")


def test_validation_warning_str():
    """Test ValidationWarning string representation."""
    warning = ValidationWarning("field_name", "Something went wrong", "default_value")
    assert "field_name" in str(warning)
    assert "Something went wrong" in str(warning)
    assert "default_value" in str(warning)

    warning2 = ValidationWarning("field_name", "Error message")
    assert "field_name" in str(warning2)
    assert "Error message" in str(warning2)
