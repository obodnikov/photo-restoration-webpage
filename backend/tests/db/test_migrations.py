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
    async def test_init_db_runs_self_healing_seeding_on_restart(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db runs seeding on every restart for self-healing."""
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

        # Second initialization - SHOULD call seed again for self-healing
        await init_db()
        assert len(seed_calls) == 2  # Called twice: initial + self-healing

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

    @pytest.mark.asyncio
    async def test_init_db_allows_new_tables_after_initialization(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db allows new tables to be added after initial migration.

        Regression test for: create_all() must always run to allow new TABLES to be created.
        CRITICAL: create_all() does NOT add new columns to existing tables - use Alembic for that.
        """
        import app.db.database
        from sqlalchemy import Column, Integer, String, Table

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # First initialization
        await init_db()

        # Verify initial tables exist
        from sqlalchemy import text
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            initial_tables = {row[0] for row in result}
            assert "users" in initial_tables
            assert "sessions" in initial_tables

        # Simulate adding a new table to the schema (like a future code update)
        # Add a temporary table to Base.metadata
        new_table = Table(
            'new_feature_table',
            Base.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(100))
        )

        # Reset module globals to simulate restart
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Second initialization - should create the new table
        await init_db()

        # Verify new table was created
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            updated_tables = {row[0] for row in result}
            assert "new_feature_table" in updated_tables, "New table should be created on restart"

        # Clean up
        Base.metadata.remove(new_table)

    @pytest.mark.asyncio
    async def test_init_db_retries_seeding_on_failure(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db doesn't mark DB as initialized if seeding fails.

        Regression test for: migration should only be recorded after successful seeding.
        """
        import app.db.database
        from sqlalchemy.ext.asyncio import async_sessionmaker

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Mock seed_database to fail on first call
        call_count = []

        async def mock_seed_fail_once(session):
            call_count.append(1)
            if len(call_count) == 1:
                raise ValueError("Simulated seeding failure")
            # Succeed on subsequent calls
            pass

        monkeypatch.setattr("app.db.seed.seed_database", mock_seed_fail_once)

        # First initialization attempt should fail
        with pytest.raises(ValueError, match="Simulated seeding failure"):
            await init_db()

        # Verify migration was NOT recorded
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(select(SchemaMigration))
            migrations = result.scalars().all()
            assert len(migrations) == 0, "Migration should not be recorded when seeding fails"

        # Reset for second attempt
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Second initialization should succeed
        await init_db()

        # Verify migration is now recorded
        async with factory() as session:
            result = await session.execute(select(SchemaMigration))
            migrations = result.scalars().all()
            assert len(migrations) == 1, "Migration should be recorded after successful seeding"
            assert migrations[0].version == "001_initial_schema"

    @pytest.mark.asyncio
    async def test_init_db_self_healing_admin_user(self, test_engine: AsyncEngine, monkeypatch):
        """Test that init_db re-creates admin user if deleted (self-healing).

        Regression test for: seeding should run on every startup for self-healing.
        """
        import app.db.database
        from sqlalchemy.ext.asyncio import async_sessionmaker

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # First initialization
        await init_db()

        # Verify admin user exists
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(select(User).where(User.role == "admin"))
            admin = result.scalar_one_or_none()
            assert admin is not None
            admin_username = admin.username

        # Simulate admin user being accidentally deleted
        async with factory() as session:
            result = await session.execute(select(User).where(User.role == "admin"))
            admin = result.scalar_one_or_none()
            if admin:
                await session.delete(admin)
                await session.commit()

        # Verify admin is deleted
        async with factory() as session:
            result = await session.execute(select(User).where(User.role == "admin"))
            admin = result.scalar_one_or_none()
            assert admin is None, "Admin should be deleted"

        # Reset module globals to simulate restart
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # Second initialization should re-create admin (self-healing)
        await init_db()

        # Verify admin user is restored
        async with factory() as session:
            result = await session.execute(select(User).where(User.role == "admin"))
            admin = result.scalar_one_or_none()
            assert admin is not None, "Admin should be self-healed on restart"
            assert admin.username == admin_username

    @pytest.mark.asyncio
    async def test_init_db_seeding_idempotency_no_duplicates(self, test_engine: AsyncEngine, monkeypatch):
        """Test that multiple init_db calls don't create duplicate users.

        Regression test for: seeding must be truly idempotent with no duplicates.
        """
        import app.db.database
        from sqlalchemy.ext.asyncio import async_sessionmaker

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        # First initialization
        await init_db()

        # Count initial users
        factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(select(User))
            initial_users = result.scalars().all()
            initial_count = len(initial_users)
            admin_users = [u for u in initial_users if u.role == "admin"]
            assert len(admin_users) == 1, "Should have exactly one admin after first init"

        # Simulate multiple restarts
        for i in range(3):
            monkeypatch.setattr(app.db.database, "_engine", None)
            monkeypatch.setattr(app.db.database, "_async_session_factory", None)
            monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

            await init_db()

            # Verify user count hasn't changed
            async with factory() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                assert len(users) == initial_count, f"User count changed on restart {i+1}"

                # Verify still only one admin
                admin_users = [u for u in users if u.role == "admin"]
                assert len(admin_users) == 1, f"Admin count changed on restart {i+1}"

    @pytest.mark.asyncio
    async def test_init_db_fresh_install_with_alembic_migration(self, monkeypatch):
        """Test that fresh installs work with Alembic migrations.

        Regression test for: Fresh installs fail because migration runs after create_all().
        When init_db() runs create_all() first, it creates tables with current model definitions
        (including user_id column). Then Alembic tries to add the same column again, causing
        "duplicate column name: user_id" error.

        This test ensures that migrations run before create_all() and are idempotent.
        """
        import app.db.database
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.pool import StaticPool

        # Create a completely fresh in-memory database (no tables created yet)
        fresh_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: fresh_engine)

        # Start with completely empty database
        # Verify no tables exist initially
        async with fresh_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            initial_tables = {row[0] for row in result}
            assert len(initial_tables) == 0, "Database should start empty"

        # Run init_db() - this should work without "duplicate column" errors
        await init_db()

        # Verify tables were created successfully
        async with fresh_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result}
            assert "users" in tables, "users table should be created"
            assert "sessions" in tables, "sessions table should be created"
            assert "processed_images" in tables, "processed_images table should be created"
            assert "schema_migrations" in tables, "schema_migrations table should be created"

            # Verify sessions table has user_id column
            result = await conn.execute(text("PRAGMA table_info(sessions)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            assert "user_id" in column_names, "sessions table should have user_id column"

            # Verify user_id column is NOT NULL
            user_id_col = next(col for col in columns if col[1] == "user_id")
            assert user_id_col[3] == 1, "user_id column should be NOT NULL"  # col[3] is notnull

        # Verify migration was recorded
        from sqlalchemy.ext.asyncio import async_sessionmaker
        factory = async_sessionmaker(fresh_engine, class_=AsyncSession, expire_on_commit=False)

        async with factory() as session:
            result = await session.execute(
                select(SchemaMigration).where(
                    SchemaMigration.version == "001_initial_schema"
                )
            )
            migration = result.scalar_one_or_none()
            assert migration is not None, "Initial migration should be recorded"

        # Simulate restart - run init_db() again
        # This should NOT fail with "duplicate column" error
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: fresh_engine)

        await init_db()  # Should succeed without errors

        # Verify everything still works after restart
        async with factory() as session:
            result = await session.execute(select(User).where(User.role == "admin"))
            admin = result.scalar_one_or_none()
            assert admin is not None, "Admin user should exist after restart"

        # Clean up
        await fresh_engine.dispose()
