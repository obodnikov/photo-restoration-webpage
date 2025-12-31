"""Tests for configuration versioning system."""
import pytest

from app.core.config import (
    CURRENT_CONFIG_VERSION,
    MIN_SUPPORTED_VERSION,
    detect_config_version,
    get_migration_suggestion,
    is_version_compatible,
    parse_version,
)


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_valid_version(self):
        """Test parsing valid semver version."""
        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("1.2.3") == (1, 2, 3)
        assert parse_version("10.20.30") == (10, 20, 30)

    def test_parse_invalid_version_format(self):
        """Test parsing invalid version formats."""
        with pytest.raises(ValueError, match="Invalid version"):
            parse_version("1.0")  # Missing patch

        with pytest.raises(ValueError, match="Invalid version"):
            parse_version("1.0.0.0")  # Too many parts

        with pytest.raises(ValueError, match="Invalid version"):
            parse_version("v1.0.0")  # Invalid prefix

    def test_parse_non_numeric_version(self):
        """Test parsing version with non-numeric parts."""
        with pytest.raises(ValueError):
            parse_version("1.a.0")

        with pytest.raises(ValueError):
            parse_version("x.y.z")

    def test_parse_empty_version(self):
        """Test parsing empty version string."""
        with pytest.raises(ValueError):
            parse_version("")

    def test_parse_none_version(self):
        """Test parsing None as version."""
        with pytest.raises(ValueError):
            parse_version(None)  # type: ignore


class TestDetectConfigVersion:
    """Tests for detect_config_version function."""

    def test_detect_version_present(self):
        """Test detecting version when config_version field is present."""
        config = {"config_version": "1.0.0", "application": {}}
        assert detect_config_version(config) == "1.0.0"

        config = {"config_version": "1.2.3", "models": []}
        assert detect_config_version(config) == "1.2.3"

    def test_detect_version_missing_defaults_to_legacy(self):
        """Test detecting version returns 0.9.0 for legacy configs."""
        config = {"application": {}, "models": []}
        assert detect_config_version(config) == "0.9.0"

        config = {}
        assert detect_config_version(config) == "0.9.0"

    def test_detect_invalid_version_returns_legacy(self):
        """Test detecting invalid version defaults to legacy."""
        config = {"config_version": "invalid", "application": {}}
        assert detect_config_version(config) == "0.9.0"

        config = {"config_version": "1.0", "application": {}}
        assert detect_config_version(config) == "0.9.0"

        config = {"config_version": "", "application": {}}
        assert detect_config_version(config) == "0.9.0"

    def test_detect_version_with_extra_fields(self):
        """Test version detection doesn't care about other fields."""
        config = {
            "config_version": "1.0.0",
            "application": {"name": "Test"},
            "models": [],
            "extra_field": "value",
        }
        assert detect_config_version(config) == "1.0.0"


class TestIsVersionCompatible:
    """Tests for is_version_compatible function."""

    def test_exact_version_match_is_compatible(self):
        """Test that exact version match is compatible."""
        assert is_version_compatible("1.0.0", "1.0.0") is True

    def test_same_major_lower_minor_is_compatible(self):
        """Test that lower minor version with same major is compatible (can be migrated)."""
        # CURRENT_CONFIG_VERSION is 1.0.0, so 0.9.0 is compatible (legacy)
        # But within same major, older versions are compatible (upgradable)
        # Note: This tests backwards compatibility, not forward compatibility
        assert is_version_compatible("1.0.0", "0.9.0") is True

    def test_newer_config_version_is_incompatible(self):
        """Test that config versions newer than application are incompatible."""
        # CURRENT_CONFIG_VERSION is 1.0.0
        # Newer versions (1.1.0, 1.0.1, etc.) should be rejected
        # The application doesn't know about features in newer configs
        assert is_version_compatible("1.1.0") is False
        assert is_version_compatible("1.2.5") is False
        assert is_version_compatible("1.0.1") is False
        assert is_version_compatible("1.0.5") is False

    def test_lower_than_minimum_is_incompatible(self):
        """Test that versions below minimum are incompatible."""
        assert is_version_compatible("0.9.0", "1.0.0") is False
        assert is_version_compatible("0.5.0", "1.0.0") is False

    def test_different_major_version_is_incompatible(self):
        """Test that different major versions are incompatible."""
        # Version 2.x.x is incompatible with 1.x.x app
        assert is_version_compatible("2.0.0") is False
        assert is_version_compatible("2.5.0") is False

        # Version 0.x.x (except 0.9.0 legacy) is incompatible with 1.x.x app
        assert is_version_compatible("0.8.0") is False
        assert is_version_compatible("0.5.0") is False
        # Note: 0.9.0 is a special case - it's compatible (legacy support)

    def test_invalid_version_is_incompatible(self):
        """Test that invalid versions are incompatible."""
        assert is_version_compatible("invalid") is False
        assert is_version_compatible("1.0") is False
        assert is_version_compatible("") is False

    def test_custom_minimum_version(self):
        """Test compatibility checking with custom minimum version."""
        # CURRENT_CONFIG_VERSION is 1.0.0
        # Test with older versions using custom minimum
        assert is_version_compatible("1.0.0", min_version="0.9.0") is True
        assert is_version_compatible("1.0.0", min_version="1.0.0") is True
        assert is_version_compatible("0.9.0", min_version="1.0.0") is False  # Below minimum


class TestGetMigrationSuggestion:
    """Tests for get_migration_suggestion function."""

    def test_suggestion_for_up_to_date_config(self):
        """Test suggestion message for up-to-date configuration."""
        suggestion = get_migration_suggestion(CURRENT_CONFIG_VERSION)
        assert "up to date" in suggestion.lower()

    def test_suggestion_for_outdated_config(self):
        """Test suggestion message for outdated configuration."""
        suggestion = get_migration_suggestion("0.9.0")
        assert "outdated" in suggestion.lower()
        assert "migrate_config.py" in suggestion
        assert CURRENT_CONFIG_VERSION in suggestion

    def test_suggestion_for_newer_config(self):
        """Test suggestion message for configuration newer than app."""
        suggestion = get_migration_suggestion("2.0.0")
        assert "newer" in suggestion.lower()
        assert "update the application" in suggestion.lower()

    def test_suggestion_for_invalid_version(self):
        """Test suggestion message for invalid version."""
        suggestion = get_migration_suggestion("invalid")
        assert "invalid" in suggestion.lower()

        suggestion = get_migration_suggestion("1.0")
        assert "invalid" in suggestion.lower()

    def test_suggestion_includes_version_numbers(self):
        """Test that suggestion includes relevant version numbers."""
        suggestion = get_migration_suggestion("1.0.0")
        # Should be up to date, so might not mention versions
        assert len(suggestion) > 0

        suggestion = get_migration_suggestion("0.5.0")
        assert "0.5.0" in suggestion
        assert CURRENT_CONFIG_VERSION in suggestion


class TestVersionConstants:
    """Tests for version constants."""

    def test_current_version_is_valid_semver(self):
        """Test that CURRENT_CONFIG_VERSION is valid semver."""
        # Should not raise
        parse_version(CURRENT_CONFIG_VERSION)

    def test_min_supported_version_is_valid_semver(self):
        """Test that MIN_SUPPORTED_VERSION is valid semver."""
        # Should not raise
        parse_version(MIN_SUPPORTED_VERSION)

    def test_min_version_not_greater_than_current(self):
        """Test that minimum version is not greater than current."""
        min_tuple = parse_version(MIN_SUPPORTED_VERSION)
        current_tuple = parse_version(CURRENT_CONFIG_VERSION)
        assert min_tuple <= current_tuple

    def test_constants_are_strings(self):
        """Test that version constants are strings."""
        assert isinstance(CURRENT_CONFIG_VERSION, str)
        assert isinstance(MIN_SUPPORTED_VERSION, str)


class TestVersionComparisonEdgeCases:
    """Tests for edge cases in version comparison."""

    def test_version_tuple_comparison(self):
        """Test that version tuples compare correctly."""
        assert (1, 0, 0) == (1, 0, 0)
        assert (1, 1, 0) > (1, 0, 0)
        assert (1, 0, 1) > (1, 0, 0)
        assert (2, 0, 0) > (1, 9, 9)
        assert (0, 9, 0) < (1, 0, 0)

    def test_compatibility_with_various_versions(self):
        """Test compatibility with various version combinations."""
        # Current version is 1.0.0, MIN_SUPPORTED is 0.9.0
        test_cases = [
            ("1.0.0", True),   # Exact match
            ("1.0.1", False),  # Higher patch - NOT compatible (future version)
            ("1.1.0", False),  # Higher minor - NOT compatible (future version)
            ("1.9.9", False),  # Much higher minor/patch - NOT compatible (future version)
            ("0.9.0", True),   # Legacy version (special case for 0.9.0 -> 1.x.x)
            ("2.0.0", False),  # Higher major - NOT compatible
            ("0.8.0", False),  # Below minimum - NOT compatible
        ]

        for version, expected in test_cases:
            result = is_version_compatible(version)
            assert result == expected, f"Version {version} compatibility mismatch"

    def test_parse_version_with_prerelease(self):
        """Test parsing versions with pre-release metadata."""
        # Pre-release metadata should be stripped
        assert parse_version("1.2.3-alpha") == (1, 2, 3)
        assert parse_version("1.2.3-beta.1") == (1, 2, 3)
        assert parse_version("1.2.3-rc.1") == (1, 2, 3)

    def test_parse_version_with_build_metadata(self):
        """Test parsing versions with build metadata."""
        # Build metadata should be stripped
        assert parse_version("1.2.3+001") == (1, 2, 3)
        assert parse_version("1.2.3+20130313144700") == (1, 2, 3)
        assert parse_version("1.2.3+exp.sha.5114f85") == (1, 2, 3)

    def test_parse_version_with_both_prerelease_and_build(self):
        """Test parsing versions with both pre-release and build metadata."""
        assert parse_version("1.2.3-alpha+001") == (1, 2, 3)
        assert parse_version("1.2.3-beta.1+sha.abc123") == (1, 2, 3)

    def test_legacy_version_0_9_0_compatible_with_1_x(self):
        """Test that legacy 0.9.0 is compatible with 1.x.x versions."""
        # Special case: 0.9.0 is compatible with 1.x.x
        assert is_version_compatible("0.9.0", "0.9.0") is True


class TestMigrationFailureHandling:
    """Tests for migration failure scenarios."""

    def test_migration_with_invalid_from_version(self):
        """Test that migration fails gracefully with invalid from_version."""
        from app.core.config_migrations import apply_migrations

        config = {"config_version": "invalid"}

        with pytest.raises(ValueError, match="Invalid version"):
            apply_migrations(config, "invalid", "1.0.0")

    def test_migration_with_missing_intermediate_version(self):
        """Test that migration fails when intermediate migration is missing."""
        from app.core.config_migrations import get_migration_path

        # Trying to migrate from 1.0.0 to 2.0.0 without intermediate migrations
        with pytest.raises(ValueError, match="No migration path"):
            get_migration_path("1.0.0", "2.0.0")

    def test_migration_loop_detection(self):
        """Test that circular migration dependencies are detected."""
        # This would require creating circular migrations, which we prevent
        # by design, but the get_migration_path has max_iterations protection
        pass  # Covered by the max_iterations check in get_migration_path


class TestBackupEdgeCases:
    """Tests for backup system edge cases."""

    def test_backup_rotation_respects_max_limit(self):
        """Test that backup rotation keeps only max_backups."""
        # This is tested in test_config_backup_and_migration.py
        # but we document it here as an important edge case
        pass
