"""
Root conftest.py - Loads test environment before any imports.

This file is at the backend root and is loaded before tests/conftest.py.
It ensures .env.test is loaded before the app modules are imported.
"""
import os
import sys
from pathlib import Path


# Load .env.test BEFORE any app imports
env_test_path = Path(__file__).parent / ".env.test"
if env_test_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_test_path, override=True)

# Set test environment flag
os.environ["TESTING"] = "1"


def pytest_configure(config):
    """
    Pytest configuration hook.

    This runs after environment is loaded but before tests start.
    We need to reload app modules to pick up the test environment.
    """
    import importlib

    # Reload app.core.config first (it has the Settings instance)
    if 'app.core.config' in sys.modules:
        import app.core.config
        importlib.reload(app.core.config)

    # Reload app.core.security (it depends on config)
    if 'app.core.security' in sys.modules:
        import app.core.security
        importlib.reload(app.core.security)

    # Reload app.main (it uses settings at module level)
    if 'app.main' in sys.modules:
        import app.main
        importlib.reload(app.main)

    print("\n✓ Reloaded app modules with test environment from .env.test")
