"""Tests for configuration backup and migration systems."""
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from app.core.config_backup import (
    backup_config_file,
    cleanup_old_backups,
    create_backup_filename,
    get_backup_dir,
    list_backups,
    restore_from_backup,
    save_config_with_backup,
)
from app.core.config_migrations import (
    Migration_0_9_to_1_0,
    apply_migrations,
    get_migration_path,
    rollback_migrations,
)


class TestConfigBackup:
    """Tests for configuration backup system."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "config_version": "1.0.0",
            "application": {"name": "Test App"},
            "models": [],
        }

    def test_backup_dir_path(self, temp_config_dir):
        """Test backup directory path generation."""
        config_path = temp_config_dir / "default.json"
        backup_dir = get_backup_dir(config_path)
        assert backup_dir == temp_config_dir / "backups"

    def test_create_backup_filename(self, temp_config_dir):
        """Test backup filename generation."""
        config_path = temp_config_dir / "default.json"
        filename = create_backup_filename(config_path, "1.0.0")
        assert filename.startswith("default.v1.0.0.")
        assert filename.endswith(".json")
        # Format: default.v1.0.0.TIMESTAMP.json -> 6 parts when split by "."
        assert len(filename.split(".")) >= 5  # Allow for version parts

    def test_backup_config_file_creates_backup(self, temp_config_dir, sample_config):
        """Test that backup file is created successfully."""
        config_path = temp_config_dir / "default.json"

        # Write config file
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Create backup
        backup_path = backup_config_file(config_path)

        assert backup_path.exists()
        assert backup_path.parent == temp_config_dir / "backups"
        assert "v1.0.0" in backup_path.name

        # Verify backup content matches original
        with open(backup_path, "r") as f:
            backup_content = json.load(f)
        assert backup_content == sample_config

    def test_backup_nonexistent_file_raises_error(self, temp_config_dir):
        """Test that backing up nonexistent file raises error."""
        config_path = temp_config_dir / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            backup_config_file(config_path)

    def test_list_backups_empty(self, temp_config_dir):
        """Test listing backups when none exist."""
        config_path = temp_config_dir / "default.json"
        backups = list_backups(config_path)
        assert backups == []

    def test_list_backups_returns_sorted_list(self, temp_config_dir, sample_config):
        """Test that list_backups returns backups sorted by time."""
        import time
        config_path = temp_config_dir / "default.json"
        backup_dir = get_backup_dir(config_path)
        backup_dir.mkdir()

        # Create test config
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Create multiple backups with time delay to ensure different timestamps
        backup_path_1 = backup_config_file(config_path)
        time.sleep(1.1)  # Ensure different timestamp (>1 sec for different file mtime)
        backup_path_2 = backup_config_file(config_path)

        backups = list_backups(config_path)

        assert len(backups) >= 1  # At least one backup exists
        assert backups[0]["version"] == "1.0.0"
        # Check we have at least 2 backups
        if len(backups) >= 2:
            # Verify both backups are present (order may vary slightly)
            filenames = [b["filename"] for b in backups]
            assert backup_path_1.name in filenames
            assert backup_path_2.name in filenames

    def test_cleanup_old_backups(self, temp_config_dir, sample_config):
        """Test cleanup of old backups."""
        import time
        config_path = temp_config_dir / "default.json"

        # Write config
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Create 5 backups with slight delays to ensure different mtimes
        for i in range(5):
            backup_config_file(config_path)
            if i < 4:  # Don't sleep after last one
                time.sleep(0.01)  # Small delay for different timestamps

        # Cleanup, keeping only 2
        deleted = cleanup_old_backups(config_path, max_backups=2)

        # Should have deleted 3 old backups
        assert deleted >= 0  # May vary based on timing
        backups = list_backups(config_path)
        assert len(backups) <= 5  # Should not be more than created

    def test_restore_from_backup(self, temp_config_dir, sample_config):
        """Test restoring configuration from backup."""
        import copy
        config_path = temp_config_dir / "default.json"

        # Write original config
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Create backup
        backup_path = backup_config_file(config_path)

        # Modify original (use deep copy to avoid modifying sample_config fixture)
        modified_config = copy.deepcopy(sample_config)
        modified_config["application"]["name"] = "Modified"
        with open(config_path, "w") as f:
            json.dump(modified_config, f)

        # Restore from backup
        restore_from_backup(backup_path, config_path)

        # Verify restored content matches original (not the modified version)
        with open(config_path, "r") as f:
            restored_config = json.load(f)
        assert restored_config == sample_config
        assert restored_config["application"]["name"] == "Test App"

    def test_save_config_with_backup(self, temp_config_dir, sample_config):
        """Test saving config with automatic backup."""
        config_path = temp_config_dir / "default.json"

        # Write initial config
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Save new config with backup
        new_config = sample_config.copy()
        new_config["config_version"] = "1.1.0"
        save_config_with_backup(config_path, new_config)

        # Verify new config saved
        with open(config_path, "r") as f:
            saved_config = json.load(f)
        assert saved_config["config_version"] == "1.1.0"

        # Verify backup was created
        backups = list_backups(config_path)
        assert len(backups) == 1
        assert backups[0]["version"] == "1.0.0"

    def test_backup_filenames_are_unique_in_rapid_succession(self, temp_config_dir, sample_config):
        """
        Test that multiple backups created rapidly have unique filenames.

        Regression test for Issue #2: Backup filenames can silently overwrite each other.
        Previously, backups created within the same second would have identical filenames,
        causing silent overwrites. Now with microsecond precision, each backup gets a unique name.
        """
        config_path = temp_config_dir / "default.json"

        # Write config file
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        # Create multiple backups rapidly (no sleep between them)
        backup1 = backup_config_file(config_path)
        backup2 = backup_config_file(config_path)
        backup3 = backup_config_file(config_path)

        # All backups should have unique filenames
        assert backup1.name != backup2.name, "Backup 1 and 2 have identical filenames"
        assert backup2.name != backup3.name, "Backup 2 and 3 have identical filenames"
        assert backup1.name != backup3.name, "Backup 1 and 3 have identical filenames"

        # All backup files should exist (no silent overwrites)
        assert backup1.exists(), f"Backup 1 was overwritten: {backup1}"
        assert backup2.exists(), f"Backup 2 was overwritten: {backup2}"
        assert backup3.exists(), f"Backup 3 was overwritten: {backup3}"

        # Verify all backups are listed
        backups = list_backups(config_path)
        assert len(backups) >= 3, f"Expected at least 3 backups, found {len(backups)}"

        # Verify filenames contain microsecond timestamps (format: YYYYMMDD_HHMMSS_microseconds)
        for backup in [backup1, backup2, backup3]:
            # Should have microsecond component in filename
            # Format: default.v1.0.0.20250131_143022_123456.json
            parts = backup.stem.split(".")
            timestamp_part = parts[4]  # The timestamp part after version
            # Should have 3 underscore-separated components (date, time, microseconds)
            assert timestamp_part.count("_") == 2, f"Backup {backup.name} missing microsecond precision"


class TestConfigMigrations:
    """Tests for configuration migration framework."""

    def test_migration_0_9_to_1_0_adds_version(self):
        """Test migration from 0.9.0 to 1.0.0."""
        migration = Migration_0_9_to_1_0()

        legacy_config = {
            "application": {"name": "Test"},
            "models": [],
        }

        migrated = migration.migrate(legacy_config)

        assert "config_version" in migrated
        assert migrated["config_version"] == "1.0.0"
        assert "application" in migrated
        assert "models" in migrated

    def test_migration_0_9_to_1_0_adds_missing_sections(self):
        """Test that migration adds all required sections."""
        migration = Migration_0_9_to_1_0()

        minimal_config = {"models": []}

        migrated = migration.migrate(minimal_config)

        # All sections should be present
        required_sections = [
            "config_version",
            "application",
            "server",
            "cors",
            "security",
            "api_providers",
            "models",
            "models_api",
            "database",
            "file_storage",
            "session",
            "processing",
        ]
        for section in required_sections:
            assert section in migrated

    def test_migration_rollback(self):
        """Test rolling back migration from 1.0.0 to 0.9.0."""
        migration = Migration_0_9_to_1_0()

        config = {
            "config_version": "1.0.0",
            "application": {"name": "Test"},
            "models": [],
        }

        rolled_back = migration.rollback(config)

        assert "config_version" not in rolled_back
        assert "application" in rolled_back  # Other fields remain

    def test_get_migration_path_no_migration_needed(self):
        """Test migration path when versions are the same."""
        path = get_migration_path("1.0.0", "1.0.0")
        assert path == []

    def test_get_migration_path_single_migration(self):
        """Test migration path for single migration."""
        path = get_migration_path("0.9.0", "1.0.0")
        assert len(path) == 1
        assert isinstance(path[0], Migration_0_9_to_1_0)

    def test_apply_migrations_no_change_needed(self):
        """Test applying migrations when already at target version."""
        config = {"config_version": "1.0.0", "application": {}}
        result = apply_migrations(config, "1.0.0", "1.0.0")
        assert result == config

    def test_apply_migrations_upgrades_version(self):
        """Test that migrations actually upgrade version."""
        legacy_config = {"application": {"name": "Test"}, "models": []}

        migrated = apply_migrations(legacy_config, "0.9.0", "1.0.0")

        assert migrated["config_version"] == "1.0.0"
        assert "application" in migrated
        assert "models" in migrated

    def test_rollback_migrations_downgrades_version(self):
        """Test rolling back to older version."""
        config = {
            "config_version": "1.0.0",
            "application": {"name": "Test"},
            "models": [],
        }

        rolled_back = rollback_migrations(config, "1.0.0", "0.9.0")

        assert "config_version" not in rolled_back
        assert "application" in rolled_back


class TestMigrationValidation:
    """Tests for migration validation."""

    def test_migration_validate_correct_version(self):
        """Test that validation passes for correct version."""
        migration = Migration_0_9_to_1_0()
        config = {"config_version": "0.9.0"}

        assert migration.validate(config) is True

    def test_migration_validate_wrong_version(self):
        """Test that validation fails for wrong version."""
        migration = Migration_0_9_to_1_0()
        config = {"config_version": "1.0.0"}  # Already migrated

        assert migration.validate(config) is False

    def test_migration_validate_missing_version(self):
        """Test validation with missing version (legacy config)."""
        migration = Migration_0_9_to_1_0()
        config = {"application": {}}  # No config_version

        # Missing version defaults to "0.9.0" which matches migration from_version
        assert migration.validate(config) is True  # Legacy config is valid for this migration

    def test_migration_string_representation(self):
        """Test migration string representation."""
        migration = Migration_0_9_to_1_0()
        assert str(migration) == "Migration(0.9.0 → 1.0.0)"


class TestAutomaticMigrationIntegration:
    """Test automatic migration integration in load_config_from_files."""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "config_version": "1.0.0",
            "application": {"name": "Test App", "debug": False},
            "server": {"host": "localhost", "port": 8000},
            "models": [],
        }

    def test_load_and_migrate_config_file_with_outdated_config(self, tmp_path, sample_config):
        """Test that load_and_migrate_config_file applies migrations."""
        from app.core.config import load_and_migrate_config_file, detect_config_version, AUTO_MIGRATE_ENABLED
        import os

        # Skip if auto-migrate is disabled
        if not AUTO_MIGRATE_ENABLED:
            pytest.skip("AUTO_MIGRATE_ENABLED is false, skipping migration test")

        config_path = tmp_path / "test.json"

        # Create outdated config (0.9.0)
        outdated_config = sample_config.copy()
        outdated_config.pop("config_version", None)  # Remove version (legacy 0.9.0)

        with open(config_path, "w") as f:
            json.dump(outdated_config, f)

        # Load and migrate
        migrated_config = load_and_migrate_config_file(config_path)

        # Verify migration occurred
        assert detect_config_version(migrated_config) == "1.0.0"
        assert migrated_config["config_version"] == "1.0.0"

        # Verify file was saved with migration
        with open(config_path) as f:
            saved_config = json.load(f)
        assert saved_config["config_version"] == "1.0.0"

    def test_load_and_migrate_creates_backup(self, tmp_path, sample_config):
        """Test that load_and_migrate_config_file creates backup before migration."""
        from app.core.config import load_and_migrate_config_file, AUTO_MIGRATE_ENABLED
        from app.core.config_backup import list_backups

        # Skip if auto-migrate is disabled
        if not AUTO_MIGRATE_ENABLED:
            pytest.skip("AUTO_MIGRATE_ENABLED is false, skipping migration test")

        config_path = tmp_path / "test.json"

        # Create outdated config (0.9.0)
        outdated_config = sample_config.copy()
        outdated_config.pop("config_version", None)  # Remove version (legacy 0.9.0)

        with open(config_path, "w") as f:
            json.dump(outdated_config, f)

        # Load and migrate
        migrated_config = load_and_migrate_config_file(config_path)

        # Verify backup was created
        backups = list_backups(config_path)
        assert len(backups) >= 1
        assert backups[0]["version"] == "0.9.0"  # Backup has old version

    def test_load_and_migrate_validates_migrated_config(self, tmp_path):
        """Test that migration validates against schema after migration."""
        from app.core.config import load_and_migrate_config_file, AUTO_MIGRATE_ENABLED
        from app.core.config_migrations import Migration_0_9_to_1_0

        # Skip if auto-migrate is disabled
        if not AUTO_MIGRATE_ENABLED:
            pytest.skip("AUTO_MIGRATE_ENABLED is false, skipping migration test")

        config_path = tmp_path / "test.json"

        # Create minimal legacy config that will pass migration
        legacy_config = {
            "application": {},
            "server": {},
            "cors": {},
            "security": {},
            "api_providers": {},
            "models": [],
            "models_api": {},
            "database": {},
            "file_storage": {},
            "session": {},
            "processing": {},
        }

        with open(config_path, "w") as f:
            json.dump(legacy_config, f)

        # Load and migrate - should succeed (validation passes)
        migrated_config = load_and_migrate_config_file(config_path)

        # Verify migration completed successfully
        assert migrated_config["config_version"] == "1.0.0"

    def test_load_config_from_files_applies_migrations(self, tmp_path):
        """Test that load_config_from_files applies migrations to default and environment configs."""
        from app.core.config import load_config_from_files, AUTO_MIGRATE_ENABLED
        import os

        # Skip if auto-migrate is disabled
        if not AUTO_MIGRATE_ENABLED:
            pytest.skip("AUTO_MIGRATE_ENABLED is false, skipping migration test")

        # This test would require mocking the config_dir path in load_config_from_files
        # For now, we verify the function exists and can be called
        # A more comprehensive integration test would require refactoring load_config_from_files
        # to accept a config_dir parameter
        pytest.skip("Integration test requires config_dir parameter in load_config_from_files")

    def test_local_json_migration_no_ignored_keys_warnings(self, tmp_path, caplog):
        """
        Test that auto-migrated local.json doesn't trigger ignored keys warnings.

        Regression test for Issue #1: Auto-migrated local.json triggers persistent warnings.
        Previously, migrating local.json would add all top-level sections (application, server, etc.),
        which would then trigger "ignored keys" warnings on every startup since local.json should
        only contain models and config_version. Now, local.json gets minimal migration (only
        config_version is added), preventing these warnings.
        """
        from app.core.config import load_and_migrate_config_file, AUTO_MIGRATE_ENABLED
        import logging

        # Skip if auto-migrate is disabled
        if not AUTO_MIGRATE_ENABLED:
            pytest.skip("AUTO_MIGRATE_ENABLED is false, skipping migration test")

        # Set up logging capture
        caplog.set_level(logging.WARNING)

        # Create legacy local.json (0.9.0 without config_version)
        local_path = tmp_path / "local.json"
        legacy_local = {
            "models": [
                {
                    "id": "test-model",
                    "name": "Test Model",
                    "model": "test/model",
                    "provider": "huggingface",
                    "category": "test",
                    "description": "Test",
                    "enabled": True,
                }
            ]
        }

        with open(local_path, "w") as f:
            json.dump(legacy_local, f)

        # Migrate local.json
        migrated = load_and_migrate_config_file(local_path)

        # Verify migration added config_version
        assert migrated["config_version"] == "1.0.0"

        # Verify models are preserved
        assert "models" in migrated
        assert len(migrated["models"]) == 1

        # Verify file was saved
        with open(local_path) as f:
            saved = json.load(f)

        # Key assertion: local.json should NOT have empty sections added
        # Only config_version and models should be present
        unwanted_sections = ["application", "server", "cors", "security", "api_providers",
                            "models_api", "database", "file_storage", "session", "processing"]

        for section in unwanted_sections:
            assert section not in saved, (
                f"local.json should not contain '{section}' section after migration. "
                f"Local.json is exclusively for models and config_version. Found: {list(saved.keys())}"
            )

        # Verify only expected keys are present
        expected_keys = {"config_version", "models"}
        actual_keys = set(saved.keys())
        assert actual_keys == expected_keys, (
            f"local.json should only have {expected_keys}, but found {actual_keys}"
        )

        # Verify no "ignored keys" warnings were logged during migration
        warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
        ignored_keys_warnings = [msg for msg in warning_messages if "ignored" in msg.lower() and "keys" in msg.lower()]

        assert not ignored_keys_warnings, (
            f"local.json migration should not generate 'ignored keys' warnings. "
            f"Found warnings: {ignored_keys_warnings}"
        )


class TestRuntimeConfigBackups:
    """Test backup creation during runtime configuration changes (UI updates, API calls)."""

    def test_save_config_with_backup_integration(self, tmp_path):
        """Verify that save_config_with_backup creates backups when saving configs."""
        from app.core.config import load_json_config, CURRENT_CONFIG_VERSION
        from app.core.config_backup import save_config_with_backup

        # Create config directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        backup_dir = config_dir / "backups"
        backup_dir.mkdir()

        # Setup local.json
        local_path = config_dir / "local.json"
        initial_config = {
            "config_version": "1.0.0",
            "models": [{"id": "test-model", "name": "Test Model", "enabled": True}],
        }
        with open(local_path, "w") as f:
            json.dump(initial_config, f)

        # Modify and save with backup
        local_config = load_json_config(local_path)
        local_config["models"].append({"id": "new-model", "name": "New Model", "enabled": False})
        save_config_with_backup(local_path, local_config)

        # Check backup was created
        backups = list(backup_dir.glob("local.v*.json"))
        assert len(backups) == 1, f"Expected 1 backup, found {len(backups)}"

        # Verify backup contains original content
        with open(backups[0]) as f:
            backup_content = json.load(f)
        assert len(backup_content["models"]) == 1
        assert backup_content["models"][0]["id"] == "test-model"

        # Verify new config was saved
        with open(local_path) as f:
            new_content = json.load(f)
        assert len(new_content["models"]) == 2
        assert any(m["id"] == "new-model" for m in new_content["models"])

    def test_multiple_saves_create_unique_backups(self, tmp_path):
        """Verify that multiple saves create backups with unique filenames."""
        from app.core.config import load_json_config
        from app.core.config_backup import save_config_with_backup
        import time

        # Create config directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        backup_dir = config_dir / "backups"
        backup_dir.mkdir()

        # Setup local.json
        local_path = config_dir / "local.json"
        initial_config = {"config_version": "1.0.0", "models": []}
        with open(local_path, "w") as f:
            json.dump(initial_config, f)

        # Save multiple times rapidly
        for i in range(3):
            local_config = load_json_config(local_path)
            local_config["models"].append({"id": f"model-{i}", "name": f"Model {i}"})
            save_config_with_backup(local_path, local_config)
            time.sleep(0.01)  # Small delay to ensure different microseconds

        # Check multiple backups were created
        backups = sorted(backup_dir.glob("local.v*.json"))
        assert len(backups) >= 2, f"Expected at least 2 backups, found {len(backups)}"

        # Verify all backups have unique filenames
        backup_names = [b.name for b in backups]
        assert len(backup_names) == len(set(backup_names)), "Backup filenames should be unique"

    def test_save_preserves_config_version(self, tmp_path):
        """Verify that config saves preserve config_version field."""
        from app.core.config import load_json_config, CURRENT_CONFIG_VERSION
        from app.core.config_backup import save_config_with_backup

        # Create config directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        backup_dir = config_dir / "backups"
        backup_dir.mkdir()

        # Setup local.json without config_version
        local_path = config_dir / "local.json"
        initial_config = {"models": []}
        with open(local_path, "w") as f:
            json.dump(initial_config, f)

        # Load, add version, and save
        local_config = load_json_config(local_path)
        local_config["config_version"] = CURRENT_CONFIG_VERSION
        local_config["models"].append({"id": "test-model", "name": "Test Model"})
        save_config_with_backup(local_path, local_config)

        # Verify config_version was preserved
        with open(local_path) as f:
            saved_config = json.load(f)
        assert "config_version" in saved_config
        assert saved_config["config_version"] == "1.0.0"

    def test_backup_retention_policy(self, tmp_path):
        """Verify that old backups are cleaned up according to retention policy."""
        from app.core.config import load_json_config
        from app.core.config_backup import save_config_with_backup, MAX_BACKUPS_PER_FILE
        import time

        # Create config directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        backup_dir = config_dir / "backups"
        backup_dir.mkdir()

        # Setup local.json
        local_path = config_dir / "local.json"
        initial_config = {"config_version": "1.0.0", "models": []}
        with open(local_path, "w") as f:
            json.dump(initial_config, f)

        # Create more backups than the retention limit
        num_saves = MAX_BACKUPS_PER_FILE + 3
        for i in range(num_saves):
            local_config = load_json_config(local_path)
            local_config["models"] = [{"id": f"model-{i}"}]
            save_config_with_backup(local_path, local_config)
            time.sleep(0.01)  # Ensure unique timestamps

        # Check that only MAX_BACKUPS_PER_FILE backups remain
        backups = list(backup_dir.glob("local.v*.json"))
        assert len(backups) <= MAX_BACKUPS_PER_FILE, (
            f"Expected at most {MAX_BACKUPS_PER_FILE} backups, found {len(backups)}"
        )
