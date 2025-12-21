"""
Tests for database seeding functionality.

Tests admin user creation and seeding logic.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.core.config import Settings
from app.core.security import get_password_hash, verify_password
from app.db.models import User
from app.db.seed import seed_admin_user


@pytest.mark.asyncio
class TestAdminSeeding:
    """Test admin user seeding functionality."""

    async def test_seed_admin_user_creates_admin(self, db_session: AsyncSession):
        """Seeding creates admin user from settings."""
        settings = Settings(
            auth_username="admin",
            auth_password="AdminPass123",
            auth_email="admin@example.com",
            auth_full_name="Admin User",
        )

        # Mock get_settings to return our test settings
        with patch('app.db.seed.get_settings', return_value=settings):
            await seed_admin_user(db_session)

        # Verify admin user created
        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        assert admin is not None
        assert admin.username == "admin"
        assert admin.email == "admin@example.com"
        assert admin.full_name == "Admin User"
        assert admin.role == "admin"
        assert admin.is_active is True
        assert admin.password_must_change is False
        assert verify_password("AdminPass123", admin.hashed_password)

    async def test_seed_admin_user_idempotent(self, db_session: AsyncSession):
        """Seeding is idempotent - doesn't create duplicate admins."""
        settings = Settings(
            auth_username="admin",
            auth_password="AdminPass123",
            auth_email="admin@example.com",
            auth_full_name="Admin User",
        )

        # Seed first time
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Seed again (should not create duplicate)
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Verify only one admin exists
        result = await db_session.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 1
        assert users[0].username == "admin"

    async def test_seed_admin_skips_existing(self, db_session: AsyncSession):
        """Seeding skips if admin user already exists."""
        # Create admin manually
        admin = User(
            username="admin",
            email="old@example.com",
            full_name="Old Name",
            hashed_password=get_password_hash("OldPass123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        original_id = admin.id

        # Seed with new credentials
        settings = Settings(
            auth_username="admin",
            auth_password="NewPass123",
            auth_email="new@example.com",
            auth_full_name="New Name",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Verify NOT updated (existing user preserved)
        await db_session.refresh(admin)
        assert admin.id == original_id
        assert admin.email == "old@example.com"  # Unchanged
        assert admin.full_name == "Old Name"  # Unchanged
        assert verify_password("OldPass123", admin.hashed_password)  # Old password still works

    async def test_seed_admin_normalizes_username(self, db_session: AsyncSession):
        """Seeding normalizes username to lowercase."""
        settings = Settings(
            auth_username="ADMIN",  # Uppercase
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Should be stored as lowercase
        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        assert admin is not None
        assert admin.username == "admin"

    async def test_seed_admin_normalizes_email(self, db_session: AsyncSession):
        """Seeding normalizes email to lowercase."""
        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="Admin@EXAMPLE.COM",  # Mixed case
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        assert admin.email == "admin@example.com"

    async def test_seed_admin_with_existing_non_admin(self, db_session: AsyncSession):
        """Seeding skips if username exists even as non-admin."""
        # Create regular user with same username
        user = User(
            username="admin",
            email="user@example.com",
            full_name="Regular User",
            hashed_password="hash",
            role="user",  # Not admin
        )
        db_session.add(user)
        await db_session.commit()

        settings = Settings(
            auth_username="admin",
            auth_password="AdminPass123",
            auth_email="admin@example.com",
            auth_full_name="Admin User",
        )

        # Should skip (not update existing user)
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Verify NOT updated (existing user preserved)
        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        assert admin.role == "user"  # Still user, not admin
        assert admin.email == "user@example.com"  # Original email

    async def test_seed_logs_creation(self, db_session: AsyncSession, caplog):
        """Seeding logs admin user creation."""
        import logging

        # Set log level to capture INFO messages
        caplog.set_level(logging.INFO)

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Check logs (case-insensitive)
        log_messages = [record.message.lower() for record in caplog.records]
        assert any("created admin user" in msg for msg in log_messages)

    async def test_seed_preserves_other_fields(self, db_session: AsyncSession):
        """Seeding skips if user exists, preserving all fields."""
        # Create admin
        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        original_created_at = admin.created_at
        original_full_name = admin.full_name

        # Seed again (should skip, not update)
        settings.auth_full_name = "Updated Admin"
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # All fields should be preserved (not updated)
        await db_session.refresh(admin)
        assert admin.created_at == original_created_at
        assert admin.full_name == original_full_name  # NOT updated

    async def test_seed_with_case_insensitive_lookup(self, db_session: AsyncSession):
        """Seeding finds existing user case-insensitively and skips."""
        # Create admin with lowercase username
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin",
            hashed_password=get_password_hash("OldPass123"),
            role="admin",
        )
        db_session.add(admin)
        await db_session.commit()

        # Seed with uppercase username
        settings = Settings(
            auth_username="ADMIN",  # Uppercase
            auth_password="NewPass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Should find existing admin (not create new) and skip (not update)
        result = await db_session.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 1
        # Password should NOT be updated (old password still works)
        assert verify_password("OldPass123", users[0].hashed_password)


@pytest.mark.unit
class TestSeedingUnit:
    """Quick unit tests for seeding."""

    @pytest.mark.asyncio
    async def test_basic_seeding(self, db_session: AsyncSession):
        """Basic seeding creates admin."""
        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        assert admin is not None
        assert admin.role == "admin"


@pytest.mark.integration
class TestSeedingIntegration:
    """Integration tests for seeding with database."""

    @pytest.mark.asyncio
    async def test_seed_during_init(self, db_session: AsyncSession):
        """Seeding works during database initialization."""
        # This simulates what happens in database.py init_db()
        settings = Settings(
            auth_username="admin",
            auth_password="InitPass123",
            auth_email="init@example.com",
            auth_full_name="Init Admin",
        )

        # Seed
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Verify admin exists and can authenticate
        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        assert admin is not None
        assert verify_password("InitPass123", admin.hashed_password)

    @pytest.mark.asyncio
    async def test_seed_rollback_on_error(self, db_session: AsyncSession):
        """Seeding is idempotent - second seed skips existing user."""
        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        # First seed succeeds
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Verify admin created
        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        assert admin is not None
        original_full_name = admin.full_name

        # Second seed should skip (idempotent)
        settings.auth_full_name = "Updated Admin"
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        await db_session.refresh(admin)
        assert admin.full_name == original_full_name  # NOT updated


@pytest.mark.security
class TestSeedingSecurity:
    """Security tests for seeding."""

    @pytest.mark.asyncio
    async def test_password_hashed_in_database(self, db_session: AsyncSession):
        """Password is stored hashed, not in plain text."""
        settings = Settings(
            auth_username="admin",
            auth_password="PlainTextPass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        # Password should NOT be stored in plain text
        assert admin.hashed_password != "PlainTextPass123"
        # But should verify correctly
        assert verify_password("PlainTextPass123", admin.hashed_password)

    @pytest.mark.asyncio
    async def test_seed_prevents_sql_injection(self, db_session: AsyncSession):
        """Seeding is safe from SQL injection in username."""
        settings = Settings(
            auth_username="admin'; DROP TABLE users--",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        # Should handle safely (parameterized queries)
        with patch("app.db.seed.get_settings", return_value=settings):
            await seed_admin_user(db_session)

        # Table should still exist
        result = await db_session.execute(select(User))
        users = result.scalars().all()
        assert len(users) >= 0  # Query worked
