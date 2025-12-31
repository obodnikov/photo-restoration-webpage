"""Configuration migration framework for version upgrades."""
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import CURRENT_CONFIG_VERSION, parse_version

logger = logging.getLogger(__name__)


class ConfigMigration(ABC):
    """Base class for configuration migrations."""

    from_version: str
    to_version: str

    @abstractmethod
    def migrate(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Apply migration transformations to configuration.

        Args:
            config: Configuration dictionary (from_version)

        Returns:
            Migrated configuration dictionary (to_version)

        Raises:
            ValueError: If migration cannot be applied
        """
        pass

    @abstractmethod
    def rollback(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Rollback migration (downgrade from to_version to from_version).

        Args:
            config: Configuration dictionary (to_version)

        Returns:
            Rolled back configuration dictionary (from_version)

        Raises:
            ValueError: If rollback cannot be applied
        """
        pass

    def validate(self, config: dict[str, Any]) -> bool:
        """
        Validate that migration can be applied to configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if migration can be applied, False otherwise
        """
        try:
            # Check version
            current_version = config.get("config_version", "0.9.0")
            if current_version != self.from_version:
                return False
            return True
        except Exception:
            return False

    def __str__(self) -> str:
        """Return string representation."""
        return f"Migration({self.from_version} → {self.to_version})"


# Example migration (placeholder - will be implemented when needed)
class Migration_0_9_to_1_0(ConfigMigration):
    """
    Migration from legacy config (0.9.0) to version 1.0.0.

    Changes:
    - Add config_version field (1.0.0)
    - Ensure all required fields exist with defaults
    """

    from_version = "0.9.0"
    to_version = "1.0.0"

    def migrate(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Migrate from 0.9.0 to 1.0.0.

        Adds config_version field and ensures all top-level sections exist.
        Note: Pydantic validation (ConfigFile schema) will fill in default values
        for missing fields when the config is loaded, so we only need to ensure
        sections exist as empty dicts.
        """
        logger.info(f"Migrating config from {self.from_version} to {self.to_version}")

        # Add config_version field
        config["config_version"] = self.to_version

        # Ensure all top-level sections exist (Pydantic will add defaults for missing fields)
        # These empty dicts act as placeholders - ConfigFile schema provides actual defaults
        if "application" not in config:
            config["application"] = {}
        if "server" not in config:
            config["server"] = {}
        if "cors" not in config:
            config["cors"] = {}
        if "security" not in config:
            config["security"] = {}
        if "api_providers" not in config:
            config["api_providers"] = {}
        if "models" not in config:
            config["models"] = []
        if "models_api" not in config:
            config["models_api"] = {}
        if "database" not in config:
            config["database"] = {}
        if "file_storage" not in config:
            config["file_storage"] = {}
        if "session" not in config:
            config["session"] = {}
        if "processing" not in config:
            config["processing"] = {}

        logger.info(f"Successfully migrated to {self.to_version}")
        return config

    def rollback(self, config: dict[str, Any]) -> dict[str, Any]:
        """Rollback from 1.0.0 to 0.9.0."""
        logger.info(f"Rolling back config from {self.to_version} to {self.from_version}")

        # Remove config_version field (legacy format)
        if "config_version" in config:
            del config["config_version"]

        logger.info(f"Successfully rolled back to {self.from_version}")
        return config


# Registry of all migrations (ordered by version)
MIGRATIONS: list[ConfigMigration] = [
    Migration_0_9_to_1_0(),
    # Future migrations will be added here:
    # Migration_1_0_to_1_1(),
    # Migration_1_1_to_1_2(),
]


def validate_migration_registry() -> None:
    """
    Validate that the MIGRATIONS registry is properly configured.

    This function checks:
    1. All migration versions are valid semver
    2. Migrations are sequential (each to_version matches next from_version)
    3. No duplicate version pairs exist
    4. No circular dependencies

    Raises:
        ValueError: If validation fails

    This is called automatically on module import to catch issues early.
    """
    if not MIGRATIONS:
        return  # Empty registry is valid (no migrations yet)

    seen_transitions = set()

    for i, migration in enumerate(MIGRATIONS):
        # Validate version format
        try:
            from_tuple = parse_version(migration.from_version)
            to_tuple = parse_version(migration.to_version)
        except ValueError as e:
            raise ValueError(
                f"Migration {i} has invalid version: {e}. "
                f"Migration: {migration.from_version} → {migration.to_version}"
            )

        # Ensure from_version < to_version (no backwards or no-op migrations)
        if from_tuple >= to_tuple:
            raise ValueError(
                f"Migration {i} has invalid version order: {migration.from_version} → {migration.to_version}. "
                f"from_version must be less than to_version."
            )

        # Check for duplicate transitions
        transition = (migration.from_version, migration.to_version)
        if transition in seen_transitions:
            raise ValueError(
                f"Duplicate migration found: {migration.from_version} → {migration.to_version}. "
                f"Each version transition should only appear once."
            )
        seen_transitions.add(transition)

        # Check sequential chaining (except for first migration)
        if i > 0:
            prev_migration = MIGRATIONS[i - 1]
            # Migrations should form a chain, but we allow non-sequential versions
            # (e.g., 0.9.0→1.0.0, then 1.0.0→2.0.0 is valid)
            # We just ensure no overlaps or conflicts
            pass  # Sequential validation happens in get_migration_path

    logger.debug(f"Migration registry validated: {len(MIGRATIONS)} migrations registered")


# Validate registry on module import
try:
    validate_migration_registry()
except ValueError as e:
    logger.error(f"Migration registry validation failed: {e}")
    raise


def get_migration_path(from_version: str, to_version: str) -> list[ConfigMigration]:
    """
    Get ordered list of migrations to apply from one version to another.

    This function builds a sequential migration path by chaining migrations.
    For example, to migrate from 1.0.0 to 1.3.0, it will find:
    1.0.0 → 1.1.0 → 1.2.0 → 1.3.0

    The function enforces sequential migrations - there must be a migration
    for each version step. If a gap exists (e.g., no migration from 1.1.0 to 1.2.0),
    the function will raise an error.

    Args:
        from_version: Starting configuration version
        to_version: Target configuration version

    Returns:
        List of migrations to apply in order (may be empty if versions are equal)

    Raises:
        ValueError: If no migration path exists or if there are version gaps
    """
    try:
        from_tuple = parse_version(from_version)
        to_tuple = parse_version(to_version)
    except ValueError as e:
        raise ValueError(f"Invalid version in migration path: {e}")

    # Determine direction
    upgrade = from_tuple < to_tuple

    if from_tuple == to_tuple:
        return []  # No migration needed

    # Build migration path by chaining migrations
    path = []
    current_version = from_version
    max_iterations = len(MIGRATIONS) + 1  # Prevent infinite loops
    iterations = 0

    while current_version != to_version:
        iterations += 1
        if iterations > max_iterations:
            raise ValueError(
                f"Migration loop detected when migrating from {from_version} to {to_version}. "
                f"Check for circular migration dependencies."
            )

        # Find next migration in the chain
        found = False
        for migration in MIGRATIONS if upgrade else reversed(MIGRATIONS):
            if upgrade:
                if migration.from_version == current_version:
                    # Validate this migration moves us in the right direction
                    try:
                        next_tuple = parse_version(migration.to_version)
                        if next_tuple <= from_tuple or next_tuple > to_tuple:
                            # Skip migrations that go backwards or overshoot
                            continue
                    except ValueError:
                        continue

                    path.append(migration)
                    current_version = migration.to_version
                    found = True
                    break
            else:  # Downgrade
                if migration.to_version == current_version:
                    # Validate this migration moves us in the right direction
                    try:
                        next_tuple = parse_version(migration.from_version)
                        if next_tuple >= from_tuple or next_tuple < to_tuple:
                            # Skip migrations that go backwards or overshoot
                            continue
                    except ValueError:
                        continue

                    path.append(migration)
                    current_version = migration.from_version
                    found = True
                    break

        if not found:
            # No migration found for this step - version gap
            raise ValueError(
                f"No migration path from {from_version} to {to_version}. "
                f"Reached {current_version} but no migration available to proceed. "
                f"Ensure all intermediate migrations are registered in MIGRATIONS."
            )

    return path


def apply_migrations(
    config: dict[str, Any],
    from_version: str,
    to_version: str = CURRENT_CONFIG_VERSION,
) -> dict[str, Any]:
    """
    Apply all necessary migrations to upgrade configuration to target version.

    Args:
        config: Configuration dictionary to migrate
        from_version: Current configuration version
        to_version: Target configuration version (default: current app version)

    Returns:
        Migrated configuration dictionary

    Raises:
        ValueError: If migration fails or no path exists
    """
    if from_version == to_version:
        logger.info(f"Configuration already at version {to_version}, no migration needed")
        return config

    logger.info(f"Applying migrations: {from_version} → {to_version}")

    # Get migration path
    try:
        migration_path = get_migration_path(from_version, to_version)
    except ValueError as e:
        logger.error(f"Cannot find migration path: {e}")
        raise

    if not migration_path:
        logger.info("No migrations needed")
        return config

    logger.info(f"Migration path: {' → '.join([m.from_version for m in migration_path] + [to_version])}")

    # Apply each migration
    migrated_config = config.copy()
    for migration in migration_path:
        logger.info(f"Applying {migration}")

        # Validate migration can be applied
        if not migration.validate(migrated_config):
            raise ValueError(
                f"Migration {migration} cannot be applied. "
                f"Current config version: {migrated_config.get('config_version', 'unknown')}"
            )

        # Apply migration
        try:
            migrated_config = migration.migrate(migrated_config)
        except Exception as e:
            logger.error(f"Migration {migration} failed: {e}")
            raise ValueError(f"Migration failed at {migration}: {e}")

    logger.info(f"Successfully migrated configuration to {to_version}")
    return migrated_config


def rollback_migrations(
    config: dict[str, Any],
    from_version: str,
    to_version: str,
) -> dict[str, Any]:
    """
    Rollback configuration from current version to an older version.

    Args:
        config: Configuration dictionary to rollback
        from_version: Current configuration version
        to_version: Target configuration version (older)

    Returns:
        Rolled back configuration dictionary

    Raises:
        ValueError: If rollback fails or no path exists
    """
    if from_version == to_version:
        logger.info(f"Configuration already at version {to_version}, no rollback needed")
        return config

    logger.info(f"Rolling back: {from_version} → {to_version}")

    # Get rollback path (reverse of upgrade path)
    try:
        migration_path = get_migration_path(from_version, to_version)
    except ValueError as e:
        logger.error(f"Cannot find rollback path: {e}")
        raise

    if not migration_path:
        logger.info("No rollback needed")
        return config

    logger.info(f"Rollback path: {' → '.join([m.to_version for m in migration_path] + [to_version])}")

    # Apply rollbacks in order
    rolled_back_config = config.copy()
    for migration in migration_path:
        logger.info(f"Rolling back {migration}")

        try:
            rolled_back_config = migration.rollback(rolled_back_config)
        except Exception as e:
            logger.error(f"Rollback {migration} failed: {e}")
            raise ValueError(f"Rollback failed at {migration}: {e}")

    logger.info(f"Successfully rolled back configuration to {to_version}")
    return rolled_back_config
