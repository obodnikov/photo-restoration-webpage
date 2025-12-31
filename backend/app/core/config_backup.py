"""Configuration backup and restore utilities."""
import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import detect_config_version, load_json_config

logger = logging.getLogger(__name__)

# Backup configuration
MAX_BACKUPS_PER_FILE = 10  # Keep last 10 backups per config file


def get_backup_dir(config_path: Path) -> Path:
    """
    Get backup directory for a configuration file.

    Args:
        config_path: Path to configuration file

    Returns:
        Path to backup directory
    """
    return config_path.parent / "backups"


def create_backup_filename(config_path: Path, version: str) -> str:
    """
    Generate timestamped backup filename with microsecond precision.

    Args:
        config_path: Original config file path
        version: Configuration version

    Returns:
        Backup filename (e.g., "default.v1.0.0.20250131_143022_123456.json")

    Note:
        Uses microsecond precision to ensure unique filenames even when
        multiple backups are created in rapid succession (e.g., scripts, CI/CD).
        This prevents silent overwrites and ensures backup retention guarantees.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = config_path.stem  # e.g., "default", "production"
    return f"{stem}.v{version}.{timestamp}.json"


def backup_config_file(config_path: Path) -> Path:
    """
    Create timestamped backup of configuration file.

    Args:
        config_path: Path to configuration file to backup

    Returns:
        Path to created backup file

    Raises:
        FileNotFoundError: If config file doesn't exist
        IOError: If backup cannot be created
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Detect version from config
    try:
        config_data = load_json_config(config_path)
        version = detect_config_version(config_data)
    except Exception as e:
        logger.warning(f"Could not detect version, using 'unknown': {e}")
        version = "unknown"

    # Create backup directory if it doesn't exist
    backup_dir = get_backup_dir(config_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    backup_filename = create_backup_filename(config_path, version)
    backup_path = backup_dir / backup_filename

    # Copy file to backup
    shutil.copy2(config_path, backup_path)
    logger.info(f"Created backup: {backup_path}")

    return backup_path


def cleanup_old_backups(config_path: Path, max_backups: int = MAX_BACKUPS_PER_FILE) -> int:
    """
    Remove old backups, keeping only the most recent N backups.

    Args:
        config_path: Original config file path
        max_backups: Maximum number of backups to keep

    Returns:
        Number of backups deleted
    """
    backup_dir = get_backup_dir(config_path)
    if not backup_dir.exists():
        return 0

    # Find all backups for this config file
    stem = config_path.stem  # e.g., "default", "production"
    pattern = f"{stem}.v*.json"
    backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    # Delete old backups (keep newest max_backups)
    deleted = 0
    for backup in backups[max_backups:]:
        try:
            backup.unlink()
            logger.info(f"Deleted old backup: {backup}")
            deleted += 1
        except Exception as e:
            logger.error(f"Failed to delete backup {backup}: {e}")

    return deleted


def list_backups(config_path: Path) -> list[dict[str, Any]]:
    """
    List all available backups for a configuration file.

    Args:
        config_path: Original config file path

    Returns:
        List of backup metadata dictionaries with keys:
        - path: Path to backup file
        - filename: Backup filename
        - version: Config version
        - timestamp: Creation timestamp
        - size_bytes: File size in bytes
    """
    backup_dir = get_backup_dir(config_path)
    if not backup_dir.exists():
        return []

    stem = config_path.stem
    pattern = f"{stem}.v*.json"
    backups = []

    # Regex pattern to parse backup filename
    # Format: <stem>.v<major>.<minor>.<patch>.<timestamp>.json
    # Example: default.v1.0.0.20250131_143022_123456.json (with microseconds)
    # Legacy:  default.v1.0.0.20250131_143022.json (without microseconds)
    backup_pattern = re.compile(
        r"^(?P<stem>[^.]+)"  # Config name (stem)
        r"\.v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"  # Version: v<major>.<minor>.<patch>
        r"\.(?P<timestamp>\d{8}_\d{6}(?:_\d{6})?)"  # Timestamp: YYYYMMDD_HHMMSS or YYYYMMDD_HHMMSS_microseconds
        r"\.json$"  # Extension
    )

    for backup_path in sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            version = "unknown"
            timestamp_str = "unknown"
            size_bytes = 0

            # Try to parse filename with regex
            match = backup_pattern.match(backup_path.name)
            if match:
                # Extract version and timestamp from regex groups
                version = f"{match.group('major')}.{match.group('minor')}.{match.group('patch')}"
                timestamp_str = match.group('timestamp')
                logger.debug(f"Parsed backup {backup_path.name}: version={version}, timestamp={timestamp_str}")
            else:
                # Filename doesn't match expected pattern
                logger.warning(
                    f"Backup filename does not match expected pattern: {backup_path.name}. "
                    f"Expected format: {stem}.v<major>.<minor>.<patch>.<timestamp>.json"
                )

            # Get file size safely
            try:
                size_bytes = backup_path.stat().st_size
            except OSError as e:
                logger.warning(f"Could not get file size for {backup_path}: {e}")
                size_bytes = 0

            backups.append({
                "path": str(backup_path),
                "filename": backup_path.name,
                "version": version,
                "timestamp": timestamp_str,
                "size_bytes": size_bytes,
            })
        except Exception as e:
            # Log but continue processing other backups
            logger.warning(f"Error reading backup metadata for {backup_path}: {e}")
            # Include the backup with minimal metadata so it's not lost
            try:
                backups.append({
                    "path": str(backup_path),
                    "filename": backup_path.name,
                    "version": "unknown",
                    "timestamp": "unknown",
                    "size_bytes": 0,
                })
            except Exception:
                # If we can't even get the filename, skip this backup
                logger.error(f"Failed to process backup file {backup_path}, skipping")
                pass

    return backups


def restore_from_backup(backup_path: Path, target_path: Path) -> None:
    """
    Restore configuration from a backup file.

    Args:
        backup_path: Path to backup file
        target_path: Path to restore to (usually original config file)

    Raises:
        FileNotFoundError: If backup file doesn't exist
        IOError: If restore fails
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    # Validate backup is valid JSON before restoring
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Backup file is not valid JSON: {e}")

    # Create backup of current file before restoring (safety)
    if target_path.exists():
        try:
            pre_restore_backup = backup_config_file(target_path)
            logger.info(f"Created safety backup before restore: {pre_restore_backup}")
        except Exception as e:
            logger.warning(f"Could not create safety backup: {e}")

    # Restore backup
    shutil.copy2(backup_path, target_path)
    logger.info(f"Restored configuration from {backup_path} to {target_path}")


def save_config_with_backup(config_path: Path, config_data: dict[str, Any]) -> None:
    """
    Save configuration with automatic backup of the current file.

    Args:
        config_path: Path to configuration file
        config_data: Configuration dictionary to save

    Raises:
        IOError: If save fails
    """
    # Backup existing file if it exists
    if config_path.exists():
        try:
            backup_path = backup_config_file(config_path)
            logger.info(f"Backed up existing config before save: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise IOError(f"Cannot save config without backup: {e}")

    # Save new config
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise

    # Cleanup old backups
    try:
        deleted = cleanup_old_backups(config_path)
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old backups")
    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {e}")
