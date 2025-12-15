"""
Pytest configuration and shared fixtures.

This module provides fixtures that can be used across all test files.
"""
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

# Environment loading is now handled in backend/conftest.py (root level)
# which is loaded before this file via pytest_configure hook
# App modules are reloaded in pytest_configure to pick up test environment

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, get_password_hash
from app.db.models import Base


def _get_app():
    """Get the FastAPI app after it's been reloaded with test config."""
    from app.main import app
    return app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Provide test settings.

    This fixture returns the settings instance that was initialized
    with the .env.test file loaded at module import time.
    """
    return get_settings()


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """
    Provide a synchronous test client for the FastAPI app.

    Use this for testing endpoints that don't require async operations.
    Gets the app fresh to ensure test config is used.
    """
    app = _get_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async test client for the FastAPI app.

    Use this for testing async endpoints and operations.
    Gets the app fresh to ensure test config is used.
    """
    app = _get_app()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def test_user_credentials() -> dict:
    """
    Provide test user credentials.

    Returns a dict with username and password for testing auth.
    """
    return {
        "username": "testuser",
        "password": "testpass"
    }


@pytest.fixture
def test_user_hashed_password() -> str:
    """
    Provide hashed password for test user.

    This is useful for testing password verification.
    Note: We hash the short test password directly, not the env var.
    """
    return get_password_hash("testpass")


@pytest.fixture
def valid_token(test_user_credentials: dict) -> str:
    """
    Provide a valid JWT token for testing protected endpoints.

    Returns a token with the test username that doesn't expire soon.
    """
    return create_access_token(
        data={"sub": test_user_credentials["username"]}
    )


@pytest.fixture
def expired_token() -> str:
    """
    Provide an expired JWT token for testing token expiration.

    Returns a token that has already expired.
    """
    from datetime import timedelta
    return create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(seconds=-1)  # Negative means already expired
    )


@pytest.fixture
def auth_headers(valid_token: str) -> dict:
    """
    Provide HTTP headers with valid authentication token.

    Use this to make authenticated requests in tests.
    """
    return {
        "Authorization": f"Bearer {valid_token}"
    }


@pytest.fixture(autouse=True)
def cleanup_test_directories(test_settings: Settings):
    """
    Automatically clean up test directories before and after each test.

    This fixture runs automatically for every test (autouse=True).
    """
    # Setup: Clean before test
    for directory in [test_settings.upload_dir, test_settings.processed_dir]:
        if directory.exists():
            import shutil
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)

    yield

    # Teardown: Clean after test
    for directory in [test_settings.upload_dir, test_settings.processed_dir]:
        if directory.exists():
            import shutil
            shutil.rmtree(directory)


@pytest.fixture
def mock_hf_api_response() -> bytes:
    """
    Provide mock HuggingFace API response (image bytes).

    Returns a simple 1x1 PNG image for testing.
    """
    # Simple 1x1 transparent PNG (base64 decoded)
    import base64
    png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    return base64.b64decode(png_data)


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Provide a test database engine with in-memory SQLite.

    Creates a new in-memory database for each test.
    """
    from sqlalchemy import text

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables and enable foreign keys
    async with engine.begin() as conn:
        # Enable foreign keys for testing cascade deletes
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a test database session.

    Each test gets a fresh session with all tables created.
    Changes are rolled back after each test.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any changes


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, may use database/external services)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (may take several seconds)"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication and authorization tests"
    )
