"""Tests for Replicate schema models."""
import pytest
from pydantic import ValidationError

from app.core.replicate_schema import (
    CustomSchema,
    ImageInputSchema,
    InputSchema,
    OutputSchema,
    ParameterSchema,
    ReplicateModelSchema,
)


def test_image_input_schema():
    """Test ImageInputSchema validation."""
    schema = ImageInputSchema(
        param_name="input_image",
        type="uri",
        format="image",
        required=True,
        description="Test image input"
    )

    assert schema.param_name == "input_image"
    assert schema.type == "uri"
    assert schema.format == "image"
    assert schema.required is True


def test_parameter_schema_integer():
    """Test ParameterSchema with integer type."""
    param = ParameterSchema(
        name="safety_tolerance",
        type="integer",
        required=False,
        min=0,
        max=2,
        default=2,
        description="Safety level"
    )

    assert param.name == "safety_tolerance"
    assert param.type == "integer"
    assert param.min == 0
    assert param.max == 2
    assert param.default == 2


def test_parameter_schema_enum():
    """Test ParameterSchema with enum type."""
    param = ParameterSchema(
        name="output_format",
        type="enum",
        values=["jpg", "png"],
        default="png",
        description="Output format"
    )

    assert param.type == "enum"
    assert param.values == ["jpg", "png"]
    assert param.default == "png"


def test_parameter_schema_enum_requires_values():
    """Test that enum type requires values list."""
    with pytest.raises(ValidationError):
        ParameterSchema(
            name="test",
            type="enum",
            description="Test"
        )


def test_parameter_schema_ui_hints():
    """Test UI hint fields."""
    param = ParameterSchema(
        name="seed",
        type="integer",
        ui_hidden=True,
        ui_group="advanced"
    )

    assert param.ui_hidden is True
    assert param.ui_group == "advanced"


def test_custom_schema():
    """Test CustomSchema validation."""
    custom = CustomSchema(
        max_file_size_mb=15,
        supported_formats=["jpg", "png", "webp"],
        estimated_time_seconds=45
    )

    assert custom.max_file_size_mb == 15
    assert custom.supported_formats == ["jpg", "png", "webp"]
    assert custom.estimated_time_seconds == 45


def test_custom_schema_normalizes_formats():
    """Test that supported_formats are normalized."""
    custom = CustomSchema(
        supported_formats=[".JPG", "PNG", ".webp"]
    )

    assert custom.supported_formats == ["jpg", "png", "webp"]


def test_replicate_model_schema():
    """Test complete ReplicateModelSchema."""
    schema = ReplicateModelSchema(
        input=InputSchema(
            image=ImageInputSchema(
                param_name="input_image",
                type="uri",
                format="image",
                required=True
            ),
            parameters=[
                ParameterSchema(
                    name="output_format",
                    type="enum",
                    values=["jpg", "png"],
                    default="png"
                ),
                ParameterSchema(
                    name="quality",
                    type="integer",
                    min=1,
                    max=100,
                    default=90
                )
            ]
        ),
        output=OutputSchema(
            type="uri",
            format="image"
        ),
        custom=CustomSchema(
            max_file_size_mb=10,
            supported_formats=["jpg", "png"]
        )
    )

    assert schema.input.image.param_name == "input_image"
    assert len(schema.input.parameters) == 2
    assert schema.output.type == "uri"


def test_get_parameter():
    """Test get_parameter method."""
    schema = ReplicateModelSchema(
        input=InputSchema(
            image=ImageInputSchema(param_name="image"),
            parameters=[
                ParameterSchema(name="param1", type="string"),
                ParameterSchema(name="param2", type="integer")
            ]
        ),
        output=OutputSchema(type="uri")
    )

    param = schema.get_parameter("param1")
    assert param is not None
    assert param.name == "param1"

    param = schema.get_parameter("nonexistent")
    assert param is None


def test_get_required_parameters():
    """Test get_required_parameters method."""
    schema = ReplicateModelSchema(
        input=InputSchema(
            image=ImageInputSchema(param_name="image"),
            parameters=[
                ParameterSchema(name="required1", type="string", required=True),
                ParameterSchema(name="optional1", type="string", required=False),
                ParameterSchema(name="required2", type="integer", required=True)
            ]
        ),
        output=OutputSchema(type="uri")
    )

    required = schema.get_required_parameters()
    assert len(required) == 2
    assert all(p.required for p in required)
    assert {p.name for p in required} == {"required1", "required2"}


def test_get_ui_visible_parameters():
    """Test get_ui_visible_parameters method."""
    schema = ReplicateModelSchema(
        input=InputSchema(
            image=ImageInputSchema(param_name="image"),
            parameters=[
                ParameterSchema(name="visible1", type="string", ui_hidden=False),
                ParameterSchema(name="hidden1", type="string", ui_hidden=True),
                ParameterSchema(name="visible2", type="integer", ui_hidden=False)
            ]
        ),
        output=OutputSchema(type="uri")
    )

    visible = schema.get_ui_visible_parameters()
    assert len(visible) == 2
    assert all(not p.ui_hidden for p in visible)
    assert {p.name for p in visible} == {"visible1", "visible2"}


def test_get_parameters_by_group():
    """Test get_parameters_by_group method."""
    schema = ReplicateModelSchema(
        input=InputSchema(
            image=ImageInputSchema(param_name="image"),
            parameters=[
                ParameterSchema(name="param1", type="string", ui_group="output"),
                ParameterSchema(name="param2", type="string", ui_group="quality"),
                ParameterSchema(name="param3", type="string", ui_group="output")
            ]
        ),
        output=OutputSchema(type="uri")
    )

    output_params = schema.get_parameters_by_group("output")
    assert len(output_params) == 2
    assert {p.name for p in output_params} == {"param1", "param3"}

    quality_params = schema.get_parameters_by_group("quality")
    assert len(quality_params) == 1
    assert quality_params[0].name == "param2"
