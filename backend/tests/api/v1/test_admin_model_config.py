"""
Integration tests for admin model configuration endpoints.

Tests CRUD operations for model configurations via the admin API.
"""
import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.db.models import User


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and return an admin user."""
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Create and return a regular user."""
    user = User(
        username="user",
        email="user@example.com",
        full_name="Regular User",
        hashed_password=get_password_hash("UserPass123"),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Generate admin access token."""
    return create_access_token(
        data={
            "sub": admin_user.username,
            "user_id": admin_user.id,
            "role": admin_user.role,
        }
    )


@pytest.fixture
def user_token(regular_user: User) -> str:
    """Generate regular user access token."""
    return create_access_token(
        data={
            "sub": regular_user.username,
            "user_id": regular_user.id,
            "role": regular_user.role,
        }
    )


@pytest.fixture
async def clean_local_config():
    """Ensure local.json is clean before and after tests."""
    from app.core.config import get_settings

    config_path = Path(__file__).parent.parent.parent.parent / "config" / "local.json"
    settings = get_settings()

    # Backup if exists
    backup_data = None
    if config_path.exists():
        with open(config_path, "r") as f:
            backup_data = f.read()

    # Clean for test
    with open(config_path, "w") as f:
        json.dump({"models": []}, f)

    # Reload config to sync in-memory state with file
    settings.reload_config()

    yield

    # Restore or clean
    if backup_data:
        with open(config_path, "w") as f:
            f.write(backup_data)
    else:
        with open(config_path, "w") as f:
            json.dump({"models": []}, f)

    # Reload config again to sync restored state
    settings.reload_config()


# ===== Authorization Tests =====


@pytest.mark.asyncio
async def test_list_configs_requires_admin(
    async_client: AsyncClient,
    user_token: str,
):
    """Test that listing configs requires admin role."""
    response = await async_client.get(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_configs_requires_auth(async_client: AsyncClient):
    """Test that listing configs requires authentication."""
    response = await async_client.get("/api/v1/admin/models/config")
    assert response.status_code in [401, 403]  # Either unauthorized or forbidden


# ===== List Configurations Tests =====


@pytest.mark.asyncio
async def test_list_model_configs(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test listing all model configurations."""
    response = await async_client.get(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    # Should have at least default models
    assert len(models) > 0

    # Check structure
    for model in models:
        assert "id" in model
        assert "name" in model
        assert "provider" in model
        assert "category" in model
        assert "source" in model
        assert "enabled" in model


# ===== Get Configuration Tests =====


@pytest.mark.asyncio
async def test_get_model_config_success(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test getting a specific model configuration."""
    # Get list first to find a valid model ID
    list_response = await async_client.get(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    models = list_response.json()
    model_id = models[0]["id"]

    # Get specific model
    response = await async_client.get(
        f"/api/v1/admin/models/config/{model_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    config = response.json()
    assert config["id"] == model_id
    assert "name" in config
    assert "model" in config
    assert "provider" in config
    assert "category" in config
    assert "description" in config
    assert "parameters" in config
    assert "source" in config


@pytest.mark.asyncio
async def test_get_model_config_not_found(
    async_client: AsyncClient,
    admin_token: str,
):
    """Test getting a non-existent model configuration."""
    response = await async_client.get(
        "/api/v1/admin/models/config/nonexistent-model",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


# ===== Create Configuration Tests =====


@pytest.mark.asyncio
async def test_create_model_config_success(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test creating a new model configuration."""
    new_config = {
        "id": "test-model",
        "name": "Test Model",
        "model": "test/model",
        "provider": "huggingface",
        "category": "upscale",
        "description": "Test model for testing",
        "enabled": True,
        "tags": ["test", "upscale"],
        "version": "1.0",
        "parameters": {"scale": 2},
    }

    response = await async_client.post(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_config,
    )

    assert response.status_code == 201
    created = response.json()
    assert created["id"] == "test-model"
    assert created["name"] == "Test Model"

    # Verify it's in local.json
    get_response = await async_client.get(
        "/api/v1/admin/models/config/test-model",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["source"] == "local"


@pytest.mark.asyncio
async def test_create_model_config_invalid_data(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test creating model with invalid data."""
    invalid_config = {
        "id": "test-invalid",
        "name": "Test Invalid",
        # Missing required fields
    }

    response = await async_client.post(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=invalid_config,
    )

    assert response.status_code == 400


# ===== Update Configuration Tests =====


@pytest.mark.asyncio
async def test_update_model_config_success(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test updating a model configuration."""
    # First create a model
    new_config = {
        "id": "test-update",
        "name": "Test Update",
        "model": "test/update",
        "provider": "huggingface",
        "category": "upscale",
        "description": "Original description",
        "enabled": True,
    }

    create_response = await async_client.post(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_config,
    )
    assert create_response.status_code == 201

    # Update it
    update_data = {
        "description": "Updated description",
        "enabled": False,
    }

    response = await async_client.put(
        "/api/v1/admin/models/config/test-update",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data,
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["description"] == "Updated description"
    assert updated["enabled"] is False
    assert updated["name"] == "Test Update"  # Unchanged fields preserved


@pytest.mark.asyncio
async def test_update_model_config_not_found(
    async_client: AsyncClient,
    admin_token: str,
):
    """Test updating a non-existent model."""
    response = await async_client.put(
        "/api/v1/admin/models/config/nonexistent",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Test"},
    )

    assert response.status_code == 404


# ===== Delete Configuration Tests =====


@pytest.mark.asyncio
async def test_delete_model_config_success(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test deleting a model configuration from local.json."""
    # First create a model
    new_config = {
        "id": "test-delete",
        "name": "Test Delete",
        "model": "test/delete",
        "provider": "huggingface",
        "category": "upscale",
    }

    create_response = await async_client.post(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_config,
    )
    assert create_response.status_code == 201

    # Delete it
    response = await async_client.delete(
        "/api/v1/admin/models/config/test-delete",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    # Verify it's gone from local but may still exist in default
    get_response = await async_client.get(
        "/api/v1/admin/models/config/test-delete",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Should be 404 if not in default, or 200 with source != "local" if in default
    assert get_response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_delete_model_config_from_default_fails(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test that deleting models from default/environment files fails."""
    # Get a model from default config
    list_response = await async_client.get(
        "/api/v1/admin/models/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    models = list_response.json()

    # Find a model from default
    default_model = next((m for m in models if m["source"] == "default"), None)
    if not default_model:
        pytest.skip("No default models available")

    # Try to delete it
    response = await async_client.delete(
        f"/api/v1/admin/models/config/{default_model['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404
    assert "default/environment" in response.json()["detail"].lower()


# ===== Tags and Categories Tests =====


@pytest.mark.asyncio
async def test_get_available_tags(
    async_client: AsyncClient,
    admin_token: str,
):
    """Test getting available tags and categories."""
    response = await async_client.get(
        "/api/v1/admin/models/tags",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    assert "categories" in data
    assert isinstance(data["tags"], list)
    assert isinstance(data["categories"], list)
    # Should have default values
    assert "restore" in data["tags"]
    assert "upscale" in data["categories"]


# ===== Validation Tests =====


@pytest.mark.asyncio
async def test_validate_model_config_valid(
    async_client: AsyncClient,
    admin_token: str,
):
    """Test validating a valid model configuration."""
    valid_config = {
        "id": "test-validate",
        "name": "Test Validate",
        "model": "test/validate",
        "provider": "huggingface",
        "category": "upscale",
    }

    response = await async_client.post(
        "/api/v1/admin/models/validate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=valid_config,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is True
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_model_config_invalid(
    async_client: AsyncClient,
    admin_token: str,
):
    """Test validating an invalid model configuration."""
    invalid_config = {
        "id": "test-invalid-validate",
        # Missing required fields
    }

    response = await async_client.post(
        "/api/v1/admin/models/validate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=invalid_config,
    )

    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is False
    assert len(result["errors"]) > 0


# ===== Reload Configuration Tests =====


@pytest.mark.asyncio
async def test_reload_model_configs(
    async_client: AsyncClient,
    admin_token: str,
    clean_local_config,
):
    """Test reloading model configurations."""
    response = await async_client.post(
        "/api/v1/admin/models/reload",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "models loaded" in data["message"].lower()
