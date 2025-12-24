"""Tests for database migration tracking system."""
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.database import is_db_initialized, record_migration, init_db
from app.db.models import Base, SchemaMigration, User


class TestSchemaMigrationModel:
    """Tests for SchemaMigration model."""

    @pytest.mark.asyncio
    async def test_create_migration_record(self, db_session: AsyncSession):
        """Test creating a migration record."""
        migration = SchemaMigration(
            version="001_test",
            description="Test migration"
        )
        db_session.add(migration)
        await db_session.commit()
        await db_session.refresh(migration)

        assert migration.id is not None
        assert migration.version == "001_test"
        assert migration.description == "Test migration"
        assert migration.applied_at is not None

    @pytest.mark.asyncio
    async def test_migration_version_is_unique(self, db_session: AsyncSession):
        """Test that migration version must be unique."""
        from sqlalchemy.exc import IntegrityError

        # Create first migration
        migration1 = SchemaMigration(
            version="001_test",
            description="First migration"
        )
        db_session.add(migration1)
        await db_session.commit()

        # Try to create duplicate
        migration2 = SchemaMigration(
            version="001_test",
            description="Duplicate migration"
        )
        db_session.add(migration2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_migration_to_dict(self, db_session: AsyncSession):
        """Test converting migration to dictionary."""
        migration = SchemaMigration(
            version="001_test",
            description="Test migration"
        )
        db_session.add(migration)
        await db_session.commit()
        await db_session.refresh(migration)

        migration_dict = migration.to_dict()

        assert migration_dict["id"] == migration.id
        assert migration_dict["version"] == "001_test"
        assert migration_dict["description"] == "Test migration"
        assert "applied_at" in migration_dict


class TestIsDbInitialized:
    """Tests for is_db_initialized function."""

    @pytest.mark.asyncio
    async def test_returns_false_for_empty_database(self, test_engine: AsyncEngine):
        """Test that returns False for database without schema."""
        # Don't create any tables
        result = await is_db_initialized(test_engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_migration_table(self, test_engine: AsyncEngine):
        """Test that returns False when schema_migrations table doesn't exist."""
        # Create tables but not schema_migrations
        async with test_engine.begin() as conn:
            # Only create users table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                )
            """))

        result = await is_db_initialized(test_engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_initial_migration(self, test_engine: AsyncEngine):
        """Test that returns False when initial migration not recorded."""
        # Create all tables including schema_migrations
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # But don't record the initial migration
        result = await is_db_initialized(test_engine)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_initialized(self, test_engine: AsyncEngine):
        """Test that returns True when database is properly initialized."""
        # Create all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Record initial migration
        from sqlalchemy.ext.asyncio import async_sessionmaker
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        async with factory() as session:
            migration = SchemaMigration(
                version="001_initial_schema",
                description="Initial schema"
            )
            session.add(migration)
            await session.commit()

        result = await is_db_initialized(test_engine)
        assert result is True


class TestRecordMigration:
    """Tests for record_migration function."""

    @pytest.mark.asyncio
    async def test_records_new_migration(self, db_session: AsyncSession):
        """Test recording a new migration."""
        await record_migration(db_session, "001_test", "Test migration")

        # Verify migration was recorded
        result = await db_session.execute(
            select(SchemaMigration).where(SchemaMigration.version == "001_test")
        )
        migration = result.scalar_one_or_none()

        assert migration is not None
        assert migration.version == "001_test"
        assert migration.description == "Test migration"

    @pytest.mark.asyncio
    async def test_skips_existing_migration(self, db_session: AsyncSession):
        """Test that existing migration is not duplicated."""
        # Record first time
        await record_migration(db_session, "001_test", "First description")

        # Try to record again with different description
        await record_migration(db_session, "001_test", "Second description")

        # Verify only one migration exists with original description
        result = await db_session.execute(
            select(SchemaMigration).where(SchemaMigration.version == "001_test")
        )
        migrations = result.scalars().all()

        assert len(migrations) == 1
        assert migrations[0].description == "First description"

    @pytest.mark.asyncio
    async def test_handles_race_condition(self, db_session: AsyncSession, test_engine: AsyncEngine):
        """Test that race condition in migration recording is handled."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        # Create two separate sessions to simulate concurrent access
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        # Both sessions try to record the same migration
        # This should not raise an error

        async with factory() as session1:
            migration1 = SchemaMigration(
                version="001_race_test",
                description="Migration 1"
            )
            session1.add(migration1)
            await session1.commit()

        # Second session tries to record same migration
        async with factory() as session2:
            # This should not fail due to race condition handling
            await record_migration(session2, "001_race_test", "Migration 2")

        # Verify only one migration exists
        result = await db_session.execute(
            select(SchemaMigration).where(SchemaMigration.version == "001_race_test")
        )
        migrations = result.scalars().all()
        assert len(migrations) == 1


class TestInitDbWithMigrations:
    """Tests for init_db with migration tracking."""

    @pytest.mark.asyncio
    async def test_init_db_creates_migration_table(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db creates schema_migrations table."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        await init_db()

        # Verify schema_migrations table exists
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            )
            tables = [row[0] for row in result]
            assert "schema_migrations" in tables

    @pytest.mark.asyncio
    async def test_init_db_records_initial_migration(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db records the initial migration."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        await init_db()

        # Verify initial migration was recorded
        from sqlalchemy.ext.asyncio import async_sessionmaker
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        async with factory() as session:
            result = await session.execute(
                select(SchemaMigration).where(
                    SchemaMigration.version == "001_initial_schema"
                )
            )
            migration = result.scalar_one_or_none()

            assert migration is not None
            assert migration.description == "Initial database schema with users, sessions, and processed_images tables"

    @pytest.mark.asyncio
    async def test_init_db_is_idempotent(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db can be called multiple times safely."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # First initialization
        await init_db()

        # Reset module globals to simulate restart
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Second initialization should not fail
        await init_db()

        # Verify only one migration record exists
        from sqlalchemy.ext.asyncio import async_sessionmaker
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        async with factory() as session:
            result = await session.execute(select(SchemaMigration))
            migrations = result.scalars().all()

            # Should still have only one migration record
            assert len(migrations) == 1

    @pytest.mark.asyncio
    async def test_init_db_skips_seeding_on_second_run(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db doesn't re-seed on subsequent runs."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Mock seed_database to track calls
        seed_calls = []

        async def mock_seed_database(session):
            seed_calls.append(1)

        monkeypatch.setattr("app.db.seed.seed_database", mock_seed_database)

        # First initialization - should call seed
        await init_db()
        assert len(seed_calls) == 1

        # Reset module globals to simulate restart
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Second initialization - should NOT call seed
        await init_db()
        assert len(seed_calls) == 1  # Still only 1 call

    @pytest.mark.asyncio
    async def test_init_db_preserves_existing_data(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db preserves existing data on restart."""
        import app.db.database
        from sqlalchemy.ext.asyncio import async_sessionmaker

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # First initialization
        await init_db()

        # Count users after first init (should have admin user)
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(select(User))
            initial_users = result.scalars().all()
            initial_count = len(initial_users)

            # Verify admin user was created (from env config)
            admin_user = next((u for u in initial_users if u.role == "admin"), None)
            assert admin_user is not None
            admin_username = admin_user.username
            admin_email = admin_user.email

        # Add an additional test user (different from admin)
        async with factory() as session:
            from app.core.security import get_password_hash
            user = User(
                username="regularuser",
                email="regular@example.com",
                full_name="Regular User",
                hashed_password=get_password_hash("password123"),
                role="user",
                is_active=True
            )
            session.add(user)
            await session.commit()

        # Reset module globals to simulate restart
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Second initialization
        await init_db()

        # Verify both users still exist
        async with factory() as session:
            result = await session.execute(select(User))
            all_users = result.scalars().all()

            # Should still have the same number of users (admin + regular)
            assert len(all_users) == initial_count + 1

            # Verify admin user still exists with same data
            admin = next((u for u in all_users if u.role == "admin"), None)
            assert admin is not None
            assert admin.username == admin_username
            assert admin.email == admin_email

            # Verify regular user still exists
            regular = next((u for u in all_users if u.username == "regularuser"), None)
            assert regular is not None
            assert regular.email == "regular@example.com"
            assert regular.full_name == "Regular User"
