"""Tests for configuration loading from environment variables."""
import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsLoading:
    """Test Settings class with different environment configurations."""

    def test_default_settings(self):
        """Test settings with default values (test environment)."""
        settings = Settings()

        # In test environment, we get values from .env.test
        assert settings.app_name == "Photo Restoration API - Test"
        assert settings.app_version == "1.0.0-test"
        assert settings.debug is True  # Test environment has debug=True
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://testserver" in settings.cors_origins

    def test_cors_origins_json_format(self, monkeypatch, tmp_path):
        """Test CORS origins with JSON array format in .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text('CORS_ORIGINS=["http://localhost:8000","http://localhost","https://example.com"]')

        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:8000","http://localhost","https://example.com"]')

        settings = Settings()
        assert settings.cors_origins == ["http://localhost:8000", "http://localhost", "https://example.com"]

    def test_cors_origins_alternate_json_format(self, monkeypatch):
        """Test CORS origins with alternative JSON format.

        pydantic-settings 2.7.1 requires JSON array format for list[str] fields.
        This test verifies that different valid JSON arrays work correctly.
        """
        monkeypatch.setenv("CORS_ORIGINS", '["http://api.example.com","https://app.example.com"]')

        settings = Settings()
        assert "http://api.example.com" in settings.cors_origins
        assert "https://app.example.com" in settings.cors_origins

    def test_allowed_extensions_json_format(self, monkeypatch):
        """Test allowed extensions with JSON array format."""
        monkeypatch.setenv("ALLOWED_EXTENSIONS", '[".jpg",".png",".webp"]')

        settings = Settings()
        # Note: Sets are unordered, so we check if the extensions are present
        assert ".jpg" in settings.allowed_extensions
        assert ".png" in settings.allowed_extensions
        assert ".webp" in settings.allowed_extensions
        assert len(settings.allowed_extensions) == 3

    def test_secret_key_override(self, monkeypatch):
        """Test SECRET_KEY can be overridden."""
        test_key = "test_secret_key_at_least_32_characters_long_12345"
        monkeypatch.setenv("SECRET_KEY", test_key)

        settings = Settings()
        assert settings.secret_key == test_key

    def test_database_url_override(self, monkeypatch):
        """Test DATABASE_URL can be overridden."""
        test_db = "postgresql://user:pass@localhost/db"
        monkeypatch.setenv("DATABASE_URL", test_db)

        settings = Settings()
        assert settings.database_url == test_db

    def test_hf_api_key_override(self, monkeypatch):
        """Test HF_API_KEY can be set."""
        test_key = "hf_test_key_12345"
        monkeypatch.setenv("HF_API_KEY", test_key)

        settings = Settings()
        assert settings.hf_api_key == test_key

    def test_debug_mode_true(self, monkeypatch):
        """Test DEBUG mode can be enabled."""
        monkeypatch.setenv("DEBUG", "true")

        settings = Settings()
        assert settings.debug is True

    def test_debug_mode_false(self, monkeypatch):
        """Test DEBUG mode defaults to false."""
        monkeypatch.setenv("DEBUG", "false")

        settings = Settings()
        assert settings.debug is False

    def test_port_override(self, monkeypatch):
        """Test PORT can be overridden."""
        monkeypatch.setenv("PORT", "9000")

        settings = Settings()
        assert settings.port == 9000

    def test_models_config_valid_json(self, monkeypatch):
        """Test MODELS_CONFIG with valid JSON."""
        valid_json = '[{"id":"test","name":"Test Model","model":"test/model","category":"test","description":"Test","parameters":{}}]'
        monkeypatch.setenv("MODELS_CONFIG", valid_json)

        settings = Settings()
        models = settings.get_models()
        assert len(models) == 1
        assert models[0]["id"] == "test"

    def test_models_config_invalid_json(self, monkeypatch):
        """Test MODELS_CONFIG with invalid JSON raises error."""
        monkeypatch.setenv("MODELS_CONFIG", "not valid json")

        with pytest.raises(ValidationError):
            Settings()

    def test_get_model_by_id(self):
        """Test getting model configuration by ID."""
        settings = Settings()

        model = settings.get_model_by_id("swin2sr-2x")
        assert model is not None
        assert model["name"] == "Swin2SR 2x Upscale"

        # Non-existent model
        model = settings.get_model_by_id("non-existent")
        assert model is None

    def test_file_storage_paths(self):
        """Test file storage paths are Path objects (test environment)."""
        settings = Settings()

        assert isinstance(settings.upload_dir, Path)
        assert isinstance(settings.processed_dir, Path)
        # In test environment, paths are under test_data/
        assert settings.upload_dir == Path("./test_data/uploads")
        assert settings.processed_dir == Path("./test_data/processed")

    def test_max_upload_size(self):
        """Test max upload size default."""
        settings = Settings()
        assert settings.max_upload_size == 10 * 1024 * 1024  # 10MB

    def test_session_cleanup_hours(self, monkeypatch):
        """Test session cleanup hours can be configured."""
        monkeypatch.setenv("SESSION_CLEANUP_HOURS", "48")

        settings = Settings()
        assert settings.session_cleanup_hours == 48


class TestEnvironmentVariableCaseSensitivity:
    """Test that environment variables are case-insensitive."""

    def test_lowercase_env_vars(self, monkeypatch):
        """Test lowercase environment variable names work."""
        monkeypatch.setenv("cors_origins", '["http://test.com"]')
        monkeypatch.setenv("debug", "true")

        settings = Settings()
        assert settings.cors_origins == ["http://test.com"]
        assert settings.debug is True

    def test_uppercase_env_vars(self, monkeypatch):
        """Test uppercase environment variable names work."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://test.com"]')
        monkeypatch.setenv("DEBUG", "true")

        settings = Settings()
        assert settings.cors_origins == ["http://test.com"]
        assert settings.debug is True


class TestProductionConfiguration:
    """Test production-like configuration scenarios."""

    def test_production_config(self, monkeypatch):
        """Test a typical production configuration."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "production_secret_key_at_least_32_characters_long")
        monkeypatch.setenv("CORS_ORIGINS", '["https://app.example.com","https://www.example.com"]')
        monkeypatch.setenv("HF_API_KEY", "hf_production_key")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/photo_restoration")

        settings = Settings()

        assert settings.debug is False
        assert settings.secret_key == "production_secret_key_at_least_32_characters_long"
        assert len(settings.cors_origins) == 2
        assert "https://app.example.com" in settings.cors_origins
        assert settings.hf_api_key == "hf_production_key"
        assert "postgresql" in settings.database_url
