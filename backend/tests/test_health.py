"""Tests for health check endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_returns_200(self, client: TestClient):
        """Test /health returns 200 with correct JSON."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "app" in data
        assert "version" in data

        # Verify values
        assert data["status"] == "healthy"
        assert data["app"] == "Photo Restoration API - Test"
        assert data["version"] == "1.0.0-test"

    def test_root_endpoint_returns_api_info(self, client: TestClient):
        """Test / returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "version" in data
        assert "docs" in data

        # Verify values
        assert data["message"] == "Photo Restoration API"
        assert data["version"] == "1.0.0-test"
        assert data["docs"] == "/api/docs"


@pytest.mark.integration
class TestAppStartupValidation:
    """Test application startup validation and configuration."""

    def test_app_startup_with_valid_config(self, client: TestClient):
        """Test app starts successfully with valid configuration."""
        # The app should already be running via the client fixture
        response = client.get("/health")
        assert response.status_code == 200

    def test_models_config_loaded(self, client: TestClient, test_settings):
        """Test MODELS_CONFIG is loaded and parsed correctly."""
        models = test_settings.get_models()

        # Should have at least one test model
        assert len(models) >= 1

        # Verify test model structure
        test_model = models[0]
        assert "id" in test_model
        assert "name" in test_model
        assert "model" in test_model
        assert "category" in test_model
        assert "description" in test_model

    def test_secret_key_configured(self, test_settings):
        """Test SECRET_KEY is configured and meets minimum length."""
        assert test_settings.secret_key is not None
        assert len(test_settings.secret_key) >= 32

    def test_hf_api_key_configured(self, test_settings):
        """Test HF_API_KEY is configured in test environment."""
        assert test_settings.hf_api_key is not None
        assert len(test_settings.hf_api_key) > 0

    def test_data_directories_exist(self, test_settings):
        """Test upload and processed directories are created."""
        assert test_settings.upload_dir.exists()
        assert test_settings.processed_dir.exists()

    def test_cors_origins_configured(self, test_settings):
        """Test CORS origins are configured correctly."""
        assert isinstance(test_settings.cors_origins, list)
        assert len(test_settings.cors_origins) > 0

        # Test environment should have testserver in CORS origins
        assert any("testserver" in origin for origin in test_settings.cors_origins)


@pytest.mark.unit
class TestModelsConfigParsing:
    """Test MODELS_CONFIG parsing and validation."""

    def test_get_models_returns_list(self, test_settings):
        """Test get_models() returns a list of models."""
        models = test_settings.get_models()

        assert isinstance(models, list)
        assert len(models) > 0

    def test_get_model_by_id_valid(self, test_settings):
        """Test get_model_by_id() with valid model ID."""
        # Get first model from config
        models = test_settings.get_models()
        first_model_id = models[0]["id"]

        # Retrieve it by ID
        model = test_settings.get_model_by_id(first_model_id)

        assert model is not None
        assert model["id"] == first_model_id

    def test_get_model_by_id_invalid(self, test_settings):
        """Test get_model_by_id() with invalid model ID returns None."""
        model = test_settings.get_model_by_id("non-existent-model-12345")

        assert model is None

    def test_models_have_required_fields(self, test_settings):
        """Test all models have required fields."""
        models = test_settings.get_models()

        required_fields = ["id", "name", "model", "category", "description"]

        for model in models:
            for field in required_fields:
                assert field in model, f"Model missing required field: {field}"
                assert model[field], f"Model has empty {field}"


@pytest.mark.security
class TestConfigurationSecurity:
    """Test security-related configuration."""

    def test_secret_key_not_default_in_production(self, test_settings):
        """Test SECRET_KEY is not using default/example value."""
        # In test environment, we use a fixed key for deterministic tests
        # So we just verify it meets minimum length requirements
        assert len(test_settings.secret_key) >= 32, \
            "SECRET_KEY must be at least 32 characters for security"

        # Verify it's not the exact production default
        assert test_settings.secret_key != "CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY", \
            "SECRET_KEY is still using production default value"

    def test_debug_mode_in_test(self, test_settings):
        """Test DEBUG mode is enabled in test environment."""
        # For test environment, debug should be True
        assert test_settings.debug is True

    def test_allowed_extensions_valid(self, test_settings):
        """Test ALLOWED_EXTENSIONS contains valid image extensions."""
        assert ".jpg" in test_settings.allowed_extensions or \
               ".jpeg" in test_settings.allowed_extensions
        assert ".png" in test_settings.allowed_extensions

    def test_max_upload_size_reasonable(self, test_settings):
        """Test MAX_UPLOAD_SIZE is set to a reasonable value."""
        # Should be set (not None)
        assert test_settings.max_upload_size is not None

        # Should be positive
        assert test_settings.max_upload_size > 0

        # Should be reasonable (between 1MB and 100MB)
        assert test_settings.max_upload_size >= 1 * 1024 * 1024  # At least 1MB
        assert test_settings.max_upload_size <= 100 * 1024 * 1024  # At most 100MB
