#!/usr/bin/env python3
"""Manual configuration migration script."""
import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import (
    CURRENT_CONFIG_VERSION,
    detect_config_version,
    load_json_config,
)
from app.core.config_backup import backup_config_file, save_config_with_backup
from app.core.config_migrations import apply_migrations, rollback_migrations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate configuration files between versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate to latest version (with automatic backup)
  python backend/scripts/migrate_config.py backend/config/default.json

  # Dry-run migration (show what would happen)
  python backend/scripts/migrate_config.py backend/config/default.json --dry-run

  # Migrate to specific version
  python backend/scripts/migrate_config.py backend/config/default.json --to 1.1.0

  # Rollback to older version
  python backend/scripts/migrate_config.py backend/config/default.json \\
    --to 1.0.0 --rollback

  # Migrate all config files
  python backend/scripts/migrate_config.py backend/config/default.json \\
    backend/config/production.json \\
    backend/config/testing.json
""",
    )

    parser.add_argument(
        "config_files",
        nargs="+",
        type=str,
        help="Path(s) to configuration file(s) to migrate",
    )

    parser.add_argument(
        "--to",
        "-t",
        dest="target_version",
        type=str,
        default=CURRENT_CONFIG_VERSION,
        help=f"Target version to migrate to (default: {CURRENT_CONFIG_VERSION})",
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show what would be migrated without making changes",
    )

    parser.add_argument(
        "--rollback",
        "-r",
        action="store_true",
        help="Rollback to an older version (requires --to)",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip automatic backup (NOT RECOMMENDED)",
    )

    args = parser.parse_args()

    success_count = 0
    failed_count = 0

    for config_file in args.config_files:
        config_path = Path(config_file)

        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            failed_count += 1
            continue

        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {config_path}")
        logger.info(f"{'='*70}")

        try:
            # Load config
            config = load_json_config(config_path)
            current_version = detect_config_version(config)

            logger.info(f"Current version: {current_version}")
            logger.info(f"Target version:  {args.target_version}")

            if current_version == args.target_version:
                logger.info("✓ Already at target version, no migration needed")
                success_count += 1
                continue

            # Determine migration direction
            is_rollback = args.rollback

            # Apply migration
            if args.dry_run:
                logger.info("\n--- DRY RUN MODE (no changes will be made) ---")

            if is_rollback:
                logger.info(f"Performing rollback: {current_version} → {args.target_version}")
                migrated_config = rollback_migrations(config, current_version, args.target_version)
            else:
                logger.info(f"Performing migration: {current_version} → {args.target_version}")
                migrated_config = apply_migrations(config, current_version, args.target_version)

            # Show diff (in dry-run mode or verbose)
            if args.dry_run:
                logger.info("\n--- Migrated Configuration Preview ---")
                logger.info(json.dumps(migrated_config, indent=2))
                logger.info("\n✓ Migration validation successful (dry-run)")
                success_count += 1
                continue

            # Save migrated config with backup
            if not args.no_backup:
                logger.info("Creating backup...")
                backup_path = backup_config_file(config_path)
                logger.info(f"✓ Backup created: {backup_path}")

            # Save migrated config
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(migrated_config, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Successfully migrated {config_path.name} to version {args.target_version}")
            success_count += 1

        except Exception as e:
            logger.error(f"✗ Migration failed for {config_path.name}: {e}")
            failed_count += 1

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("Migration Summary")
    logger.info(f"{'='*70}")
    logger.info(f"Total files: {len(args.config_files)}")
    logger.info(f"✓ Successful: {success_count}")
    if failed_count > 0:
        logger.info(f"✗ Failed: {failed_count}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
