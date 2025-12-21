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
from app.db.models import Base

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


async def init_db() -> None:
    """
    Initialize database: create tables, configure SQLite, and seed initial data.

    This should be called once during application startup.
    Performs:
    1. Creates database engine
    2. Configures SQLite (WAL mode, foreign keys, etc.)
    3. Creates all tables
    4. Seeds initial data (admin user)
    """
    global _engine, _async_session_factory

    # Create engine if not exists
    if _engine is None:
        _engine = create_engine()

    # Configure SQLite
    await configure_sqlite(_engine)

    # Create all tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual flush control
            autocommit=False,  # Manual commit control
        )

    # Seed initial data (admin user)
    from app.db.seed import seed_database

    async with _async_session_factory() as session:
        try:
            await seed_database(session)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to seed database: {e}")
            # Don't fail startup if seeding fails
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
