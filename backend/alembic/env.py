import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import app models and database configuration
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from app.db.models import Base
from app.db.database import get_database_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set database URL from app settings
config.set_main_option("sqlalchemy.url", get_database_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")

    # Convert async dialect to sync for offline mode
    # Offline mode doesn't use async engines
    if "sqlite+aiosqlite://" in url:
        url = url.replace("sqlite+aiosqlite://", "sqlite://")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Strategy:
    - Default: Run migrations synchronously (for CLI usage)
    - If already in event loop: Also run synchronously (avoid nested loops)
    - Async mode is only used when explicitly needed (not for CLI)

    This ensures 'alembic upgrade head' works from CLI without issues.
    """
    # Always run synchronously to avoid async/sync URL mismatch issues
    # The app's database URL may be async (sqlite+aiosqlite) but we convert
    # it to sync (sqlite) in run_migrations_sync() for compatibility
    run_migrations_sync()


def run_migrations_sync() -> None:
    """Run migrations synchronously (for use in async contexts)."""
    from sqlalchemy import create_engine

    url = config.get_main_option("sqlalchemy.url")

    # Convert async dialect to sync for synchronous engine
    # SQLAlchemy's create_engine() cannot handle async dialects like sqlite+aiosqlite
    if "sqlite+aiosqlite://" in url:
        url = url.replace("sqlite+aiosqlite://", "sqlite://")

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
