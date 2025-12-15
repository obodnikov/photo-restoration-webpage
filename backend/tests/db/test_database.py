"""Tests for database setup and configuration."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings
from app.db.database import (
    close_db,
    configure_sqlite,
    create_engine,
    get_database_url,
    get_db,
    get_engine,
    get_session_factory,
    init_db,
)
from app.db.models import Base


class TestGetDatabaseUrl:
    """Tests for get_database_url function."""

    def test_converts_sync_sqlite_to_async(self, monkeypatch, test_settings):
        """Test that sync SQLite URL is converted to async format."""
        test_settings.database_url = "sqlite:///./test.db"

        def mock_get_settings():
            return test_settings

        import app.db.database

        monkeypatch.setattr(app.db.database, "get_settings", mock_get_settings)

        url = get_database_url()
        assert url == "sqlite+aiosqlite:///./test.db"

    def test_preserves_async_sqlite_url(self, monkeypatch, test_settings):
        """Test that async SQLite URL is preserved."""
        test_settings.database_url = "sqlite+aiosqlite:///./test.db"

        def mock_get_settings():
            return test_settings

        import app.db.database

        monkeypatch.setattr(app.db.database, "get_settings", mock_get_settings)

        url = get_database_url()
        assert url == "sqlite+aiosqlite:///./test.db"

    def test_preserves_other_database_urls(self, monkeypatch, test_settings):
        """Test that non-SQLite URLs are preserved."""
        test_settings.database_url = "postgresql://user:pass@localhost/db"

        def mock_get_settings():
            return test_settings

        import app.db.database

        monkeypatch.setattr(app.db.database, "get_settings", mock_get_settings)

        url = get_database_url()
        assert url == "postgresql://user:pass@localhost/db"


class TestCreateEngine:
    """Tests for create_engine function."""

    def test_creates_async_engine(self, monkeypatch, test_settings):
        """Test that async engine is created."""
        test_settings.database_url = "sqlite+aiosqlite:///:memory:"

        def mock_get_settings():
            return test_settings

        import app.db.database

        monkeypatch.setattr(app.db.database, "get_settings", mock_get_settings)

        engine = create_engine()

        assert isinstance(engine, AsyncEngine)
        assert "sqlite" in str(engine.url)

    def test_engine_configuration(self, monkeypatch, test_settings):
        """Test that engine has correct configuration."""
        test_settings.database_url = "sqlite+aiosqlite:///:memory:"

        def mock_get_settings():
            return test_settings

        import app.db.database

        monkeypatch.setattr(app.db.database, "get_settings", mock_get_settings)

        engine = create_engine()

        # Engine should be configured with StaticPool
        assert engine.pool.__class__.__name__ == "StaticPool"


class TestConfigureSqlite:
    """Tests for configure_sqlite function."""

    @pytest.mark.asyncio
    async def test_configures_wal_mode(self, test_engine):
        """Test that WAL mode is configured.

        Note: WAL mode is not available for in-memory databases.
        For in-memory databases, journal_mode will be 'MEMORY'.
        This test verifies the PRAGMA is executed without error.
        """
        await configure_sqlite(test_engine)

        # Verify PRAGMA was executed (in-memory databases return 'MEMORY')
        async with test_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            # In-memory databases don't support WAL, so mode will be 'MEMORY'
            assert mode.upper() in ("WAL", "MEMORY")

    @pytest.mark.asyncio
    async def test_configures_foreign_keys(self, test_engine):
        """Test that foreign keys are enabled."""
        await configure_sqlite(test_engine)

        # Verify foreign keys are enabled
        async with test_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA foreign_keys"))
            enabled = result.scalar()
            assert enabled == 1

    @pytest.mark.asyncio
    async def test_configures_synchronous(self, test_engine):
        """Test that synchronous mode is configured."""
        await configure_sqlite(test_engine)

        # Verify synchronous mode
        async with test_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA synchronous"))
            sync_mode = result.scalar()
            # NORMAL = 1
            assert sync_mode == 1

    @pytest.mark.asyncio
    async def test_configures_busy_timeout(self, test_engine):
        """Test that busy timeout is configured."""
        await configure_sqlite(test_engine)

        # Verify busy timeout
        async with test_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA busy_timeout"))
            timeout = result.scalar()
            assert timeout == 5000


class TestInitDb:
    """Tests for init_db function."""

    @pytest.mark.asyncio
    async def test_creates_tables(self, test_engine, monkeypatch):
        """Test that tables are created."""
        import app.db.database

        # Mock the global engine
        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        await init_db()

        # Verify tables exist
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result]

            assert "sessions" in tables
            assert "processed_images" in tables

    @pytest.mark.asyncio
    async def test_creates_session_factory(self, test_engine, monkeypatch):
        """Test that session factory is created."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", None)
        monkeypatch.setattr(app.db.database, "_async_session_factory", None)
        monkeypatch.setattr(app.db.database, "create_engine", lambda: test_engine)

        await init_db()

        factory = get_session_factory()
        assert factory is not None

        # Verify can create session
        async with factory() as session:
            assert isinstance(session, AsyncSession)


class TestGetDb:
    """Tests for get_db function."""

    @pytest.mark.asyncio
    async def test_yields_session(self, test_engine, monkeypatch):
        """Test that database session is yielded."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", test_engine)

        # Create session factory
        from sqlalchemy.ext.asyncio import async_sessionmaker

        factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        monkeypatch.setattr(app.db.database, "_async_session_factory", factory)

        # Test generator
        gen = get_db()
        session = await gen.__anext__()

        assert isinstance(session, AsyncSession)

        # Close generator
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    @pytest.mark.asyncio
    async def test_commits_on_success(self, test_engine, monkeypatch):
        """Test that changes are committed on success."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", test_engine)

        # Initialize database
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        from sqlalchemy.ext.asyncio import async_sessionmaker

        factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        monkeypatch.setattr(app.db.database, "_async_session_factory", factory)

        # Use get_db
        gen = get_db()
        session = await gen.__anext__()

        # Add something to session
        from app.db.models import Session as SessionModel

        test_session = SessionModel(
            session_id="test-commit",
            created_at=__import__("datetime").datetime.utcnow(),
            last_accessed=__import__("datetime").datetime.utcnow(),
        )
        session.add(test_session)

        # Close generator (should commit)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

        # Verify committed
        async with factory() as verify_session:
            from sqlalchemy import select

            stmt = select(SessionModel).where(SessionModel.session_id == "test-commit")
            result = await verify_session.execute(stmt)
            found = result.scalar_one_or_none()
            assert found is not None

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self, test_engine, monkeypatch):
        """Test that changes are rolled back on error."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", test_engine)

        # Initialize database
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        from sqlalchemy.ext.asyncio import async_sessionmaker

        factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        monkeypatch.setattr(app.db.database, "_async_session_factory", factory)

        # Use get_db and raise error
        gen = get_db()
        session = await gen.__anext__()

        from app.db.models import Session as SessionModel

        test_session = SessionModel(
            session_id="test-rollback",
            created_at=__import__("datetime").datetime.utcnow(),
            last_accessed=__import__("datetime").datetime.utcnow(),
        )
        session.add(test_session)

        # Throw into generator to simulate error
        try:
            await gen.athrow(Exception("Test error"))
        except Exception:
            pass

        # Verify not committed
        async with factory() as verify_session:
            from sqlalchemy import select

            stmt = select(SessionModel).where(
                SessionModel.session_id == "test-rollback"
            )
            result = await verify_session.execute(stmt)
            found = result.scalar_one_or_none()
            assert found is None


class TestCloseDb:
    """Tests for close_db function."""

    @pytest.mark.asyncio
    async def test_disposes_engine(self, test_engine, monkeypatch):
        """Test that engine is disposed."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", test_engine)
        monkeypatch.setattr(app.db.database, "_async_session_factory", "factory")

        await close_db()

        # Verify globals are reset
        assert app.db.database._engine is None
        assert app.db.database._async_session_factory is None


class TestGetEngine:
    """Tests for get_engine function."""

    def test_returns_engine_when_initialized(self, test_engine, monkeypatch):
        """Test that engine is returned when initialized."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", test_engine)

        engine = get_engine()
        assert engine is test_engine

    def test_raises_error_when_not_initialized(self, monkeypatch):
        """Test that error is raised when not initialized."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_engine", None)

        with pytest.raises(RuntimeError, match="not initialized"):
            get_engine()


class TestGetSessionFactory:
    """Tests for get_session_factory function."""

    def test_returns_factory_when_initialized(self, monkeypatch):
        """Test that factory is returned when initialized."""
        import app.db.database

        mock_factory = "test_factory"
        monkeypatch.setattr(app.db.database, "_async_session_factory", mock_factory)

        factory = get_session_factory()
        assert factory == mock_factory

    def test_raises_error_when_not_initialized(self, monkeypatch):
        """Test that error is raised when not initialized."""
        import app.db.database

        monkeypatch.setattr(app.db.database, "_async_session_factory", None)

        with pytest.raises(RuntimeError, match="not initialized"):
            get_session_factory()
