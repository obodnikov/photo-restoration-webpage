"""Application configuration using Pydantic BaseSettings with JSON config file support."""
import json
import logging
import os
import warnings
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config_schema import ConfigFile

logger = logging.getLogger(__name__)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary (base is not modified)
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_json_config(config_path: Path) -> dict[str, Any]:
    """
    Load and parse JSON configuration file.

    Args:
        config_path: Path to JSON config file

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config_from_files(app_env: str = "development") -> dict[str, Any]:
    """
    Load configuration from JSON files based on environment.

    Loading priority (lowest to highest):
    1. config/default.json (base configuration)
    2. config/{app_env}.json (environment-specific overrides)
    3. config/local.json (local overrides, highest priority)

    Args:
        app_env: Application environment (development, production, staging, testing)

    Returns:
        Merged configuration dictionary
    """
    config_dir = Path(__file__).parent.parent.parent / "config"

    # Load default config
    default_config_path = config_dir / "default.json"
    if not default_config_path.exists():
        logger.warning(f"Default config not found: {default_config_path}")
        return {}

    config = load_json_config(default_config_path)
    logger.info(f"Loaded default config from {default_config_path}")

    # Load environment-specific config
    env_config_path = config_dir / f"{app_env}.json"
    if env_config_path.exists():
        env_config = load_json_config(env_config_path)
        config = deep_merge(config, env_config)
        logger.info(f"Loaded {app_env} config from {env_config_path}")
    else:
        logger.info(f"No environment-specific config found at {env_config_path}, using defaults only")

    # Load local config (highest priority) - for model configurations
    local_config_path = config_dir / "local.json"
    if local_config_path.exists():
        try:
            local_config = load_json_config(local_config_path)
            # Special handling for models array - merge by model ID
            if "models" in local_config and "models" in config:
                config["models"] = merge_model_configs(config["models"], local_config["models"])
            else:
                config = deep_merge(config, local_config)
            logger.info(f"Loaded local config from {local_config_path}")
        except Exception as e:
            logger.error(f"Error loading local config: {e}, skipping")

    return config


def merge_model_configs(base_models: list[dict], local_models: list[dict]) -> list[dict]:
    """
    Merge model configurations with local.json overriding base configs by model ID.

    Args:
        base_models: Models from default/environment config
        local_models: Models from local.json

    Returns:
        Merged model list with local models taking priority
    """
    # Create a dict keyed by model ID for easy lookup
    models_dict = {model["id"]: model for model in base_models}

    # Override/add models from local config
    for local_model in local_models:
        model_id = local_model.get("id")
        if model_id:
            models_dict[model_id] = local_model

    return list(models_dict.values())


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment selection
    app_env: str = "development"

    # ===== SECRETS (from .env only) =====
    # These should NEVER be in config files, only in .env
    hf_api_key: str = ""
    replicate_api_token: str = ""
    secret_key: str = "CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY"

    # Admin user credentials (for database seeding)
    auth_username: str = "admin"
    auth_password: str = "changeme"
    auth_email: str = "admin@example.com"
    auth_full_name: str = "System Administrator"

    # ===== CONFIGURATION (from JSON files + .env overrides) =====
    # Application
    app_name: str = "Photo Restoration API"
    app_version: str = "1.8.2"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS - Must be JSON array format in .env file
    # Example: CORS_ORIGINS=["http://localhost:3000","http://localhost"]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost"]

    # Security
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # HuggingFace
    hf_api_timeout: int = 60
    hf_api_url: str = "https://api-inference.huggingface.co/models"

    # Replicate (API token is secret, loaded from .env)
    replicate_api_timeout: int = 120

    # Models configuration (JSON string - DEPRECATED, use config files instead)
    models_config: str = """[
        {
            "id": "swin2sr-2x",
            "name": "Swin2SR 2x Upscale",
            "model": "caidas/swin2SR-classical-sr-x2-64",
            "provider": "huggingface",
            "category": "upscale",
            "description": "Fast 2x upscaling",
            "enabled": true,
            "parameters": {"scale": 2}
        }
    ]"""
    # Models API authentication (default: public access)
    models_require_auth: bool = False

    # Database
    # Note: Use 4 slashes (////) for absolute paths, 3 slashes (///) for relative paths
    database_url: str = "sqlite+aiosqlite:////data/photo_restoration.db"

    # File storage
    upload_dir: Path = Path("./data/uploads")
    processed_dir: Path = Path("./data/processed")
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    # Allowed extensions - Must be JSON array format in .env file
    # Example: ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png"]
    allowed_extensions: set[str] = {".jpg", ".jpeg", ".png"}

    # Session
    session_cleanup_hours: int = 24
    session_cleanup_interval_hours: int = 6  # How often to run cleanup task

    # Processing limits
    max_concurrent_uploads_per_session: int = 3  # Concurrent processing limit per session

    # Internal flag to track if using new config system
    _using_json_config: bool = False
    _config_data: dict[str, Any] | None = None

    def __init__(self, **kwargs: Any):
        """Initialize settings with config file support."""
        # Try to load from JSON config files first
        app_env = os.getenv("APP_ENV", kwargs.get("app_env", "development"))

        using_json = False
        config_data_dict = None

        try:
            config_data = load_config_from_files(app_env)
            if config_data:
                # Validate using Pydantic schema
                validated_config = ConfigFile(**config_data)

                # Flatten config for Settings
                flat_config = self._flatten_config(validated_config)

                # Merge with kwargs (JSON config provides defaults)
                kwargs = {**flat_config, **kwargs}

                using_json = True
                config_data_dict = config_data
                logger.info("Using new JSON config system")
        except FileNotFoundError:
            logger.warning("Config files not found, falling back to .env only (DEPRECATED)")
            warnings.warn(
                "Using .env-only configuration is deprecated. "
                "Please migrate to JSON config files using: python scripts/migrate_env_to_config.py",
                DeprecationWarning,
                stacklevel=2
            )
        except Exception as e:
            logger.error(f"Error loading JSON config: {e}, falling back to .env only")
            warnings.warn(f"Config file error: {e}. Falling back to .env only.", stacklevel=2)

        super().__init__(**kwargs)

        # IMPORTANT: Environment variables override JSON config
        # Apply environment variable overrides AFTER Pydantic initialization
        # This ensures env vars have highest priority
        env_overrides = {}

        # Check for environment variable overrides for key settings
        if os.getenv("DEBUG") is not None:
            debug_str = os.getenv("DEBUG", "").lower()
            debug_val = debug_str in ("true", "1", "yes", "on")
            if debug_val != self.debug:
                env_overrides["debug"] = debug_val
                object.__setattr__(self, "debug", debug_val)

        if os.getenv("HOST") is not None:
            host_val = os.getenv("HOST")
            if host_val != self.host:
                env_overrides["host"] = host_val
                object.__setattr__(self, "host", host_val)

        if os.getenv("PORT") is not None:
            port_val = int(os.getenv("PORT"))
            if port_val != self.port:
                env_overrides["port"] = port_val
                object.__setattr__(self, "port", port_val)

        if os.getenv("UPLOAD_DIR") is not None:
            upload_dir_val = Path(os.getenv("UPLOAD_DIR"))
            if upload_dir_val != self.upload_dir:
                env_overrides["upload_dir"] = str(upload_dir_val)
                object.__setattr__(self, "upload_dir", upload_dir_val)

        if os.getenv("PROCESSED_DIR") is not None:
            processed_dir_val = Path(os.getenv("PROCESSED_DIR"))
            if processed_dir_val != self.processed_dir:
                env_overrides["processed_dir"] = str(processed_dir_val)
                object.__setattr__(self, "processed_dir", processed_dir_val)

        # Log environment overrides
        if env_overrides:
            logger.info(f"Environment variables overriding JSON config: {', '.join(env_overrides.keys())}")

        # Set flags AFTER all initialization
        self._using_json_config = using_json
        self._config_data = config_data_dict

        # Log configuration source and summary
        if self._using_json_config:
            models_count = len(self._config_data.get("models", []))
            logger.info(f"✓ Configuration loaded from JSON files (APP_ENV={self.app_env})")
            logger.info(f"  - Models: {models_count} configured")
            logger.info(f"  - CORS origins: {len(self.cors_origins)} configured")
            logger.info(f"  - Database: {self.database_url}")

            if self.debug:
                logger.debug("=== Configuration Details (DEBUG mode) ===")
                logger.debug(f"  App: {self.app_name} v{self.app_version}")
                logger.debug(f"  Server: {self.host}:{self.port}")
                logger.debug(f"  Debug: {self.debug}")
                logger.debug(f"  CORS origins: {self.cors_origins}")
                logger.debug(f"  Models ({models_count}):")
                for model in self._config_data.get("models", []):
                    logger.debug(f"    - {model['id']}: {model['name']} ({model.get('provider', 'unknown')})")
                logger.debug(f"  Upload dir: {self.upload_dir}")
                logger.debug(f"  Processed dir: {self.processed_dir}")
                logger.debug(f"  Max upload size: {self.max_upload_size / 1024 / 1024:.1f}MB")
                logger.debug("=" * 50)
        else:
            logger.warning("⚠ Using .env-only configuration (DEPRECATED)")
            logger.warning("  Please migrate to JSON config: python scripts/migrate_env_to_config.py")
            if self.debug:
                logger.debug(f"  Fallback models_config length: {len(self.models_config)} chars")

    @staticmethod
    def _flatten_config(config: ConfigFile) -> dict[str, Any]:
        """Flatten ConfigFile to match Settings field names."""
        return {
            # Application
            "app_name": config.application.name,
            "app_version": config.application.version,
            "debug": config.application.debug,

            # Server
            "host": config.server.host,
            "port": config.server.port,

            # CORS
            "cors_origins": config.cors.origins,

            # Security
            "algorithm": config.security.algorithm,
            "access_token_expire_minutes": config.security.access_token_expire_minutes,

            # API Providers
            "hf_api_url": config.api_providers.huggingface.api_url,
            "hf_api_timeout": config.api_providers.huggingface.timeout_seconds,
            "replicate_api_timeout": config.api_providers.replicate.timeout_seconds,

            # Models API
            "models_require_auth": config.models_api.require_auth,

            # Database
            "database_url": config.database.url,

            # File Storage
            "upload_dir": Path(config.file_storage.upload_dir),
            "processed_dir": Path(config.file_storage.processed_dir),
            "max_upload_size": config.file_storage.max_upload_size_mb * 1024 * 1024,
            "allowed_extensions": set(config.file_storage.allowed_extensions),

            # Session
            "session_cleanup_hours": config.session.cleanup_hours,
            "session_cleanup_interval_hours": config.session.cleanup_interval_hours,

            # Processing
            "max_concurrent_uploads_per_session": config.processing.max_concurrent_uploads_per_session,
        }

    @field_validator("models_config")
    @classmethod
    def validate_models_config(cls, v: str) -> str:
        """Validate models configuration JSON (DEPRECATED - use config files)."""
        try:
            models = json.loads(v)
            if not isinstance(models, list):
                raise ValueError("models_config must be a JSON array")

            # Validate each model has required fields
            for model in models:
                if "id" not in model or "name" not in model or "model" not in model:
                    raise ValueError("Each model must have 'id', 'name', and 'model' fields")

                # If provider is specified, validate it
                if "provider" in model and model["provider"] not in ["huggingface", "replicate"]:
                    raise ValueError(f"Invalid provider '{model['provider']}'. Must be 'huggingface' or 'replicate'")

            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in models_config: {e}")

    def get_models(self) -> list[dict[str, Any]]:
        """
        Parse and return models configuration.

        Returns models from JSON config if available, otherwise from .env MODELS_CONFIG.
        """
        # Try to get from JSON config first
        if self._using_json_config and self._config_data:
            models = self._config_data.get("models", [])
            if models:
                return models

        # Fallback to .env MODELS_CONFIG (deprecated)
        return json.loads(self.models_config)

    def get_model_by_id(self, model_id: str) -> dict[str, Any] | None:
        """Get model configuration by ID."""
        models = self.get_models()
        for model in models:
            if model.get("id") == model_id:
                return model
        return None

    def is_using_json_config(self) -> bool:
        """Check if using new JSON config system."""
        return self._using_json_config

    def get_available_tags(self) -> list[str]:
        """Get available tags for model configuration."""
        if self._config_data and "model_configuration" in self._config_data:
            return self._config_data["model_configuration"].get("available_tags", [])
        return ["restore", "replicate", "advanced", "enhance", "upscale", "fast"]

    def get_available_categories(self) -> list[str]:
        """Get available categories for model configuration."""
        if self._config_data and "model_configuration" in self._config_data:
            return self._config_data["model_configuration"].get("available_categories", [])
        return ["restore", "upscale", "enhance"]

    def get_model_source(self, model_id: str) -> str:
        """
        Determine the source config file for a given model.

        Args:
            model_id: Model identifier

        Returns:
            "local", "production", "development", or "default"
        """
        config_dir = Path(__file__).parent.parent.parent / "config"

        # Check local.json first
        local_config_path = config_dir / "local.json"
        if local_config_path.exists():
            try:
                local_config = load_json_config(local_config_path)
                local_models = local_config.get("models", [])
                if any(m.get("id") == model_id for m in local_models):
                    return "local"
            except Exception:
                pass

        # Check environment config
        env_config_path = config_dir / f"{self.app_env}.json"
        if env_config_path.exists():
            try:
                env_config = load_json_config(env_config_path)
                env_models = env_config.get("models", [])
                if any(m.get("id") == model_id for m in env_models):
                    return self.app_env
            except Exception:
                pass

        # Default to "default"
        return "default"

    def save_local_model_config(self, model_data: dict[str, Any]) -> None:
        """
        Save or update a model configuration in local.json.

        Args:
            model_data: Model configuration dictionary

        Raises:
            ValueError: If model_data is invalid
            IOError: If unable to write to local.json
        """
        model_id = model_data.get("id")
        if not model_id:
            raise ValueError("Model configuration must have an 'id' field")

        config_dir = Path(__file__).parent.parent.parent / "config"
        local_config_path = config_dir / "local.json"

        # Load existing local config or create new
        if local_config_path.exists():
            local_config = load_json_config(local_config_path)
        else:
            local_config = {"models": []}

        # Ensure models array exists
        if "models" not in local_config:
            local_config["models"] = []

        # Update or add model
        models = local_config["models"]
        found = False
        for i, model in enumerate(models):
            if model.get("id") == model_id:
                models[i] = model_data
                found = True
                break

        if not found:
            models.append(model_data)

        # Write back to file
        with open(local_config_path, "w", encoding="utf-8") as f:
            json.dump(local_config, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved model '{model_id}' to local.json")

    def delete_local_model_config(self, model_id: str) -> bool:
        """
        Delete a model configuration from local.json.

        Args:
            model_id: Model identifier

        Returns:
            True if model was deleted, False if not found in local.json

        Raises:
            IOError: If unable to write to local.json
        """
        config_dir = Path(__file__).parent.parent.parent / "config"
        local_config_path = config_dir / "local.json"

        if not local_config_path.exists():
            return False

        local_config = load_json_config(local_config_path)
        models = local_config.get("models", [])

        # Find and remove model
        original_len = len(models)
        models = [m for m in models if m.get("id") != model_id]

        if len(models) == original_len:
            return False  # Model not found

        local_config["models"] = models

        # Write back to file
        with open(local_config_path, "w", encoding="utf-8") as f:
            json.dump(local_config, f, indent=2, ensure_ascii=False)

        logger.info(f"Deleted model '{model_id}' from local.json")
        return True

    def reload_config(self) -> None:
        """
        Reload configuration from files (hot reload).

        This reloads the config data without restarting the application.
        Note: This only updates _config_data, settings fields remain unchanged.
        """
        try:
            config_data = load_config_from_files(self.app_env)
            if config_data:
                # Validate using Pydantic schema
                validated_config = ConfigFile(**config_data)
                self._config_data = config_data
                logger.info("Configuration reloaded successfully")
            else:
                logger.warning("No configuration data loaded during reload")
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            raise


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function provides a way to get settings that can be
    overridden in tests using dependency injection.
    """
    return settings


# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.processed_dir.mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)
