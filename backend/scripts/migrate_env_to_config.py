#!/usr/bin/env python3
"""
Migration script to convert .env configuration to JSON config files.

This script reads the current .env file, extracts non-secret configuration,
and generates a config.json file with proper structure. Secrets remain in .env.

Usage:
    python scripts/migrate_env_to_config.py --env-file backend/.env --output config/production.json
    python scripts/migrate_env_to_config.py --help
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Secrets that should remain in .env (never in config.json)
SECRETS = {
    "HF_API_KEY",
    "REPLICATE_API_TOKEN",
    "SECRET_KEY",
    "AUTH_USERNAME",
    "AUTH_PASSWORD",
}

# Environment selection variable
ENV_VARS = {"APP_ENV", "DEBUG"}


def parse_env_file(env_path: Path) -> Dict[str, str]:
    """
    Parse .env file into a dictionary.

    Args:
        env_path: Path to .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}

    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    with open(env_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env_vars[key] = value
            else:
                logger.warning(f"Line {line_num}: Invalid format (skipping): {line}")

    logger.info(f"Parsed {len(env_vars)} variables from {env_path}")
    return env_vars


def parse_json_value(value: str) -> Any:
    """
    Try to parse a string value as JSON.

    Args:
        value: String value to parse

    Returns:
        Parsed JSON value or original string
    """
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return value


def migrate_to_config(env_vars: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert env vars to config.json structure.

    Args:
        env_vars: Dictionary of environment variables

    Returns:
        Configuration dictionary
    """
    config: dict[str, Any] = {
        "application": {},
        "server": {},
        "cors": {},
        "security": {},
        "api_providers": {"huggingface": {}, "replicate": {}},
        "models": [],
        "models_api": {},
        "database": {},
        "file_storage": {},
        "session": {},
        "processing": {},
    }

    # Application
    if "APP_NAME" in env_vars:
        config["application"]["name"] = env_vars["APP_NAME"]
    if "APP_VERSION" in env_vars:
        config["application"]["version"] = env_vars["APP_VERSION"]
    if "DEBUG" in env_vars:
        config["application"]["debug"] = env_vars["DEBUG"].lower() in ("true", "1", "yes")

    # Server
    if "HOST" in env_vars:
        config["server"]["host"] = env_vars["HOST"]
    if "PORT" in env_vars:
        config["server"]["port"] = int(env_vars["PORT"])

    # CORS
    if "CORS_ORIGINS" in env_vars:
        config["cors"]["origins"] = parse_json_value(env_vars["CORS_ORIGINS"])

    # Security
    if "ALGORITHM" in env_vars:
        config["security"]["algorithm"] = env_vars["ALGORITHM"]
    if "ACCESS_TOKEN_EXPIRE_MINUTES" in env_vars:
        config["security"]["access_token_expire_minutes"] = int(env_vars["ACCESS_TOKEN_EXPIRE_MINUTES"])

    # HuggingFace Provider
    if "HF_API_URL" in env_vars:
        config["api_providers"]["huggingface"]["api_url"] = env_vars["HF_API_URL"]
    if "HF_API_TIMEOUT" in env_vars:
        config["api_providers"]["huggingface"]["timeout_seconds"] = int(env_vars["HF_API_TIMEOUT"])

    # Replicate Provider
    # (API token is secret, stays in .env)

    # Models
    if "MODELS_CONFIG" in env_vars:
        models = parse_json_value(env_vars["MODELS_CONFIG"])
        if isinstance(models, list):
            config["models"] = models
        else:
            logger.warning("MODELS_CONFIG is not a valid JSON array")

    # Models API
    if "MODELS_REQUIRE_AUTH" in env_vars:
        config["models_api"]["require_auth"] = env_vars["MODELS_REQUIRE_AUTH"].lower() in ("true", "1", "yes")

    # Database
    if "DATABASE_URL" in env_vars:
        config["database"]["url"] = env_vars["DATABASE_URL"]

    # File Storage
    if "UPLOAD_DIR" in env_vars:
        config["file_storage"]["upload_dir"] = env_vars["UPLOAD_DIR"]
    if "PROCESSED_DIR" in env_vars:
        config["file_storage"]["processed_dir"] = env_vars["PROCESSED_DIR"]
    if "MAX_UPLOAD_SIZE" in env_vars:
        # Convert bytes to MB
        max_size_bytes = int(env_vars["MAX_UPLOAD_SIZE"])
        config["file_storage"]["max_upload_size_mb"] = max_size_bytes // (1024 * 1024)
    if "ALLOWED_EXTENSIONS" in env_vars:
        config["file_storage"]["allowed_extensions"] = parse_json_value(env_vars["ALLOWED_EXTENSIONS"])

    # Session
    if "SESSION_CLEANUP_HOURS" in env_vars:
        config["session"]["cleanup_hours"] = int(env_vars["SESSION_CLEANUP_HOURS"])
    if "SESSION_CLEANUP_INTERVAL_HOURS" in env_vars:
        config["session"]["cleanup_interval_hours"] = int(env_vars["SESSION_CLEANUP_INTERVAL_HOURS"])

    # Processing
    if "MAX_CONCURRENT_UPLOADS_PER_SESSION" in env_vars:
        config["processing"]["max_concurrent_uploads_per_session"] = int(
            env_vars["MAX_CONCURRENT_UPLOADS_PER_SESSION"]
        )

    # Remove empty sections
    config = {k: v for k, v in config.items() if v}

    return config


def create_new_env_file(env_vars: Dict[str, str]) -> str:
    """
    Create new .env file content with only secrets.

    Args:
        env_vars: Original environment variables

    Returns:
        New .env file content
    """
    lines = [
        "# === SECRETS (NEVER COMMIT ACTUAL VALUES) ===",
        f"HF_API_KEY={env_vars.get('HF_API_KEY', 'your_huggingface_api_key_here')}",
        f"REPLICATE_API_TOKEN={env_vars.get('REPLICATE_API_TOKEN', 'your_replicate_api_token_here')}",
        f"SECRET_KEY={env_vars.get('SECRET_KEY', 'CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY')}",
        "",
        "# === CREDENTIALS ===",
        f"AUTH_USERNAME={env_vars.get('AUTH_USERNAME', 'admin')}",
        f"AUTH_PASSWORD={env_vars.get('AUTH_PASSWORD', 'changeme')}",
        "",
        "# === ENVIRONMENT ===",
        f"APP_ENV={env_vars.get('APP_ENV', 'production')}",
        "",
        "# === OPTIONAL OVERRIDES ===",
        "# Uncomment to override config.json values:",
        "# DEBUG=true",
        "# MAX_UPLOAD_SIZE_MB=20",
        "# DATABASE_URL=postgresql://user:pass@host/db",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Main migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate .env configuration to JSON config files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate to production config
  python scripts/migrate_env_to_config.py --env-file backend/.env --output config/production.json

  # Migrate to development config with backup
  python scripts/migrate_env_to_config.py --env-file .env --output config/development.json --backup

  # Dry run (show what would be migrated)
  python scripts/migrate_env_to_config.py --env-file .env --output config/production.json --dry-run
        """,
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output config JSON file path (e.g., config/production.json)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup of original .env file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without writing files",
    )
    parser.add_argument(
        "--update-env",
        action="store_true",
        help="Update .env file to contain only secrets",
    )

    args = parser.parse_args()

    try:
        # Parse .env file
        logger.info(f"Reading {args.env_file}...")
        env_vars = parse_env_file(args.env_file)

        # Migrate to config
        logger.info("Converting to config.json format...")
        config = migrate_to_config(env_vars)

        # Show configuration
        config_json = json.dumps(config, indent=2)
        if args.dry_run:
            logger.info("\n=== Generated Configuration ===")
            print(config_json)
            logger.info("\n=== New .env (secrets only) ===")
            print(create_new_env_file(env_vars))
            logger.info("\nDry run complete. No files were modified.")
            return 0

        # Create backup if requested
        if args.backup and args.env_file.exists():
            backup_path = args.env_file.with_suffix(f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(args.env_file, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Write config file
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(config_json)
        logger.info(f"✓ Created config file: {args.output}")

        # Update .env if requested
        if args.update_env:
            new_env_content = create_new_env_file(env_vars)
            with open(args.env_file, "w", encoding="utf-8") as f:
                f.write(new_env_content)
            logger.info(f"✓ Updated {args.env_file} (secrets only)")

        logger.info("\n=== Migration Complete ===")
        logger.info(f"✓ Configuration: {args.output}")
        if args.update_env:
            logger.info(f"✓ Secrets: {args.env_file}")
        logger.info("\nNext steps:")
        logger.info(f"1. Review {args.output}")
        logger.info("2. Set APP_ENV environment variable (e.g., APP_ENV=production)")
        logger.info("3. Validate: python scripts/validate_config.py --env production")
        logger.info("4. Test your application")

        return 0

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
