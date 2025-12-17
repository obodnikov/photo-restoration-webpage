"""Tests for models API endpoints."""
import json

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture
def test_models_config():
    """Sample models configuration for testing."""
    return [
        {
            "id": "test-model-1",
            "name": "Test Model 1",
            "model": "test/model-1",
            "category": "upscale",
            "description": "Test upscale model",
            "parameters": {"scale": 2},
            "tags": ["test", "upscale"],
            "version": "1.0",
        },
        {
            "id": "test-model-2",
            "name": "Test Model 2",
            "model": "test/model-2",
            "category": "enhance",
            "description": "Test enhancement model",
            "parameters": {"prompt": "enhance"},
            "tags": ["test", "enhance"],
            "version": "2.0",
        },
    ]


@pytest.fixture
def override_settings_public(test_models_config):
    """Override settings with public models access."""
    return Settings(
        secret_key="test-secret-key-min-32-chars-long-for-testing",
        models_config=json.dumps(test_models_config),
        models_require_auth=False,  # Public access
        auth_username="testuser",
        auth_password="testpass",
        hf_api_key="test-key",
    )


@pytest.fixture
def override_settings_protected(test_models_config):
    """Override settings with protected models access."""
    return Settings(
        secret_key="test-secret-key-min-32-chars-long-for-testing",
        models_config=json.dumps(test_models_config),
        models_require_auth=True,  # Require authentication
        auth_username="testuser",
        auth_password="testpass",
        hf_api_key="test-key",
    )


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """Automatically clear dependency overrides before/after each test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class TestModelsListPublic:
    """Tests for GET /api/v1/models with public access."""

    def test_list_models_returns_all_models(
        self, client: TestClient, override_settings_public
    ):
        """Test that GET /models returns all configured models."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "models" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["models"]) == 2

    def test_list_models_includes_all_fields(
        self, client: TestClient, override_settings_public
    ):
        """Test that model response includes all required fields."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        model = data["models"][0]

        # Check all required fields
        assert "id" in model
        assert "name" in model
        assert "model" in model
        assert "category" in model
        assert "description" in model
        assert "parameters" in model
        assert "tags" in model
        assert "version" in model

    def test_list_models_returns_correct_data(
        self, client: TestClient, override_settings_public
    ):
        """Test that model data matches configuration."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        models = data["models"]

        # Verify first model
        model1 = next(m for m in models if m["id"] == "test-model-1")
        assert model1["name"] == "Test Model 1"
        assert model1["model"] == "test/model-1"
        assert model1["category"] == "upscale"
        assert model1["description"] == "Test upscale model"
        assert model1["parameters"]["scale"] == 2
        assert "test" in model1["tags"]
        assert model1["version"] == "1.0"

    def test_list_models_no_auth_required_public(
        self, client: TestClient, override_settings_public
    ):
        """Test that no authentication is required when models_require_auth=False."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        # Request without Authorization header should succeed
        response = client.get("/api/v1/models")

        assert response.status_code == status.HTTP_200_OK


class TestModelsListProtected:
    """Tests for GET /api/v1/models with authentication required."""

    def test_list_models_requires_auth_when_protected(
        self, client: TestClient, override_settings_protected
    ):
        """Test that authentication is required when models_require_auth=True."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        # Request without Authorization header should fail
        response = client.get("/api/v1/models")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_models_succeeds_with_valid_token(
        self, client: TestClient, override_settings_protected, valid_token
    ):
        """Test that request succeeds with valid token when protected."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        response = client.get(
            "/api/v1/models", headers={"Authorization": f"Bearer {valid_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "models" in data
        assert data["total"] == 2

    def test_list_models_fails_with_invalid_token(
        self, client: TestClient, override_settings_protected
    ):
        """Test that request fails with invalid token."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        response = client.get(
            "/api/v1/models", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetModelByIdPublic:
    """Tests for GET /api/v1/models/{model_id} with public access."""

    def test_get_model_by_id_returns_model(
        self, client: TestClient, override_settings_public
    ):
        """Test that GET /models/{model_id} returns correct model."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models/test-model-1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == "test-model-1"
        assert data["name"] == "Test Model 1"
        assert data["model"] == "test/model-1"
        assert data["category"] == "upscale"

    def test_get_model_by_id_includes_all_fields(
        self, client: TestClient, override_settings_public
    ):
        """Test that model includes all required fields."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models/test-model-2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "id" in data
        assert "name" in data
        assert "model" in data
        assert "category" in data
        assert "description" in data
        assert "parameters" in data
        assert "tags" in data
        assert "version" in data

    def test_get_model_not_found(self, client: TestClient, override_settings_public):
        """Test that 404 is returned for non-existent model."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models/non-existent-model")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "non-existent-model" in data["detail"]

    def test_get_model_no_auth_required_public(
        self, client: TestClient, override_settings_public
    ):
        """Test that no authentication is required when models_require_auth=False."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        response = client.get("/api/v1/models/test-model-1")

        assert response.status_code == status.HTTP_200_OK


class TestGetModelByIdProtected:
    """Tests for GET /api/v1/models/{model_id} with authentication required."""

    def test_get_model_requires_auth_when_protected(
        self, client: TestClient, override_settings_protected
    ):
        """Test that authentication is required when models_require_auth=True."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        response = client.get("/api/v1/models/test-model-1")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_model_succeeds_with_valid_token(
        self, client: TestClient, override_settings_protected, valid_token
    ):
        """Test that request succeeds with valid token when protected."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        response = client.get(
            "/api/v1/models/test-model-1",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "test-model-1"

    def test_get_model_fails_with_invalid_token(
        self, client: TestClient, override_settings_protected
    ):
        """Test that request fails with invalid token."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        response = client.get(
            "/api/v1/models/test-model-1",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_model_not_found_with_auth(
        self, client: TestClient, override_settings_protected, valid_token
    ):
        """Test that 404 is returned for non-existent model even with valid auth."""
        app.dependency_overrides[get_settings] = lambda: override_settings_protected

        response = client.get(
            "/api/v1/models/non-existent",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestModelsCaching:
    """Tests for models caching behavior."""

    def test_models_are_cached(self, client: TestClient, override_settings_public):
        """Test that models list is cached and not re-parsed on every request."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        # First request
        response1 = client.get("/api/v1/models")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["total"] == 2

        # Second request should use cached data
        response2 = client.get("/api/v1/models")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["total"] == 2
        assert data1 == data2

    def test_settings_override_refreshes_models(
        self, client: TestClient, override_settings_public, test_models_config
    ):
        """Test that updating settings refreshes models."""
        app.dependency_overrides[get_settings] = lambda: override_settings_public

        # First request
        response1 = client.get("/api/v1/models")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["total"] == 2

        # Update config with new settings
        new_config = [
            {
                "id": "new-model",
                "name": "New Model",
                "model": "test/new",
                "category": "test",
                "description": "New test model",
                "parameters": {},
                "tags": [],
                "version": "1.0",
            }
        ]
        new_settings = Settings(
            secret_key="test-secret-key-min-32-chars-long-for-testing",
            models_config=json.dumps(new_config),
            models_require_auth=False,
            auth_username="testuser",
            auth_password="testpass",
            hf_api_key="test-key",
        )
        app.dependency_overrides[get_settings] = lambda: new_settings

        # Second request should get new data
        response2 = client.get("/api/v1/models")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["total"] == 1
        assert data2["models"][0]["id"] == "new-model"
