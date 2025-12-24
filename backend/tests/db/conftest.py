"""Shared fixtures for database tests."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.models import User


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Provide a test user for database tests.

    This user can be used as foreign key for session and other models.
    """
    user = User(
        username="test_db_user",
        email="testdb@example.com",
        full_name="Test DB User",
        hashed_password=get_password_hash("testpassword123"),
        role="user",
        is_active=True,
        password_must_change=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user
