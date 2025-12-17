"""Tests for configuration loading from JSON files."""
import json
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

        with patch("app.core.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
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
