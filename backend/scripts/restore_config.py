#!/usr/bin/env python3
"""Manual configuration restore script."""
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_backup import list_backups, restore_from_backup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for restore script."""
    parser = argparse.ArgumentParser(
        description="Restore configuration from a backup file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available backups
  python backend/scripts/restore_config.py backend/config/default.json --list

  # Restore from specific backup file
  python backend/scripts/restore_config.py backend/config/default.json \\
    --from backend/config/backups/default.v1.0.0.20250131_143022.json

  # Restore from latest backup
  python backend/scripts/restore_config.py backend/config/default.json --latest
""",
    )

    parser.add_argument(
        "config_file",
        type=str,
        help="Path to configuration file to restore to",
    )

    parser.add_argument(
        "--from",
        "-f",
        dest="backup_file",
        type=str,
        help="Path to backup file to restore from",
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Restore from the latest backup",
    )

    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available backups",
    )

    args = parser.parse_args()

    config_path = Path(args.config_file)

    if args.list:
        # List available backups
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
                f"(version {backup['version']}, timestamp {backup['timestamp']}, {size_kb:.1f} KB)"
            )

        return 0

    # Validate arguments
    if not args.backup_file and not args.latest:
        logger.error("Error: Must specify either --from or --latest")
        parser.print_help()
        return 1

    if args.backup_file and args.latest:
        logger.error("Error: Cannot specify both --from and --latest")
        return 1

    # Determine backup file to restore
    if args.latest:
        logger.info("Finding latest backup...")
        backups = list_backups(config_path)
        if not backups:
            logger.error("No backups found")
            return 1
        backup_path = Path(backups[0]["path"])  # First in list is most recent
        logger.info(f"Latest backup: {backup_path.name}")
    else:
        backup_path = Path(args.backup_file)

    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        return 1

    # Confirm restore
    logger.warning(f"⚠ This will replace {config_path} with {backup_path.name}")
    logger.warning("   A safety backup of the current file will be created")
    response = input("Continue? (yes/no): ")

    if response.lower() not in ("yes", "y"):
        logger.info("Restore cancelled")
        return 0

    # Perform restore
    try:
        restore_from_backup(backup_path, config_path)
        logger.info(f"✓ Configuration restored successfully from {backup_path.name}")
        return 0
    except Exception as e:
        logger.error(f"✗ Restore failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
