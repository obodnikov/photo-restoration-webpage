"""Tests for configuration schemas."""
import pytest
from pydantic import ValidationError

from app.core.config_schema import (
    ApplicationConfig,
    ConfigFile,
    FileStorageConfig,
    ModelConfig,
    SecurityConfig,
    ServerConfig,
)


class TestApplicationConfig:
    """Tests for ApplicationConfig schema."""

    def test_valid_config(self):
        """Test valid application configuration."""
        config = ApplicationConfig(name="Test API", version="1.0.0", debug=True, log_level="DEBUG")
        assert config.name == "Test API"
        assert config.debug is True
        assert config.log_level == "DEBUG"

    def test_defaults(self):
        """Test default values."""
        config = ApplicationConfig()
        assert config.name == "Photo Restoration API"
        assert config.version == "1.8.2"
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_invalid_log_level(self):
        """Test invalid log level raises error."""
        with pytest.raises(ValidationError):
            ApplicationConfig(log_level="INVALID")


class TestServerConfig:
    """Tests for ServerConfig schema."""

    def test_valid_config(self):
        """Test valid server configuration."""
        config = ServerConfig(host="127.0.0.1", port=9000, workers=4)
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.workers == 4

    def test_port_validation(self):
        """Test port number validation."""
        # Valid ports
        ServerConfig(port=1)
        ServerConfig(port=8000)
        ServerConfig(port=65535)

        # Invalid ports
        with pytest.raises(ValidationError):
            ServerConfig(port=0)
        with pytest.raises(ValidationError):
            ServerConfig(port=65536)

    def test_workers_validation(self):
        """Test workers validation."""
        # Valid
        ServerConfig(workers=1)
        ServerConfig(workers=16)

        # Invalid
        with pytest.raises(ValidationError):
            ServerConfig(workers=0)
        with pytest.raises(ValidationError):
            ServerConfig(workers=17)


class TestModelConfig:
    """Tests for ModelConfig schema."""

    def test_valid_huggingface_model(self):
        """Test valid HuggingFace model config."""
        config = ModelConfig(
            id="test-model",
            name="Test Model",
            model="test/model",
            provider="huggingface",
            category="upscale",
            description="Test model",
        )
        assert config.id == "test-model"
        assert config.provider == "huggingface"
        assert config.enabled is True  # Default

    def test_valid_replicate_model(self):
        """Test valid Replicate model config."""
        config = ModelConfig(
            id="test-replicate",
            name="Test Replicate",
            model="owner/model",
            provider="replicate",
            category="restore",
            description="Test",
            input_param_name="input_image",
        )
        assert config.provider == "replicate"
        assert config.input_param_name == "input_image"

    def test_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValidationError):
            ModelConfig(
                id="test",
                name="Test",
                model="test/model",
                provider="invalid",
                category="test",
                description="Test",
            )

    def test_required_fields(self):
        """Test that required fields are enforced."""
        # Missing id
        with pytest.raises(ValidationError):
            ModelConfig(
                name="Test", model="test/model", provider="huggingface", category="test", description="Test"
            )

        # Missing provider
        with pytest.raises(ValidationError):
            ModelConfig(id="test", name="Test", model="test/model", category="test", description="Test")


class TestFileStorageConfig:
    """Tests for FileStorageConfig schema."""

    def test_valid_config(self):
        """Test valid file storage config."""
        config = FileStorageConfig(
            upload_dir="/data/uploads",
            processed_dir="/data/processed",
            max_upload_size_mb=20,
            allowed_extensions=[".jpg", ".png"],
            image_quality=90,
        )
        assert config.upload_dir == "/data/uploads"
        assert config.max_upload_size_mb == 20
        assert config.image_quality == 90

    def test_extension_validation(self):
        """Test that extensions are normalized with dots."""
        config = FileStorageConfig(allowed_extensions=["jpg", ".png", "jpeg"])
        assert config.allowed_extensions == [".jpg", ".png", ".jpeg"]

    def test_size_validation(self):
        """Test upload size validation."""
        # Valid
        FileStorageConfig(max_upload_size_mb=1)
        FileStorageConfig(max_upload_size_mb=100)

        # Invalid
        with pytest.raises(ValidationError):
            FileStorageConfig(max_upload_size_mb=0)
        with pytest.raises(ValidationError):
            FileStorageConfig(max_upload_size_mb=101)

    def test_quality_validation(self):
        """Test image quality validation."""
        # Valid
        FileStorageConfig(image_quality=1)
        FileStorageConfig(image_quality=100)

        # Invalid
        with pytest.raises(ValidationError):
            FileStorageConfig(image_quality=0)
        with pytest.raises(ValidationError):
            FileStorageConfig(image_quality=101)


class TestConfigFile:
    """Tests for complete ConfigFile schema."""

    def test_minimal_valid_config(self):
        """Test minimal valid configuration."""
        config = ConfigFile(models=[])
        assert config.application.name == "Photo Restoration API"
        assert len(config.models) == 0

    def test_full_valid_config(self):
        """Test complete valid configuration."""
        config_dict = {
            "application": {"name": "Test API", "version": "1.0.0", "debug": True, "log_level": "DEBUG"},
            "server": {"host": "0.0.0.0", "port": 8000, "workers": 2},
            "cors": {"origins": ["http://localhost:3000"]},
            "security": {"algorithm": "HS256", "access_token_expire_minutes": 1440},
            "api_providers": {
                "huggingface": {"api_url": "https://api.huggingface.co", "timeout_seconds": 60},
                "replicate": {"timeout_seconds": 120},
            },
            "models": [
                {
                    "id": "test-model",
                    "name": "Test",
                    "model": "test/model",
                    "provider": "huggingface",
                    "category": "test",
                    "description": "Test model",
                }
            ],
            "models_api": {"require_auth": False},
            "database": {"url": "sqlite+aiosqlite:///test.db"},
            "file_storage": {
                "upload_dir": "./uploads",
                "processed_dir": "./processed",
                "max_upload_size_mb": 10,
                "allowed_extensions": [".jpg"],
            },
            "session": {"cleanup_hours": 24, "cleanup_interval_hours": 6},
            "processing": {"max_concurrent_uploads_per_session": 3},
        }

        config = ConfigFile(**config_dict)
        assert config.application.name == "Test API"
        assert config.server.port == 8000
        assert len(config.models) == 1

    def test_duplicate_model_ids(self):
        """Test that duplicate model IDs are rejected."""
        config_dict = {
            "models": [
                {
                    "id": "duplicate",
                    "name": "Model 1",
                    "model": "test/model1",
                    "provider": "huggingface",
                    "category": "test",
                    "description": "Test 1",
                },
                {
                    "id": "duplicate",
                    "name": "Model 2",
                    "model": "test/model2",
                    "provider": "huggingface",
                    "category": "test",
                    "description": "Test 2",
                },
            ]
        }

        with pytest.raises(ValidationError, match="Model IDs must be unique"):
            ConfigFile(**config_dict)

    def test_empty_models_allowed(self):
        """Test that empty models list is allowed."""
        config = ConfigFile(models=[])
        assert config.models == []

    def test_json_schema_generation(self):
        """Test that JSON schema can be generated."""
        schema = ConfigFile.model_json_schema()
        assert "properties" in schema
        assert "application" in schema["properties"]
        assert "models" in schema["properties"]
