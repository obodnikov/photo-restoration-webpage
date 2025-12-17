#!/usr/bin/env python3
"""
Configuration validation script.

Validates JSON config files against Pydantic schemas and checks for required secrets.

Usage:
    python scripts/validate_config.py --env production
    python scripts/validate_config.py --config config/production.json
    python scripts/validate_config.py --help
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_schema import ConfigFile
from pydantic import ValidationError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Required secrets in .env
REQUIRED_SECRETS = {
    "HF_API_KEY": "HuggingFace API key",
    "SECRET_KEY": "JWT secret key for token signing",
}

# Optional secrets
OPTIONAL_SECRETS = {
    "REPLICATE_API_TOKEN": "Replicate API token (optional, only needed for Replicate models)",
    "AUTH_USERNAME": "Authentication username",
    "AUTH_PASSWORD": "Authentication password",
}


def validate_json_syntax(config_path: Path) -> Dict[str, Any]:
    """
    Validate JSON syntax.

    Args:
        config_path: Path to config file

    Returns:
        Parsed config dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
            logger.info(f"✓ JSON syntax valid: {config_path}")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"✗ JSON syntax error in {config_path}:")
            logger.error(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
            raise


def validate_schema(config: Dict[str, Any]) -> ConfigFile:
    """
    Validate config against Pydantic schema.

    Args:
        config: Configuration dictionary

    Returns:
        Validated ConfigFile instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        validated = ConfigFile(**config)
        logger.info("✓ Schema validation passed")
        return validated
    except ValidationError as e:
        logger.error("✗ Schema validation failed:")
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            logger.error(f"  {loc}: {error['msg']}")
        raise


def check_secrets(env_file: Path = Path(".env")) -> Tuple[bool, List[str]]:
    """
    Check if required secrets are present in .env file.

    Args:
        env_file: Path to .env file

    Returns:
        Tuple of (all_present, missing_secrets)
    """
    missing = []

    if not env_file.exists():
        logger.warning(f"⚠ .env file not found: {env_file}")
        return False, list(REQUIRED_SECRETS.keys())

    # Read .env file
    env_vars = {}
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    # Check required secrets
    for key, description in REQUIRED_SECRETS.items():
        if key not in env_vars or not env_vars[key]:
            missing.append(f"{key} ({description})")
            logger.error(f"✗ Missing required secret: {key} ({description})")
        else:
            # Check if using example/placeholder value
            value = env_vars[key]
            if "your_" in value.lower() or "change" in value.lower() or value == key.lower():
                logger.warning(f"⚠ {key} appears to be a placeholder value")
            else:
                logger.info(f"✓ {key} is set")

    # Check optional secrets
    for key, description in OPTIONAL_SECRETS.items():
        if key in env_vars and env_vars[key]:
            logger.info(f"✓ {key} is set ({description})")

    return len(missing) == 0, missing


def validate_models(config: Dict[str, Any]) -> bool:
    """
    Validate models configuration.

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, False otherwise
    """
    models = config.get("models", [])
    if not models:
        logger.warning("⚠ No models configured")
        return True

    # Check for duplicate IDs
    model_ids = [m.get("id") for m in models]
    if len(model_ids) != len(set(model_ids)):
        logger.error("✗ Duplicate model IDs found")
        return False

    # Validate each model
    for i, model in enumerate(models):
        model_id = model.get("id", f"<unknown-{i}>")

        # Check required fields
        required = ["id", "name", "model", "provider", "category", "description"]
        for field in required:
            if field not in model:
                logger.error(f"✗ Model '{model_id}': missing required field '{field}'")
                return False

        # Check provider
        if model["provider"] not in ["huggingface", "replicate"]:
            logger.error(f"✗ Model '{model_id}': invalid provider '{model['provider']}'")
            return False

        logger.info(f"✓ Model '{model_id}' ({model['provider']}) is valid")

    logger.info(f"✓ All {len(models)} models are valid")
    return True


def main() -> int:
    """Main validation script."""
    parser = argparse.ArgumentParser(
        description="Validate configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate production config
  python scripts/validate_config.py --env production

  # Validate specific config file
  python scripts/validate_config.py --config config/development.json

  # Validate with custom .env location
  python scripts/validate_config.py --env production --env-file /path/to/.env
        """,
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=["development", "production", "staging", "testing"],
        help="Environment to validate (e.g., production)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file to validate (alternative to --env)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to .env file for secret checking (default: .env)",
    )
    parser.add_argument(
        "--no-secrets-check",
        action="store_true",
        help="Skip checking .env secrets",
    )

    args = parser.parse_args()

    if not args.env and not args.config:
        parser.error("Either --env or --config must be specified")

    # Determine config path
    if args.config:
        config_path = args.config
    else:
        config_path = Path("config") / f"{args.env}.json"
        # Fallback to default.json if env-specific doesn't exist
        if not config_path.exists():
            logger.warning(f"{config_path} not found, using config/default.json")
            config_path = Path("config") / "default.json"

    logger.info(f"\n{'='*60}")
    logger.info(f"Validating configuration: {config_path}")
    logger.info(f"{'='*60}\n")

    errors = []

    try:
        # Step 1: Validate JSON syntax
        logger.info("[1/4] Validating JSON syntax...")
        config = validate_json_syntax(config_path)

        # Step 2: Validate schema
        logger.info("\n[2/4] Validating against schema...")
        validated_config = validate_schema(config)

        # Step 3: Validate models
        logger.info("\n[3/4] Validating models...")
        if not validate_models(config):
            errors.append("Models validation failed")

        # Step 4: Check secrets
        if not args.no_secrets_check:
            logger.info("\n[4/4] Checking secrets in .env...")
            secrets_ok, missing = check_secrets(args.env_file)
            if not secrets_ok:
                errors.append(f"Missing secrets: {', '.join(missing)}")
        else:
            logger.info("\n[4/4] Skipping secrets check (--no-secrets-check)")

        # Summary
        logger.info(f"\n{'='*60}")
        if errors:
            logger.error("✗ Validation FAILED")
            for error in errors:
                logger.error(f"  - {error}")
            logger.info(f"{'='*60}\n")
            return 1
        else:
            logger.info("✓ Validation PASSED")
            logger.info(f"{'='*60}\n")
            logger.info("Configuration is valid and ready to use!")
            return 0

    except FileNotFoundError as e:
        logger.error(f"✗ File not found: {e}")
        return 1
    except json.JSONDecodeError:
        logger.error("✗ JSON syntax error")
        return 1
    except ValidationError:
        logger.error("✗ Schema validation error")
        return 1
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
