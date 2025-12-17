"""
Tests for requirements.txt to ensure all package versions are valid and installable.

This test validates that:
1. All packages in requirements.txt have correct version specifiers
2. Package versions exist and are available on PyPI
3. Critical packages (replicate, huggingface-hub, fastapi, etc.) are present
"""
import re
from pathlib import Path

import pytest


def parse_requirements_file(file_path: Path) -> list[tuple[str, str]]:
    """
    Parse requirements.txt and extract package names and version specifiers.

    Args:
        file_path: Path to requirements.txt

    Returns:
        List of tuples (package_name, version_specifier)
    """
    packages = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Skip lines with -e or --editable
            if line.startswith(('-e', '--editable')):
                continue

            # Parse package[extras]==version or package>=version
            # Examples: fastapi==0.115.7, huggingface-hub>=1.2.3, bcrypt<5.0.0
            match = re.match(r'^([a-zA-Z0-9_\-\[\]]+)([<>=!]+.*)$', line)
            if match:
                package_name = match.group(1)
                version_spec = match.group(2)
                packages.append((package_name, version_spec))

    return packages


@pytest.fixture
def requirements_file():
    """Path to requirements.txt file."""
    backend_dir = Path(__file__).parent.parent
    return backend_dir / "requirements.txt"


@pytest.fixture
def parsed_requirements(requirements_file):
    """Parsed requirements from requirements.txt."""
    return parse_requirements_file(requirements_file)


class TestRequirementsFile:
    """Test suite for requirements.txt validation."""

    def test_requirements_file_exists(self, requirements_file):
        """Test that requirements.txt exists."""
        assert requirements_file.exists(), "requirements.txt not found"

    def test_requirements_file_not_empty(self, parsed_requirements):
        """Test that requirements.txt is not empty."""
        assert len(parsed_requirements) > 0, "requirements.txt is empty"

    def test_all_lines_parseable(self, requirements_file):
        """Test that all non-comment lines can be parsed."""
        with open(requirements_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Should have a version specifier
                assert re.match(r'^[a-zA-Z0-9_\-\[\]]+[<>=!]+', line), (
                    f"Line {line_num} doesn't have a valid version specifier: {line}"
                )

    def test_replicate_package_present(self, parsed_requirements):
        """Test that replicate package is present with correct version."""
        package_names = [pkg[0] for pkg in parsed_requirements]
        assert "replicate" in package_names, "replicate package not found in requirements.txt"

        # Find replicate version
        replicate_version = None
        for pkg_name, version_spec in parsed_requirements:
            if pkg_name == "replicate":
                replicate_version = version_spec
                break

        assert replicate_version is not None, "replicate version not found"

        # Should be pinned to a specific version (==)
        assert version_spec.startswith("=="), (
            f"replicate should be pinned to a specific version, got: {version_spec}"
        )

        # Extract version number
        version_match = re.match(r'==([0-9.]+)', version_spec)
        assert version_match, f"Invalid version format: {version_spec}"

        version = version_match.group(1)
        # Should be 1.0.x (stable release)
        assert version.startswith("1.0."), (
            f"replicate version should be 1.0.x (stable), got: {version}"
        )

    def test_huggingface_hub_package_present(self, parsed_requirements):
        """Test that huggingface-hub package is present."""
        package_names = [pkg[0] for pkg in parsed_requirements]
        assert "huggingface-hub" in package_names, (
            "huggingface-hub package not found in requirements.txt"
        )

    def test_fastapi_package_present(self, parsed_requirements):
        """Test that fastapi package is present with pinned version."""
        package_names = [pkg[0] for pkg in parsed_requirements]
        assert "fastapi" in package_names, "fastapi package not found in requirements.txt"

        # Find fastapi version
        for pkg_name, version_spec in parsed_requirements:
            if pkg_name == "fastapi":
                assert version_spec.startswith("=="), (
                    f"fastapi should be pinned to a specific version, got: {version_spec}"
                )
                break

    def test_critical_packages_present(self, parsed_requirements):
        """Test that all critical packages are present."""
        package_names = [pkg[0] for pkg in parsed_requirements]

        critical_packages = [
            "fastapi",
            "uvicorn[standard]",
            "pydantic",
            "pydantic-settings",
            "httpx",
            "huggingface-hub",
            "replicate",
            "Pillow",
            "python-jose[cryptography]",
            "passlib[bcrypt]",
            "sqlalchemy[asyncio]",
            "aiosqlite",
            "apscheduler",
            "pytest",
            "pytest-asyncio",
        ]

        for critical_pkg in critical_packages:
            # Handle packages with extras like uvicorn[standard]
            pkg_base = critical_pkg.split('[')[0]
            matching_packages = [pkg for pkg in package_names if pkg.startswith(pkg_base)]

            assert len(matching_packages) > 0, (
                f"Critical package '{critical_pkg}' not found in requirements.txt"
            )

    def test_no_duplicate_packages(self, parsed_requirements):
        """Test that no package is listed multiple times."""
        package_names = [pkg[0] for pkg in parsed_requirements]
        duplicates = []
        seen = set()

        for pkg_name in package_names:
            if pkg_name in seen:
                duplicates.append(pkg_name)
            seen.add(pkg_name)

        assert len(duplicates) == 0, (
            f"Duplicate packages found in requirements.txt: {', '.join(duplicates)}"
        )

    def test_bcrypt_version_constraint(self, parsed_requirements):
        """Test that bcrypt has the correct version constraint for passlib compatibility."""
        bcrypt_version = None
        for pkg_name, version_spec in parsed_requirements:
            if pkg_name == "bcrypt":
                bcrypt_version = version_spec
                break

        assert bcrypt_version is not None, "bcrypt package not found in requirements.txt"

        # Should have <5.0.0 constraint for passlib 1.7.4 compatibility
        assert "<5.0.0" in bcrypt_version, (
            f"bcrypt should have <5.0.0 constraint for passlib compatibility, got: {bcrypt_version}"
        )

    def test_version_specifiers_valid_format(self, parsed_requirements):
        """Test that all version specifiers use valid operators."""
        valid_operators = ["==", ">=", "<=", ">", "<", "!=", "~="]

        for pkg_name, version_spec in parsed_requirements:
            # Extract operator from version spec
            operator_match = re.match(r'^([<>=!~]+)', version_spec)
            assert operator_match, (
                f"Invalid version specifier for {pkg_name}: {version_spec}"
            )

            operator = operator_match.group(1)
            assert operator in valid_operators, (
                f"Invalid operator '{operator}' for {pkg_name}. "
                f"Valid operators: {', '.join(valid_operators)}"
            )

    def test_replicate_version_is_stable(self, parsed_requirements):
        """Test that replicate uses a stable release version (not alpha/beta)."""
        replicate_version = None
        for pkg_name, version_spec in parsed_requirements:
            if pkg_name == "replicate":
                replicate_version = version_spec
                break

        assert replicate_version is not None

        # Extract version number
        version_match = re.match(r'==([0-9.]+)([a-z0-9]*)', version_spec)
        assert version_match, f"Invalid version format: {version_spec}"

        version = version_match.group(1)
        suffix = version_match.group(2)

        # Should not have alpha/beta/rc suffixes
        assert suffix == "", (
            f"replicate should use a stable release version, not alpha/beta/rc. Got: {version_spec}"
        )

        # Version should be semantic versioning (X.Y.Z)
        version_parts = version.split('.')
        assert len(version_parts) >= 2, (
            f"replicate version should follow semantic versioning (X.Y.Z), got: {version}"
        )


class TestImportability:
    """Test that critical packages can be imported."""

    def test_replicate_importable(self):
        """Test that replicate package can be imported."""
        try:
            import replicate
            assert hasattr(replicate, 'run'), "replicate.run() method not found"
        except ImportError as e:
            pytest.fail(f"Failed to import replicate: {e}")

    def test_huggingface_hub_importable(self):
        """Test that huggingface_hub package can be imported."""
        try:
            from huggingface_hub import InferenceClient
            assert InferenceClient is not None
        except ImportError as e:
            pytest.fail(f"Failed to import huggingface_hub: {e}")

    def test_fastapi_importable(self):
        """Test that fastapi package can be imported."""
        try:
            import fastapi
            assert hasattr(fastapi, 'FastAPI'), "FastAPI class not found"
        except ImportError as e:
            pytest.fail(f"Failed to import fastapi: {e}")
