"""
Load test environment before any app imports.
This file is automatically discovered by pytest.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.test file
env_test_path = Path(__file__).parent / ".env.test"
if env_test_path.exists():
    load_dotenv(env_test_path, override=True)
    print(f"✓ Loaded test environment from {env_test_path}")

# Set test environment flag
os.environ["TESTING"] = "1"
