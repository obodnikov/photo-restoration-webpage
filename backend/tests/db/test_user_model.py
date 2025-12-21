"""
Tests for User model.

Tests user creation, relationships, and model methods.
"""
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.db.models import Session, User


@pytest.mark.asyncio
class TestUserModel:
    """Test User model functionality."""

    async def test_create_user(self, db_session: AsyncSession):
        """User can be created with all required fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Password123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "user"
        assert user.is_active is True  # Default
        assert user.password_must_change is False  # Default
        assert isinstance(user.created_at, datetime)
        assert user.last_login is None  # Not set yet

    async def test_create_admin_user(self, db_session: AsyncSession):
        """Admin user can be created."""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("AdminPass123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        assert admin.role == "admin"

    async def test_username_unique(self, db_session: AsyncSession):
        """Username must be unique."""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            full_name="User One",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create another user with same username
        user2 = User(
            username="testuser",
            email="test2@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("Pass456"),
            role="user",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_email_unique(self, db_session: AsyncSession):
        """Email must be unique."""
        user1 = User(
            username="user1",
            email="same@example.com",
            full_name="User One",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create another user with same email
        user2 = User(
            username="user2",
            email="same@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("Pass456"),
            role="user",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_password_hashing(self, db_session: AsyncSession):
        """Password is stored hashed and can be verified."""
        password = "MySecurePass123"
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash(password),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Password should be hashed (not plain text)
        assert user.hashed_password != password
        # But should verify correctly
        assert verify_password(password, user.hashed_password)

    async def test_user_to_dict(self, db_session: AsyncSession):
        """User.to_dict() returns correct dictionary."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        user_dict = user.to_dict()

        assert user_dict["id"] == user.id
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["full_name"] == "Test User"
        assert user_dict["role"] == "user"
        assert user_dict["is_active"] is True
        assert user_dict["password_must_change"] is False
        assert "created_at" in user_dict
        assert user_dict["last_login"] is None
        # Password should NOT be in dict
        assert "hashed_password" not in user_dict
        assert "password" not in user_dict

    async def test_user_sessions_relationship(self, db_session: AsyncSession):
        """User can have multiple sessions."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create sessions for the user
        session1 = Session(user_id=user.id, session_id="session-uuid-1")
        session2 = Session(user_id=user.id, session_id="session-uuid-2")
        db_session.add_all([session1, session2])
        await db_session.commit()

        # Refresh user to load relationship
        await db_session.refresh(user, attribute_names=["sessions"])

        assert len(user.sessions) == 2
        assert session1 in user.sessions
        assert session2 in user.sessions

    async def test_cascade_delete_user_deletes_sessions(self, db_session: AsyncSession):
        """Deleting a user deletes their sessions (CASCADE)."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create sessions
        session1 = Session(user_id=user.id, session_id="session-1")
        session2 = Session(user_id=user.id, session_id="session-2")
        db_session.add_all([session1, session2])
        await db_session.commit()

        # Delete user
        await db_session.delete(user)
        await db_session.commit()

        # Sessions should be deleted
        result = await db_session.execute(select(Session))
        sessions = result.scalars().all()
        assert len(sessions) == 0

    async def test_inactive_user(self, db_session: AsyncSession):
        """User can be marked as inactive."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_active is False

    async def test_password_must_change_flag(self, db_session: AsyncSession):
        """User can be flagged to change password on first login."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            password_must_change=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.password_must_change is True

    async def test_update_last_login(self, db_session: AsyncSession):
        """User last_login can be updated."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.last_login is None

        # Update last_login
        now = datetime.utcnow()
        user.last_login = now
        await db_session.commit()
        await db_session.refresh(user)

        assert user.last_login is not None
        # Should be close to now (within 1 second)
        assert abs((user.last_login - now).total_seconds()) < 1

    async def test_multiple_users(self, db_session: AsyncSession):
        """Multiple users can exist in database."""
        users = [
            User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                hashed_password=get_password_hash("Pass123"),
                role="user",
            )
            for i in range(5)
        ]
        db_session.add_all(users)
        await db_session.commit()

        result = await db_session.execute(select(User))
        all_users = result.scalars().all()
        assert len(all_users) == 5

    async def test_user_created_at_auto_set(self, db_session: AsyncSession):
        """User created_at is automatically set on creation."""
        before_create = datetime.utcnow()

        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        after_create = datetime.utcnow()

        assert user.created_at is not None
        assert before_create <= user.created_at <= after_create

    async def test_username_case_sensitivity(self, db_session: AsyncSession):
        """Usernames are case-sensitive at database level."""
        user1 = User(
            username="TestUser",
            email="test1@example.com",
            full_name="User One",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(user1)
        await db_session.commit()

        # SQLite is case-insensitive for strings by default,
        # but our code normalizes to lowercase
        user2 = User(
            username="testuser",  # lowercase version
            email="test2@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("Pass456"),
            role="user",
        )
        db_session.add(user2)

        # This should fail if normalization is working
        # (both become "testuser")
        with pytest.raises(Exception):
            await db_session.commit()


@pytest.mark.unit
class TestUserModelUnit:
    """Quick unit tests for User model."""

    @pytest.mark.asyncio
    async def test_user_creation_basic(self, db_session: AsyncSession):
        """Basic user creation works."""
        user = User(
            username="test",
            email="test@example.com",
            full_name="Test",
            hashed_password="hashed",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
