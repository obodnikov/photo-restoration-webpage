#!/usr/bin/env python3
"""Manual configuration backup script."""
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_backup import backup_config_file, list_backups

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for backup script."""
    parser = argparse.ArgumentParser(
        description="Create a backup of a configuration file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup default.json
  python backend/scripts/backup_config.py backend/config/default.json

  # Backup production.json
  python backend/scripts/backup_config.py backend/config/production.json

  # List existing backups
  python backend/scripts/backup_config.py backend/config/default.json --list
""",
    )

    parser.add_argument(
        "config_file",
        type=str,
        help="Path to configuration file to backup",
    )

    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List existing backups instead of creating new one",
    )

    args = parser.parse_args()

    config_path = Path(args.config_file)

    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return 1

    if args.list:
        # List existing backups
        logger.info(f"Listing backups for {config_path.name}...")
        backups = list_backups(config_path)

        if not backups:
            logger.info("No backups found")
            return 0

        logger.info(f"Found {len(backups)} backups:")
        for i, backup in enumerate(backups, 1):
            size_kb = backup["size_bytes"] / 1024
            logger.info(
                f"  {i}. {backup['filename']} "
                f"(version {backup['version']}, {size_kb:.1f} KB)"
            )

        return 0

    # Create backup
    try:
        backup_path = backup_config_file(config_path)
        logger.info(f"✓ Backup created successfully: {backup_path}")
        return 0
    except Exception as e:
        logger.error(f"✗ Backup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
