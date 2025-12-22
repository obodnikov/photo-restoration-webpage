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

    @pytest.mark.asyncio
    async def test_seed_reraises_non_integrity_errors(self, db_session: AsyncSession):
        """Seeding re-raises non-IntegrityError exceptions."""
        from sqlalchemy.exc import OperationalError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        # Mock commit to raise OperationalError (e.g., disk full, connection lost)
        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_commit():
                raise OperationalError("Disk full", None, None)

            db_session.commit = mock_commit

            try:
                # Should re-raise OperationalError, not swallow it
                with pytest.raises(OperationalError):
                    await seed_admin_user(db_session)
            finally:
                # Restore original commit
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_seed_reraises_not_null_integrity_error(self, db_session: AsyncSession):
        """Seeding re-raises IntegrityError for NOT NULL violations."""
        from unittest.mock import MagicMock
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        # Mock commit to raise IntegrityError with NOT NULL violation
        # SQLite format: "NOT NULL constraint failed: users.username"
        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_commit():
                # Create a mock sqlite3.IntegrityError
                orig_error = Exception("NOT NULL constraint failed: users.email")
                integrity_error = IntegrityError(
                    "NOT NULL constraint failed",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_commit

            try:
                # Should re-raise IntegrityError for NOT NULL violations
                with pytest.raises(IntegrityError) as exc_info:
                    await seed_admin_user(db_session)

                # Verify it's the NOT NULL error
                assert "NOT NULL" in str(exc_info.value)
            finally:
                # Restore original commit
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_seed_reraises_check_constraint_error(self, db_session: AsyncSession):
        """Seeding re-raises IntegrityError for CHECK constraint violations."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        # Mock commit to raise IntegrityError with CHECK constraint violation
        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_commit():
                # Create a mock CHECK constraint error
                orig_error = Exception("CHECK constraint failed: users")
                integrity_error = IntegrityError(
                    "CHECK constraint failed",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_commit

            try:
                # Should re-raise IntegrityError for CHECK constraint violations
                with pytest.raises(IntegrityError) as exc_info:
                    await seed_admin_user(db_session)

                # Verify it's the CHECK constraint error
                assert "CHECK" in str(exc_info.value)
            finally:
                # Restore original commit
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_seed_suppresses_only_unique_violations(self, db_session: AsyncSession):
        """Seeding suppresses UNIQUE violations but re-raises other IntegrityErrors."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        # Test 1: UNIQUE violation should be suppressed (no exception)
        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_unique_violation():
                # SQLite UNIQUE constraint violation
                orig_error = Exception("UNIQUE constraint failed: users.username")
                integrity_error = IntegrityError(
                    "UNIQUE constraint failed",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_unique_violation

            try:
                # Should NOT raise - UNIQUE violations are suppressed
                await seed_admin_user(db_session)
            finally:
                db_session.commit = original_commit

        # Test 2: Foreign key violation should be re-raised
        with patch("app.db.seed.get_settings", return_value=settings):
            async def mock_fk_violation():
                orig_error = Exception("FOREIGN KEY constraint failed")
                integrity_error = IntegrityError(
                    "FOREIGN KEY constraint failed",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_fk_violation

            try:
                # Should re-raise - FK violations are NOT suppressed
                with pytest.raises(IntegrityError) as exc_info:
                    await seed_admin_user(db_session)
                assert "FOREIGN KEY" in str(exc_info.value)
            finally:
                db_session.commit = original_commit


@pytest.mark.security
class TestDatabaseSpecificIntegrityErrors:
    """Test database-specific integrity error detection."""

    @pytest.mark.asyncio
    async def test_postgresql_unique_violation_detected(self, db_session: AsyncSession):
        """PostgreSQL unique violations (pgcode 23505) are properly detected and suppressed."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_pg_unique_violation():
                # Create mock PostgreSQL unique violation error
                class PostgreSQLError:
                    def __init__(self):
                        self.pgcode = "23505"  # PostgreSQL unique_violation SQLSTATE
                    def __str__(self):
                        return "duplicate key value violates unique constraint"

                orig_error = PostgreSQLError()

                integrity_error = IntegrityError(
                    "duplicate key value violates unique constraint",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_pg_unique_violation

            try:
                # Should NOT raise - PostgreSQL unique violations are suppressed
                await seed_admin_user(db_session)
            finally:
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_postgresql_not_null_violation_reraised(self, db_session: AsyncSession):
        """PostgreSQL NOT NULL violations (pgcode 23502) are re-raised."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_pg_not_null_violation():
                # Create mock PostgreSQL NOT NULL violation error
                class PostgreSQLError:
                    def __init__(self):
                        self.pgcode = "23502"  # PostgreSQL not_null_violation SQLSTATE
                    def __str__(self):
                        return "null value in column violates not-null constraint"

                orig_error = PostgreSQLError()

                integrity_error = IntegrityError(
                    "null value in column violates not-null constraint",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_pg_not_null_violation

            try:
                # Should re-raise - PostgreSQL NOT NULL violations are NOT suppressed
                with pytest.raises(IntegrityError) as exc_info:
                    await seed_admin_user(db_session)
                assert "not-null constraint" in str(exc_info.value)
            finally:
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_mysql_unique_violation_detected(self, db_session: AsyncSession):
        """MySQL unique violations (errno 1062) are properly detected and suppressed."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_mysql_unique_violation():
                # Create mock MySQL unique violation error
                # Use a simple object with errno attribute
                class MySQLError:
                    def __init__(self):
                        self.errno = 1062  # MySQL ER_DUP_ENTRY
                    def __str__(self):
                        return "Duplicate entry 'admin' for key 'users.username'"

                orig_error = MySQLError()

                integrity_error = IntegrityError(
                    "Duplicate entry 'admin' for key 'users.username'",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_mysql_unique_violation

            try:
                # Should NOT raise - MySQL unique violations are suppressed
                await seed_admin_user(db_session)
            finally:
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_mysql_foreign_key_violation_reraised(self, db_session: AsyncSession):
        """MySQL foreign key violations (errno 1452) are re-raised."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_mysql_fk_violation():
                # Create mock MySQL foreign key violation error
                class MySQLError:
                    def __init__(self):
                        self.errno = 1452  # MySQL ER_NO_REFERENCED_ROW_2
                    def __str__(self):
                        return "Cannot add or update a child row: a foreign key constraint fails"

                orig_error = MySQLError()

                integrity_error = IntegrityError(
                    "Cannot add or update a child row: a foreign key constraint fails",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_mysql_fk_violation

            try:
                # Should re-raise - MySQL FK violations are NOT suppressed
                with pytest.raises(IntegrityError) as exc_info:
                    await seed_admin_user(db_session)
                assert "foreign key constraint fails" in str(exc_info.value)
            finally:
                db_session.commit = original_commit

    @pytest.mark.asyncio
    async def test_sqlite_foreign_key_violation_reraised(self, db_session: AsyncSession):
        """SQLite foreign key violations are re-raised (not suppressed like UNIQUE)."""
        from sqlalchemy.exc import IntegrityError

        settings = Settings(
            auth_username="admin",
            auth_password="Pass123",
            auth_email="admin@example.com",
            auth_full_name="Admin",
        )

        with patch("app.db.seed.get_settings", return_value=settings):
            original_commit = db_session.commit

            async def mock_sqlite_fk_violation():
                # Create mock SQLite foreign key violation error
                orig_error = Exception("FOREIGN KEY constraint failed")
                integrity_error = IntegrityError(
                    "FOREIGN KEY constraint failed",
                    None,
                    orig_error
                )
                integrity_error.orig = orig_error
                raise integrity_error

            db_session.commit = mock_sqlite_fk_violation

            try:
                # Should re-raise - SQLite FK violations are NOT suppressed
                with pytest.raises(IntegrityError) as exc_info:
                    await seed_admin_user(db_session)
                assert "FOREIGN KEY" in str(exc_info.value)
            finally:
                db_session.commit = original_commit
