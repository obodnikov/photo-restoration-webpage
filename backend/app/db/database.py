"""
Database setup and configuration.

This module provides async SQLAlchemy setup with SQLite,
following best practices for WAL mode and proper configuration.
"""
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.models import Base, SchemaMigration

# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """
    Get database URL from settings.

    Converts sync SQLite URL to async format for aiosqlite.

    Returns:
        Async database URL
    """
    settings = get_settings()
    db_url = settings.database_url

    # Ensure URL is in async format
    if db_url.startswith("sqlite://"):
        # Convert to aiosqlite format
        return db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        return db_url
    else:
        return db_url


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with proper SQLite configuration.

    Configures:
    - WAL mode for concurrent reads/writes
    - StaticPool for connection reuse
    - Proper timeout and busy_timeout settings

    Returns:
        Configured AsyncEngine instance
    """
    database_url = get_database_url()

    # Create engine with SQLite-specific settings
    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL query logging
        poolclass=StaticPool,  # Use StaticPool for SQLite
        connect_args={
            "check_same_thread": False,  # Allow multi-threading
            "timeout": 30.0,  # Connection timeout (seconds)
        },
    )

    return engine


async def configure_sqlite(engine: AsyncEngine) -> None:
    """
    Configure SQLite with WAL mode and optimal settings.

    This should be called once during application startup.

    Args:
        engine: AsyncEngine instance to configure
    """
    async with engine.begin() as conn:
        # Enable WAL mode for concurrent access
        await conn.execute(text("PRAGMA journal_mode=WAL"))

        # Optimize for performance
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        await conn.execute(text("PRAGMA busy_timeout=5000"))

        # Foreign key enforcement
        await conn.execute(text("PRAGMA foreign_keys=ON"))


async def is_db_initialized(engine: AsyncEngine) -> bool:
    """
    Check if the database has been initialized with the schema.

    This checks if the schema_migrations table exists and contains
    the initial migration record.

    Args:
        engine: AsyncEngine instance to check

    Returns:
        True if database is initialized, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)

    from sqlalchemy import inspect, select
    from sqlalchemy.exc import OperationalError

    try:
        async with engine.connect() as conn:
            # Check if schema_migrations table exists
            def check_table_exists(sync_conn):
                inspector = inspect(sync_conn)
                table_names = inspector.get_table_names()
                exists = "schema_migrations" in table_names
                logger.debug(f"schema_migrations table exists: {exists}, all tables: {table_names}")
                return exists

            table_exists = await conn.run_sync(check_table_exists)

            if not table_exists:
                logger.debug("schema_migrations table does not exist")
                return False

            # Check if initial migration is recorded
            # Use text query because conn.execute() with ORM models doesn't work properly
            from sqlalchemy import text
            result = await conn.execute(
                text("SELECT COUNT(*) FROM schema_migrations WHERE version = :version"),
                {"version": "001_initial_schema"}
            )
            count = result.scalar()

            if count and count > 0:
                logger.debug(f"Found migration record: 001_initial_schema")
                return True
            else:
                logger.debug("Migration '001_initial_schema' not found in schema_migrations table")
                return False

    except OperationalError as e:
        # Database file doesn't exist or is not accessible
        logger.debug(f"OperationalError checking database initialization: {e}")
        return False


async def record_migration(session: AsyncSession, version: str, description: str) -> None:
    """
    Record a migration as applied in the database.

    Args:
        session: Database session
        version: Migration version identifier
        description: Human-readable description of the migration
    """
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    # Check if migration already recorded
    result = await session.execute(
        select(SchemaMigration).where(SchemaMigration.version == version)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Migration already recorded, skip
        return

    # Record the migration
    migration = SchemaMigration(
        version=version,
        description=description,
    )
    session.add(migration)

    try:
        await session.commit()
    except IntegrityError:
        # Race condition: another instance recorded it simultaneously
        await session.rollback()
        # This is fine, migration is recorded


async def run_alembic_migrations() -> None:
    """
    Run Alembic migrations to upgrade database schema.

    This function runs pending Alembic migrations to ensure the database
    schema is up to date. It is the PRIMARY mechanism for schema management.

    The function runs in a separate thread to avoid blocking the async event loop,
    since alembic.command.upgrade() is synchronous.
    """
    import logging
    import asyncio
    logger = logging.getLogger(__name__)

    def _run_migrations_sync() -> None:
        """Synchronous wrapper for Alembic migrations."""
        try:
            from alembic import command
            from alembic.config import Config
            from pathlib import Path

            # Get alembic.ini path
            alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"

            if not alembic_cfg_path.exists():
                logger.warning(f"Alembic config not found at {alembic_cfg_path}, skipping migrations")
                return

            # Create Alembic config
            alembic_cfg = Config(str(alembic_cfg_path))

            # Run migrations to head
            logger.info("Running Alembic migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic migrations completed successfully")

        except ImportError:
            logger.warning("Alembic not installed, skipping migrations")
        except Exception as e:
            logger.error(f"Failed to run Alembic migrations: {e}", exc_info=True)
            raise

    # Run migrations in a separate thread to avoid blocking the event loop
    try:
        await asyncio.to_thread(_run_migrations_sync)
    except Exception as e:
        logger.error(f"Failed to run Alembic migrations in thread: {e}", exc_info=True)
        raise


async def init_db() -> None:
    """
    Initialize database: run migrations, configure SQLite, and seed initial data.

    Schema Management Strategy:
    - Alembic migrations are the PRIMARY mechanism for schema creation and updates
    - Base migration (000_initial_schema) creates all tables on fresh installs
    - create_all() runs as a FALLBACK to catch unmigrated model changes

    This function is idempotent:
    - ALWAYS runs Alembic migrations (creates tables, handles column additions, etc.)
    - ALWAYS runs create_all() as fallback (creates missing tables not in migrations)
    - Tracks initialization via schema_migrations to avoid re-seeding
    - Re-runs seeding every startup for self-healing (seeding is idempotent)

    This should be called during application startup.
    Performs:
    1. Creates database engine
    2. Configures SQLite (WAL mode, foreign keys, etc.)
    3. Runs Alembic migrations (primary schema management)
    4. Runs create_all() as fallback (catches unmigrated tables)
    5. Creates session factory
    6. On first initialization: records migration and seeds data
    7. On subsequent startups: re-runs idempotent seeding for self-healing
    """
    import logging
    import os
    logger = logging.getLogger(__name__)

    global _engine, _async_session_factory

    # Log database URL for debugging (redact credentials for security)
    database_url = get_database_url()

    # Redact credentials from database URL for logging
    def redact_db_url(url: str) -> str:
        """Redact username and password from database URL for secure logging."""
        import re
        # Pattern matches: scheme://user:pass@host/db or scheme:///path
        # Replace user:pass@ with ***:***@
        redacted = re.sub(r'://([^:/@]+):([^@]+)@', r'://***:***@', url)
        return redacted

    logger.info(f"Database URL: {redact_db_url(database_url)}")

    # Extract file path from URL for existence check
    if database_url.startswith("sqlite+aiosqlite:///"):
        db_path = database_url[len("sqlite+aiosqlite:///"):]
        if os.path.exists(db_path):
            logger.info(f"Database file exists at: {db_path}")
        else:
            logger.warning(f"Database file does NOT exist at: {db_path}")
    else:
        logger.info("Non-file database URL, skipping file existence check")

    # Create engine if not exists
    if _engine is None:
        _engine = create_engine()

    # Configure SQLite
    await configure_sqlite(_engine)

    # Run Alembic migrations to create/update schema
    # Alembic is now the PRIMARY mechanism for schema management
    # The base migration (000_initial_schema) creates all tables on fresh installs
    await run_alembic_migrations()

    # Run create_all() as a FALLBACK only
    # This catches any tables added to models but not yet in Alembic migrations
    # In a properly maintained codebase, this should be a no-op
    # CRITICAL: create_all() does NOT add new columns to existing tables
    # CRITICAL: create_all() does NOT drop, rename, or alter columns
    # For schema changes, you MUST create Alembic migrations
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database schema synchronized")

    # Create session factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual flush control
            autocommit=False,  # Manual commit control
        )

    # Check if this is first initialization
    db_initialized = await is_db_initialized(_engine)
    logger.info(f"Database initialized status: {db_initialized}")

    async with _async_session_factory() as session:
        try:
            if not db_initialized:
                # First initialization: seed data first, then record migration
                logger.info("First initialization: creating initial data")

                from app.db.seed import seed_database
                await seed_database(session)

                # Only record migration AFTER successful seeding
                # This ensures we retry if seeding fails
                await record_migration(
                    session,
                    "001_initial_schema",
                    "Initial database schema with users, sessions, and processed_images tables"
                )
                logger.info("Database initialized successfully")
            else:
                # Subsequent startups: re-run idempotent seeding for self-healing
                # This ensures admin user exists even if accidentally deleted
                logger.info("Database already initialized, running self-healing seed")

                from app.db.seed import seed_database
                try:
                    await seed_database(session)
                    logger.info("Self-healing seed completed")
                except Exception as seed_error:
                    # Self-healing seed failures are logged but don't crash startup
                    # since the DB is already initialized and may be operational
                    logger.warning(
                        f"Self-healing seed failed (application will continue): {seed_error}",
                        exc_info=True
                    )

        except Exception as e:
            # Only fail startup on first initialization errors
            if not db_initialized:
                logger.error(f"Failed to initialize database: {e}", exc_info=True)
                raise
            # For initialized DBs, errors during self-healing were already logged above
            pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    This is a dependency that can be injected into FastAPI routes.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    global _async_session_factory

    if _async_session_factory is None:
        await init_db()

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """
    Close database connections.

    This should be called during application shutdown.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None

    _async_session_factory = None


def get_engine() -> AsyncEngine:
    """
    Get the current database engine.

    Returns:
        AsyncEngine instance

    Raises:
        RuntimeError: If database not initialized
    """
    global _engine

    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get the session factory.

    Returns:
        async_sessionmaker instance

    Raises:
        RuntimeError: If database not initialized
    """
    global _async_session_factory

    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return _async_session_factory
