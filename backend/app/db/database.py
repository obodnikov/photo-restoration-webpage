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
    from sqlalchemy import inspect, select
    from sqlalchemy.exc import OperationalError

    try:
        async with engine.connect() as conn:
            # Check if schema_migrations table exists
            def check_table_exists(sync_conn):
                inspector = inspect(sync_conn)
                return "schema_migrations" in inspector.get_table_names()

            table_exists = await conn.run_sync(check_table_exists)

            if not table_exists:
                return False

            # Check if initial migration is recorded
            result = await conn.execute(
                select(SchemaMigration).where(
                    SchemaMigration.version == "001_initial_schema"
                )
            )
            migration = result.scalar_one_or_none()

            return migration is not None

    except OperationalError:
        # Database file doesn't exist or is not accessible
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


async def init_db() -> None:
    """
    Initialize database: create tables, configure SQLite, and seed initial data.

    This function is idempotent - it checks if the database is already initialized
    and skips schema creation if the initial migration is already recorded.
    This prevents re-running migrations on container restart.

    This should be called during application startup.
    Performs:
    1. Creates database engine
    2. Configures SQLite (WAL mode, foreign keys, etc.)
    3. Checks if database is already initialized
    4. Creates all tables (only if not initialized)
    5. Records initial migration
    6. Seeds initial data (admin user, only if not initialized)
    """
    import logging
    logger = logging.getLogger(__name__)

    global _engine, _async_session_factory

    # Create engine if not exists
    if _engine is None:
        _engine = create_engine()

    # Configure SQLite
    await configure_sqlite(_engine)

    # Check if database is already initialized
    db_initialized = await is_db_initialized(_engine)

    if db_initialized:
        logger.info("Database already initialized, skipping schema creation and seeding")
    else:
        logger.info("Database not initialized, creating schema and seeding initial data")

        # Create all tables
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database schema created successfully")

    # Create session factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual flush control
            autocommit=False,  # Manual commit control
        )

    # Only seed if database was just initialized
    if not db_initialized:
        async with _async_session_factory() as session:
            try:
                # Record initial migration
                await record_migration(
                    session,
                    "001_initial_schema",
                    "Initial database schema with users, sessions, and processed_images tables"
                )
                logger.info("Recorded initial migration: 001_initial_schema")

                # Seed initial data (admin user)
                from app.db.seed import seed_database
                await seed_database(session)
                logger.info("Database seeding completed successfully")

            except Exception as e:
                logger.error(f"Failed to initialize database: {e}", exc_info=True)
                # Fail startup if initial migration fails
                raise


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
