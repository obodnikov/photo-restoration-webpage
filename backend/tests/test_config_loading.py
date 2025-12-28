"""Tests for configuration loading from JSON files."""
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import Settings, deep_merge, load_config_from_files, load_json_config


class TestDeepMerge:
    """Tests for deep_merge utility function."""

    def test_simple_merge(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test merging nested dictionaries."""
        base = {"server": {"host": "0.0.0.0", "port": 8000}}
        override = {"server": {"port": 9000}}
        result = deep_merge(base, override)
        assert result == {"server": {"host": "0.0.0.0", "port": 9000}}

    def test_deep_nested_merge(self):
        """Test merging deeply nested dictionaries."""
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"d": 3, "e": 4}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": 1, "d": 3, "e": 4}}}

    def test_override_with_different_type(self):
        """Test that override replaces value even if type changes."""
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        result = deep_merge(base, override)
        assert result == {"a": "string"}

    def test_base_not_modified(self):
        """Test that original base dict is not modified."""
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge(base, override)
        assert base == {"a": 1}  # Original unchanged
        assert result == {"a": 1, "b": 2}


class TestLoadJsonConfig:
    """Tests for load_json_config function."""

    def test_load_valid_json(self, tmp_path):
        """Test loading valid JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {"application": {"name": "Test API"}}
        config_file.write_text(json.dumps(config_data))

        result = load_json_config(config_file)
        assert result == config_data

    def test_file_not_found(self, tmp_path):
        """Test error when file doesn't exist."""
        config_file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_json_config(config_file)

    def test_invalid_json(self, tmp_path):
        """Test error with invalid JSON."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{invalid json")
        with pytest.raises(json.JSONDecodeError):
            load_json_config(config_file)


class TestLoadConfigFromFiles:
    """Tests for load_config_from_files function."""

    def test_load_default_only(self, tmp_path, monkeypatch):
        """Test loading only default config."""
        # Mock config directory
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        default_config = {"application": {"name": "Default"}}
        (config_dir / "default.json").write_text(json.dumps(default_config))

        # Patch config directory path
        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            result = load_config_from_files("development")

        assert result == default_config

    def test_load_with_environment_override(self, tmp_path, monkeypatch):
        """Test loading default + environment-specific config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        default_config = {"application": {"name": "Default", "debug": False}}
        (config_dir / "default.json").write_text(json.dumps(default_config))

        dev_config = {"application": {"debug": True}}
        (config_dir / "development.json").write_text(json.dumps(dev_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            result = load_config_from_files("development")

        assert result == {"application": {"name": "Default", "debug": True}}

    def test_default_not_found(self, tmp_path):
        """Test when default.json doesn't exist."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            result = load_config_from_files("production")

        assert result == {}


class TestSettingsLoading:
    """Tests for Settings class with JSON config loading."""

    def test_load_from_json_config(self, tmp_path, monkeypatch):
        """Test Settings loads from JSON config files."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config = {
            "application": {"name": "Test API", "version": "1.8.2", "debug": True},
            "server": {"host": "127.0.0.1", "port": 9000},
            "models": [],
        }
        (config_dir / "default.json").write_text(json.dumps(config))

        # Create a proper Path mock that returns the tmp_path when navigating up
        def path_side_effect(*args, **kwargs):
            if args and args[0] == __file__:
                mock_file_path = tmp_path / "fake.py"
                return mock_file_path
            return Path(*args, **kwargs)

        with patch("app.core.config.Path", side_effect=path_side_effect):
            settings = Settings(app_env="development")

        assert settings.app_name == "Test API"
        assert settings.app_version == "1.8.2"
        assert settings.debug is True
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.is_using_json_config() is True

    def test_env_var_overrides_json_config(self, tmp_path, monkeypatch):
        """Test that environment variables override JSON config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config = {"application": {"debug": False}, "server": {"port": 8000}}
        (config_dir / "default.json").write_text(json.dumps(config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            settings = Settings(app_env="development", debug=True, port=9000)

        assert settings.debug is True  # ENV override
        assert settings.port == 9000  # ENV override

    def test_fallback_to_env_only(self, tmp_path, monkeypatch):
        """Test fallback to .env when config files missing."""
        # No config directory
        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            with pytest.warns(DeprecationWarning, match="Using .env-only configuration is deprecated"):
                settings = Settings(app_env="development")

        # Should still work with defaults
        assert settings.app_name == "Photo Restoration API"
        assert settings.is_using_json_config() is False

    def test_get_models_from_json_config(self, tmp_path):
        """Test get_models() returns models from JSON config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        models = [
            {
                "id": "test-model",
                "name": "Test Model",
                "model": "test/model",
                "provider": "huggingface",
                "category": "test",
                "description": "Test",
                "enabled": True,
            }
        ]
        config = {"models": models}
        (config_dir / "default.json").write_text(json.dumps(config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            settings = Settings(app_env="development")

        assert settings.get_models() == models

    def test_get_models_fallback_to_env(self):
        """Test get_models() falls back to MODELS_CONFIG env var."""
        # Mock no JSON config available
        with patch("app.core.config.load_config_from_files", return_value={}):
            with pytest.warns(DeprecationWarning):
                settings = Settings(app_env="development")

        models = settings.get_models()
        assert isinstance(models, list)
        assert len(models) > 0  # Should have default model from models_config

    def test_get_model_by_id(self, tmp_path):
        """Test get_model_by_id() finds model."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        models = [
            {
                "id": "model-1",
                "name": "Model 1",
                "model": "test/model1",
                "provider": "huggingface",
                "category": "test",
                "description": "Test 1",
            }
        ]
        config = {"models": models}
        (config_dir / "default.json").write_text(json.dumps(config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            settings = Settings(app_env="development")

        model = settings.get_model_by_id("model-1")
        assert model is not None
        assert model["name"] == "Model 1"

        # Non-existent model
        assert settings.get_model_by_id("nonexistent") is None

    def test_invalid_json_config_fallback(self, tmp_path):
        """Test fallback when JSON config is invalid."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Invalid JSON
        (config_dir / "default.json").write_text("{invalid")

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            with pytest.warns(UserWarning, match="Config file error"):
                settings = Settings(app_env="development")

        # Should fall back to .env defaults
        assert settings.is_using_json_config() is False


class TestLocalJsonConfig:
    """Tests for local.json configuration behavior (model-only merging)."""

    def test_local_json_merges_models_only(self, tmp_path, caplog):
        """Test that local.json only merges models array, ignoring other keys."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Base configuration
        default_config = {
            "application": {"name": "Default App", "debug": False},
            "server": {"host": "0.0.0.0", "port": 8000},
            "models": [
                {"id": "model-1", "name": "Model 1", "enabled": True},
                {"id": "model-2", "name": "Model 2", "enabled": True},
            ],
        }
        (config_dir / "default.json").write_text(json.dumps(default_config))

        # Local config with models AND other keys
        local_config = {
            "models": [
                {"id": "model-2", "name": "Model 2 (Local)", "enabled": False},
                {"id": "model-3", "name": "Model 3 (Test)", "enabled": True},
            ],
            "application": {"debug": True, "name": "Local App"},  # Should be ignored
            "server": {"port": 9000},  # Should be ignored
            "database": {"url": "sqlite:///local.db"},  # Should be ignored
        }
        (config_dir / "local.json").write_text(json.dumps(local_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            result = load_config_from_files("development")

        # Models should be merged
        assert len(result["models"]) == 3
        assert result["models"][0]["id"] == "model-1"
        assert result["models"][0]["name"] == "Model 1"
        assert result["models"][1]["id"] == "model-2"
        assert result["models"][1]["name"] == "Model 2 (Local)"
        assert result["models"][1]["enabled"] is False
        assert result["models"][2]["id"] == "model-3"
        assert result["models"][2]["name"] == "Model 3 (Test)"

        # Other keys should remain from default, NOT from local
        assert result["application"]["name"] == "Default App"
        assert result["application"]["debug"] is False
        assert result["server"]["port"] == 8000
        assert "database" not in result

    def test_local_json_warns_about_ignored_keys(self, tmp_path, caplog):
        """Test that warning is logged when local.json contains non-model keys."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        default_config = {"models": []}
        (config_dir / "default.json").write_text(json.dumps(default_config))

        local_config = {
            "models": [{"id": "test", "name": "Test"}],
            "application": {"debug": True},
            "server": {"port": 9000},
        }
        (config_dir / "local.json").write_text(json.dumps(local_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            with caplog.at_level(logging.WARNING):
                load_config_from_files("development")

        # Check warning was logged
        assert any("local.json contains non-model keys" in record.message for record in caplog.records)
        assert any("application" in record.message and "server" in record.message for record in caplog.records)

    def test_local_json_models_only_no_warning(self, tmp_path, caplog):
        """Test that no warning is logged when local.json only contains models."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        default_config = {"models": []}
        (config_dir / "default.json").write_text(json.dumps(default_config))

        local_config = {
            "models": [{"id": "test", "name": "Test"}],
        }
        (config_dir / "local.json").write_text(json.dumps(local_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            with caplog.at_level(logging.WARNING):
                load_config_from_files("development")

        # No warning should be logged
        assert not any("local.json contains non-model keys" in record.message for record in caplog.records)

    def test_local_json_with_env_specific_config(self, tmp_path):
        """Test that local.json models merge correctly with environment-specific config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Default config
        default_config = {
            "application": {"debug": False},
            "models": [{"id": "model-1", "name": "Default Model"}],
        }
        (config_dir / "default.json").write_text(json.dumps(default_config))

        # Development config overrides application.debug and adds a model
        # Note: deep_merge replaces the entire models array from default
        dev_config = {
            "application": {"debug": True},
            "models": [{"id": "model-2", "name": "Dev Model"}],
        }
        (config_dir / "development.json").write_text(json.dumps(dev_config))

        # Local config adds another model
        local_config = {
            "models": [{"id": "model-3", "name": "Local Model"}],
            "application": {"debug": False},  # Should be ignored
        }
        (config_dir / "local.json").write_text(json.dumps(local_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            result = load_config_from_files("development")

        # Should have 2 models: model-2 from dev (which replaced model-1) and model-3 from local
        assert len(result["models"]) == 2
        model_ids = [m["id"] for m in result["models"]]
        assert "model-2" in model_ids
        assert "model-3" in model_ids

        # application.debug should come from development.json, not local.json
        assert result["application"]["debug"] is True

    def test_local_json_empty_models_array(self, tmp_path):
        """Test that empty models array in local.json is handled correctly."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        default_config = {
            "models": [{"id": "model-1", "name": "Default Model"}],
        }
        (config_dir / "default.json").write_text(json.dumps(default_config))

        # Empty models array in local.json
        local_config = {"models": []}
        (config_dir / "local.json").write_text(json.dumps(local_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            result = load_config_from_files("development")

        # Should keep default model (empty array doesn't override)
        assert len(result["models"]) == 1
        assert result["models"][0]["id"] == "model-1"

    def test_local_json_no_models_key(self, tmp_path, caplog):
        """Test local.json with no models key at all."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        default_config = {
            "models": [{"id": "model-1", "name": "Default Model"}],
        }
        (config_dir / "default.json").write_text(json.dumps(default_config))

        # local.json with only non-model keys
        local_config = {
            "application": {"debug": True},
            "server": {"port": 9000},
        }
        (config_dir / "local.json").write_text(json.dumps(local_config))

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            with caplog.at_level(logging.WARNING):
                result = load_config_from_files("development")

        # Should keep default model
        assert len(result["models"]) == 1
        assert result["models"][0]["id"] == "model-1"

        # Should warn about ignored keys
        assert any("local.json contains non-model keys" in record.message for record in caplog.records)
