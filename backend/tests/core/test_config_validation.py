"""Tests for config validation functions."""
import pytest

from app.core.config import validate_ui_parameters


class TestValidateUIParameters:
    """Tests for validate_ui_parameters function."""

    def test_no_models(self):
        """Test with empty models list."""
        result = validate_ui_parameters([])
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_non_replicate_models_ignored(self):
        """Test that non-Replicate models are skipped."""
        models = [
            {
                "id": "hf-model",
                "provider": "huggingface",
                "parameters": {"scale": 2}
            }
        ]
        result = validate_ui_parameters(models)
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_replicate_model_without_schema(self):
        """Test Replicate model without replicate_schema."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "model": "test/model"
                # No replicate_schema
            }
        ]
        result = validate_ui_parameters(models)
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_replicate_model_without_parameters(self):
        """Test Replicate model with schema but no parameters."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"}
                        # No parameters array
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_replicate_model_with_empty_parameters(self):
        """Test Replicate model with empty parameters array."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": []  # Empty
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_replicate_model_missing_ui_hidden(self):
        """Test Replicate model with parameters missing ui_hidden."""
        models = [
            {
                "id": "replicate-restore",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {
                                "name": "output_format",
                                "type": "enum",
                                "values": ["jpg", "png"]
                                # Missing ui_hidden
                            },
                            {
                                "name": "seed",
                                "type": "integer"
                                # Missing ui_hidden
                            }
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert len(result["needs_migration"]) == 1
        assert "replicate-restore" in result["needs_migration"]
        assert len(result["missing_params"]) == 2
        assert "replicate-restore.output_format" in result["missing_params"]
        assert "replicate-restore.seed" in result["missing_params"]

    def test_replicate_model_all_parameters_have_ui_hidden(self):
        """Test Replicate model with all parameters having ui_hidden."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {
                                "name": "param1",
                                "type": "string",
                                "ui_hidden": False
                            },
                            {
                                "name": "param2",
                                "type": "integer",
                                "ui_hidden": True
                            }
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_replicate_model_partial_migration(self):
        """Test Replicate model with some parameters missing ui_hidden."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {
                                "name": "param1",
                                "type": "string",
                                "ui_hidden": False  # Has ui_hidden
                            },
                            {
                                "name": "param2",
                                "type": "integer"
                                # Missing ui_hidden
                            },
                            {
                                "name": "param3",
                                "type": "boolean",
                                "ui_hidden": True  # Has ui_hidden
                            }
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert len(result["needs_migration"]) == 1
        assert "replicate-model" in result["needs_migration"]
        assert len(result["missing_params"]) == 1
        assert "replicate-model.param2" in result["missing_params"]

    def test_multiple_models_mixed_migration_status(self):
        """Test multiple models with different migration statuses."""
        models = [
            {
                "id": "hf-model",
                "provider": "huggingface"  # Should be ignored
            },
            {
                "id": "replicate-good",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {"name": "param1", "type": "string", "ui_hidden": False}
                        ]
                    }
                }
            },
            {
                "id": "replicate-bad",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {"name": "param1", "type": "string"}  # Missing ui_hidden
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert len(result["needs_migration"]) == 1
        assert "replicate-bad" in result["needs_migration"]
        assert "replicate-good" not in result["needs_migration"]
        assert len(result["missing_params"]) == 1
        assert "replicate-bad.param1" in result["missing_params"]

    def test_parameter_without_name(self):
        """Test parameter missing name field."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {
                                # Missing name field
                                "type": "string"
                            }
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert len(result["needs_migration"]) == 1
        assert len(result["missing_params"]) == 1
        assert "replicate-model.unknown" in result["missing_params"]

    def test_malformed_schema_missing_input(self):
        """Test malformed schema missing input field."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    # Missing input field
                    "output": {"type": "uri"}
                }
            }
        ]
        result = validate_ui_parameters(models)
        # Should not crash, should skip gracefully
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_parameters_not_array(self):
        """Test when parameters is not an array."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": "not-an-array"  # Invalid type
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        # Should not crash, should skip gracefully
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_model_without_id(self):
        """Test model missing id field."""
        models = [
            {
                # Missing id
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {"name": "param1", "type": "string"}  # Missing ui_hidden
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        assert len(result["needs_migration"]) == 1
        assert "unknown" in result["needs_migration"]
        assert len(result["missing_params"]) == 1
        assert "unknown.param1" in result["missing_params"]

    def test_parameters_as_dict_instead_of_list(self):
        """Test when parameters is a dict instead of list (schema variation)."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": {  # Dict instead of list!
                            "param1": {"type": "string"},
                            "param2": {"type": "integer"}
                        }
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        # Should skip gracefully, not treat dict keys as params
        assert result["needs_migration"] == []
        assert result["missing_params"] == []

    def test_parameter_list_with_non_dict_elements(self):
        """Test when parameters list contains non-dict elements."""
        models = [
            {
                "id": "replicate-model",
                "provider": "replicate",
                "replicate_schema": {
                    "input": {
                        "image": {"param_name": "input_image", "type": "uri"},
                        "parameters": [
                            {"name": "param1", "type": "string", "ui_hidden": False},
                            "invalid-string-element",  # Invalid!
                            {"name": "param2", "type": "integer"}  # Missing ui_hidden
                        ]
                    }
                }
            }
        ]
        result = validate_ui_parameters(models)
        # Should skip invalid element, process valid ones
        assert len(result["needs_migration"]) == 1
        assert "replicate-model" in result["needs_migration"]
        assert len(result["missing_params"]) == 1
        assert "replicate-model.param2" in result["missing_params"]
        # Should NOT include the invalid element
