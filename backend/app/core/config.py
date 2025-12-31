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

# Configuration version constants
CURRENT_CONFIG_VERSION = "1.0.0"
MIN_SUPPORTED_VERSION = "0.9.0"  # Support legacy configs without version field

# Flag to enable/disable automatic migrations (can be controlled via env var)
AUTO_MIGRATE_ENABLED = os.getenv("CONFIG_AUTO_MIGRATE", "true").lower() in ("true", "1", "yes", "on")


def parse_version(version: str) -> tuple[int, int, int]:
    """
    Parse a semver version string into a tuple of integers.

    Supports standard semver format (major.minor.patch) and strips
    pre-release and build metadata if present (e.g., "1.2.3-alpha+001").

    Note: Pre-release and build metadata are ignored for version comparison.
    Config versions should use simple major.minor.patch format.

    Args:
        version: Semantic version string (e.g., "1.2.3" or "1.2.3-alpha+build")

    Returns:
        Tuple of (major, minor, patch) as integers

    Raises:
        ValueError: If version string is invalid
    """
    try:
        # Strip pre-release metadata (after '-') and build metadata (after '+')
        # Example: "1.2.3-alpha+build" -> "1.2.3"
        core_version = version.split("-")[0].split("+")[0]

        parts = core_version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}. Expected 'major.minor.patch'")

        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, AttributeError, IndexError) as e:
        raise ValueError(f"Invalid version string '{version}': {e}")


def detect_config_version(config_dict: dict[str, Any]) -> str:
    """
    Detect configuration version from loaded JSON.

    Args:
        config_dict: Loaded configuration dictionary

    Returns:
        Version string. Returns "0.9.0" for legacy configs without version field.
    """
    version = config_dict.get("config_version", "0.9.0")

    # Validate version format
    try:
        parse_version(version)
    except ValueError as e:
        logger.warning(f"Invalid config_version '{version}': {e}. Treating as legacy config (0.9.0)")
        return "0.9.0"

    return version


def is_version_compatible(version: str, min_version: str = MIN_SUPPORTED_VERSION) -> bool:
    """
    Check if a configuration version is compatible with current application.

    Compatibility rules:
    - Version must be >= minimum supported version (0.9.0)
    - Version must be <= current application version (no future configs)
    - Major version must match current version (breaking changes across majors)
    - Special case: 0.9.0 (legacy) is compatible with 1.x.x (can be migrated)

    Args:
        version: Configuration version to check
        min_version: Minimum supported version

    Returns:
        True if version is compatible, False otherwise
    """
    try:
        ver_tuple = parse_version(version)
        min_tuple = parse_version(min_version)
        current_tuple = parse_version(CURRENT_CONFIG_VERSION)

        # Version must be >= minimum supported version
        if ver_tuple < min_tuple:
            return False

        # Special case: 0.9.0 (legacy without version field) is compatible with 1.x.x
        # This allows seamless migration from legacy configs
        if ver_tuple == (0, 9, 0) and current_tuple[0] == 1:
            return True

        # Major version must match current version (no breaking changes across majors)
        if ver_tuple[0] != current_tuple[0]:
            return False

        # Version must not be newer than current application version
        # Newer configs may contain features the application doesn't support
        if ver_tuple > current_tuple:
            return False

        return True
    except ValueError:
        # Invalid version strings are not compatible
        return False


def get_migration_suggestion(from_version: str) -> str:
    """
    Get migration suggestion message for a given version.

    Args:
        from_version: Current configuration version

    Returns:
        Human-readable migration suggestion
    """
    try:
        from_tuple = parse_version(from_version)
        current_tuple = parse_version(CURRENT_CONFIG_VERSION)

        if from_tuple == current_tuple:
            return "Configuration is up to date."

        if from_tuple < current_tuple:
            return (
                f"Configuration version {from_version} is outdated. "
                f"Current version is {CURRENT_CONFIG_VERSION}. "
                f"Run migration: python backend/scripts/migrate_config.py"
            )

        if from_tuple > current_tuple:
            return (
                f"Configuration version {from_version} is newer than application version {CURRENT_CONFIG_VERSION}. "
                f"Please update the application or downgrade the configuration."
            )

        return "Unknown version relationship."
    except ValueError:
        return f"Invalid configuration version '{from_version}'. Please fix or regenerate configuration."


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
    2. config/{app_env}.json (environment-specific overrides for all settings)
    3. config/local.json (MODEL CONFIGURATIONS ONLY - other keys ignored)

    Note: local.json is exclusively for model overrides. Only the 'models' array
    is merged from local.json. All other configuration keys (application, server,
    database, etc.) in local.json are silently ignored. For non-model overrides,
    use environment-specific files or environment variables.

    Args:
        app_env: Application environment (development, production, staging, testing)

    Returns:
        Merged configuration dictionary
    """
    config_dir = Path(__file__).parent.parent.parent / "config"

    # Load default config (with auto-migration if enabled)
    default_config_path = config_dir / "default.json"
    if not default_config_path.exists():
        logger.warning(f"Default config not found: {default_config_path}")
        return {}

    if AUTO_MIGRATE_ENABLED:
        config = load_and_migrate_config_file(default_config_path)
        logger.info(f"Loaded and migrated default config from {default_config_path}")
    else:
        config = load_json_config(default_config_path)
        logger.info(f"Loaded default config from {default_config_path}")

    # Detect and validate version of default config
    default_version = detect_config_version(config)
    logger.info(f"Default config version: {default_version}")

    # Load environment-specific config and validate version consistency
    env_config_path = config_dir / f"{app_env}.json"
    if env_config_path.exists():
        if AUTO_MIGRATE_ENABLED:
            env_config = load_and_migrate_config_file(env_config_path)
            logger.info(f"Loaded and migrated environment config from {env_config_path}")
        else:
            env_config = load_json_config(env_config_path)
            logger.info(f"Loaded environment config from {env_config_path}")

        env_version = detect_config_version(env_config)
        logger.info(f"Environment config version: {env_version}")

        # Ensure version consistency between default and environment configs
        if default_version != env_version:
            logger.error(f"Version mismatch: default.json has {default_version}, {app_env}.json has {env_version}")
            logger.error("All config files must have the same config_version field")
            raise ValueError(
                f"Configuration version mismatch: default.json ({default_version}) != {app_env}.json ({env_version}). "
                f"All configuration files must have the same version."
            )

        config = deep_merge(config, env_config)
        logger.info(f"Loaded {app_env} config from {env_config_path}")
    else:
        logger.info(f"No environment-specific config found at {env_config_path}, using defaults only")

    # Use the validated version (both files have same version at this point)
    config_version = default_version
    logger.info(f"Configuration version: {config_version}")

    if not is_version_compatible(config_version):
        logger.error(f"Incompatible configuration version: {config_version}")
        logger.error(f"Supported versions: {MIN_SUPPORTED_VERSION} - {CURRENT_CONFIG_VERSION} (major version {CURRENT_CONFIG_VERSION.split('.')[0]})")
        logger.error(get_migration_suggestion(config_version))
        raise ValueError(
            f"Configuration version {config_version} is incompatible with application version {CURRENT_CONFIG_VERSION}. "
            f"{get_migration_suggestion(config_version)}"
        )

    # Warn if configuration is outdated (but compatible)
    if config_version != CURRENT_CONFIG_VERSION:
        try:
            ver_tuple = parse_version(config_version)
            current_tuple = parse_version(CURRENT_CONFIG_VERSION)
            if ver_tuple < current_tuple:
                logger.warning(f"Configuration version {config_version} is outdated (current: {CURRENT_CONFIG_VERSION})")
                logger.warning(get_migration_suggestion(config_version))
        except ValueError:
            pass  # Already logged in detect_config_version

    # Load local config - MODELS ONLY (all other keys are ignored)
    # Note: local.json is exclusively for model configuration overrides.
    # For non-model settings, use environment-specific files or environment variables.
    local_config_path = config_dir / "local.json"
    if local_config_path.exists():
        try:
            # Load local config (with auto-migration if enabled)
            if AUTO_MIGRATE_ENABLED:
                local_config = load_and_migrate_config_file(local_config_path)
                logger.info(f"Loaded and migrated local config from {local_config_path}")
            else:
                local_config = load_json_config(local_config_path)

            # Check version consistency for local.json (warning only, not enforced)
            # Rationale: local.json is optional and only affects 'models' array.
            # Version mismatches are tolerable since:
            # 1. local.json has limited scope (models only)
            # 2. Model schema changes are rare and usually backward-compatible
            # 3. Auto-migration will upgrade local.json when loaded
            # 4. Enforcing strict version would break development workflows
            local_version = detect_config_version(local_config)
            if local_version != config_version:
                logger.warning(
                    f"local.json version ({local_version}) differs from main config ({config_version}). "
                    f"This is acceptable but consider updating local.json to match version {config_version}. "
                    f"Auto-migration will upgrade it if enabled."
                )

            # Warn about ignored keys (anything other than 'models' and 'config_version')
            # Note: config_version is allowed but not used for merging
            ignored_keys = [key for key in local_config.keys() if key not in ("models", "config_version")]
            if ignored_keys:
                logger.warning(
                    f"local.json contains non-model keys that will be ignored: {ignored_keys}. "
                    f"local.json only affects 'models' array. "
                    f"For other settings, use environment-specific files or environment variables."
                )

            # Special handling for models array - merge by model ID
            # IMPORTANT: Only 'models' key is processed from local.json
            # All other keys (application, server, database, etc.) are ignored
            if "models" in local_config and "models" in config:
                config["models"] = merge_model_configs(config["models"], local_config["models"])
            elif "models" in local_config:
                # If base config has no models, use local models directly
                config["models"] = local_config["models"]
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


def load_and_migrate_config_file(config_path: Path, app_env: str = "development") -> dict[str, Any]:
    """
    Load configuration file and apply automatic migrations if needed.

    IMPORTANT: This function MODIFIES config files on disk when AUTO_MIGRATE_ENABLED=true.
    This is intentional behavior to ensure config files stay up-to-date with the application.

    Benefits of auto-migration:
    - Eliminates manual migration steps during deployments
    - Ensures configs are always compatible with current app version
    - Creates automatic backups before any changes (safety net)
    - One-time cost: migration only happens once per version upgrade

    To disable auto-migration (e.g., for version-controlled shared configs):
    - Set environment variable: CONFIG_AUTO_MIGRATE=false
    - Use manual migration scripts in backend/scripts/

    This function:
    1. Loads the config file
    2. Detects the version
    3. Checks if migration is needed
    4. If AUTO_MIGRATE_ENABLED and version is outdated:
       - Special handling for local.json (only adds config_version, not full migration)
       - For other files: full migration with all sections
       - Creates automatic backup (in config/backups/)
       - Applies migrations
       - Validates migrated config against schema
       - Saves migrated config to original file
       - Returns migrated config
    5. Otherwise, returns config as-is

    Args:
        config_path: Path to configuration file
        app_env: Application environment (for backup naming)

    Returns:
        Configuration dictionary (possibly migrated)

    Raises:
        ValueError: If migration fails or validation fails
    """
    # Lazy import to avoid circular dependency
    from app.core.config_backup import backup_config_file, save_config_with_backup
    from app.core.config_migrations import apply_migrations

    config = load_json_config(config_path)
    config_version = detect_config_version(config)

    # Check if migration is needed
    if config_version == CURRENT_CONFIG_VERSION:
        return config  # Already up to date

    if not AUTO_MIGRATE_ENABLED:
        logger.warning(f"Config version {config_version} is outdated, but auto-migration is disabled")
        logger.warning("Set CONFIG_AUTO_MIGRATE=true to enable automatic migrations")
        return config

    # Check if outdated (but compatible)
    try:
        ver_tuple = parse_version(config_version)
        current_tuple = parse_version(CURRENT_CONFIG_VERSION)

        if ver_tuple < current_tuple:
            logger.info(f"Auto-migrating config from {config_version} to {CURRENT_CONFIG_VERSION}")

            try:
                # Special handling for local.json: only add config_version, don't add empty sections
                # This prevents "ignored keys" warnings since local.json is exclusively for models
                is_local_config = config_path.name == "local.json"

                if is_local_config:
                    logger.info("Detected local.json - applying minimal migration (config_version only)")
                    # Only update the version field, preserve existing structure
                    migrated_config = config.copy()
                    migrated_config["config_version"] = CURRENT_CONFIG_VERSION

                    # Ensure models array exists (local.json purpose)
                    if "models" not in migrated_config:
                        migrated_config["models"] = []

                    # No schema validation for local.json (it's intentionally minimal)
                    logger.debug("Skipping schema validation for local.json (models-only file)")
                else:
                    # Full migration for default.json, production.json, etc.
                    migrated_config = apply_migrations(config, config_version, CURRENT_CONFIG_VERSION)

                    # Validate migrated config against schema to ensure it's loadable
                    try:
                        ConfigFile(**migrated_config)
                        logger.debug(f"Migration validation passed: config conforms to schema")
                    except Exception as validation_error:
                        raise ValueError(
                            f"Migrated config failed schema validation: {validation_error}. "
                            f"The migration may have produced an invalid configuration. "
                            f"This is likely a bug in the migration logic."
                        )

                # Save with automatic backup
                save_config_with_backup(config_path, migrated_config)

                logger.info(f"✓ Successfully migrated {config_path} to version {CURRENT_CONFIG_VERSION}")
                return migrated_config

            except Exception as e:
                logger.error(f"✗ Migration failed: {e}")
                logger.error(f"Cannot load incompatible config version {config_version}")
                logger.error("Options:")
                logger.error("  1. Fix migration error and retry")
                logger.error("  2. Restore from backup (see backend/config/backups/)")
                logger.error("  3. Disable auto-migration: CONFIG_AUTO_MIGRATE=false")
                raise ValueError(
                    f"Failed to migrate configuration from {config_version} to {CURRENT_CONFIG_VERSION}: {e}. "
                    f"Cannot continue with incompatible config. Check logs for details."
                ) from e
        else:
            # Version is newer than current (shouldn't happen, but handle gracefully)
            logger.warning(f"Config version {config_version} is newer than app version {CURRENT_CONFIG_VERSION}")
            return config

    except ValueError as e:
        logger.warning(f"Could not parse versions for migration: {e}")
        return config


def validate_ui_parameters(models: list[dict]) -> dict[str, list[str]]:
    """
    Validate that Replicate models have ui_hidden flags on parameters.

    Args:
        models: List of model configurations

    Returns:
        Dictionary with warnings:
        - 'needs_migration': List of model IDs that need migration
        - 'missing_params': List of parameter names missing ui_hidden
    """
    warnings_dict = {
        'needs_migration': [],
        'missing_params': []
    }

    for model in models:
        # Only check Replicate models with schemas
        if model.get('provider') != 'replicate':
            continue

        model_id = model.get('id', 'unknown')
        schema = model.get('replicate_schema')

        # Defensive: check for missing or invalid schema
        if not schema:
            logger.debug(f"Skipping model {model_id}: missing replicate_schema")
            continue

        if not isinstance(schema, dict):
            logger.warning(f"Skipping model {model_id}: replicate_schema is not a dict (got {type(schema).__name__})")
            continue

        input_schema = schema.get('input')
        if not input_schema:
            logger.debug(f"Skipping model {model_id}: missing replicate_schema.input")
            continue

        if not isinstance(input_schema, dict):
            logger.warning(f"Skipping model {model_id}: replicate_schema.input is not a dict (got {type(input_schema).__name__})")
            continue

        parameters = input_schema.get('parameters', [])

        # Validate parameters is a list (guard against schema variations)
        if not parameters:
            logger.debug(f"Skipping model {model_id}: no parameters defined")
            continue

        if not isinstance(parameters, list):
            logger.warning(f"Skipping model {model_id}: parameters is not a list (got {type(parameters).__name__})")
            continue

        needs_migration = False

        for param in parameters:
            # Validate param is a dict
            if not isinstance(param, dict):
                logger.warning(f"Skipping invalid parameter in model {model_id}: expected dict, got {type(param).__name__}")
                continue

            param_name = param.get('name', 'unknown')
            if 'ui_hidden' not in param:
                needs_migration = True
                warnings_dict['missing_params'].append(f"{model_id}.{param_name}")

        if needs_migration:
            warnings_dict['needs_migration'].append(model_id)

    return warnings_dict


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

    # Migration settings
    migration_script_command: str = "python backend/scripts/migrate_ui_parameters.py"

    # Internal flag to track if using new config system
    _using_json_config: bool = False
    _config_data: dict[str, Any] | None = None
    _ui_migration_warnings: dict[str, list[str]] | None = None

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

        # Lazy validation: don't validate UI parameters on init, only when first requested
        # This improves startup performance, especially in test environments
        # Validation will happen on first call to needs_ui_migration() or get_ui_migration_info()

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

    def _ensure_ui_validation(self) -> None:
        """
        Lazy validation of UI parameters (runs only once, on first access).

        This improves startup performance by deferring validation until needed.
        """
        # Skip if already validated or not using JSON config
        if self._ui_migration_warnings is not None or not self._using_json_config:
            return

        # Perform validation once
        models = self._config_data.get("models", []) if self._config_data else []
        if models:
            self._ui_migration_warnings = validate_ui_parameters(models)

            # Log warnings if migration needed (only on first validation)
            if self._ui_migration_warnings.get('needs_migration'):
                logger.warning("=" * 70)
                logger.warning("⚠️  MIGRATION REQUIRED: Custom Model Parameters UI")
                logger.warning("=" * 70)
                logger.warning(
                    f"Models need migration: {', '.join(self._ui_migration_warnings['needs_migration'])}"
                )
                logger.warning(
                    f"Parameters missing ui_hidden: {len(self._ui_migration_warnings['missing_params'])}"
                )
                logger.warning("")
                logger.warning("The Custom Model Parameters UI feature requires model")
                logger.warning("configurations to include 'ui_hidden' flags on parameters.")
                logger.warning("")
                logger.warning("To migrate your configuration, run:")
                logger.warning(f"  {self.migration_script_command}")
                logger.warning("")
                logger.warning("For more info, see README.md 'Breaking Changes' section")
                logger.warning("=" * 70)
        else:
            self._ui_migration_warnings = {"needs_migration": [], "missing_params": []}

    def needs_ui_migration(self) -> bool:
        """
        Check if any models need UI parameter migration.

        Uses lazy validation - validation only runs on first call.

        Returns:
            True if migration is needed, False otherwise
        """
        self._ensure_ui_validation()

        if not self._ui_migration_warnings:
            return False
        return len(self._ui_migration_warnings.get('needs_migration', [])) > 0

    def get_ui_migration_info(self) -> dict[str, Any]:
        """
        Get detailed information about UI migration status.

        Uses lazy validation - validation only runs on first call.

        Returns:
            Dictionary with migration status and details
        """
        self._ensure_ui_validation()

        if not self._ui_migration_warnings:
            return {
                'needs_migration': False,
                'model_ids': [],
                'missing_params': [],
                'count': 0
            }

        return {
            'needs_migration': self.needs_ui_migration(),
            'model_ids': self._ui_migration_warnings.get('needs_migration', []),
            'missing_params': self._ui_migration_warnings.get('missing_params', []),
            'count': len(self._ui_migration_warnings.get('needs_migration', []))
        }

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
