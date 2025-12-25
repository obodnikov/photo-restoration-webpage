"""
Database seeding utilities.

This module provides functions to seed the database with initial data:
- Create initial admin user from environment variables
"""
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.models import User

logger = logging.getLogger(__name__)


def is_unique_violation(error: IntegrityError) -> bool:
    """
    Check if an IntegrityError is specifically a unique constraint violation.

    This function inspects the database-specific error to distinguish unique
    constraint violations (which are expected in race conditions) from other
    integrity errors like NOT NULL, CHECK, or foreign key violations.

    Supports:
    - PostgreSQL: SQLSTATE 23505 (checks both pgcode and sqlstate attributes)
      - pgcode: psycopg2 (sync driver)
      - sqlstate: asyncpg (async driver)
    - SQLite: Error message contains "UNIQUE constraint failed"
    - MySQL: Error code 1062 (errno attribute)

    Args:
        error: The IntegrityError to inspect

    Returns:
        True if the error is a unique constraint violation, False otherwise
    """
    if not hasattr(error, "orig") or error.orig is None:
        # If we can't determine the error type, treat it as non-unique
        # to be safe (re-raise it)
        return False

    error_msg = str(error.orig).lower()

    # PostgreSQL: Check SQLSTATE code
    # - pgcode: Used by psycopg2 (sync driver)
    # - sqlstate: Used by asyncpg (async driver)
    if hasattr(error.orig, "pgcode") and error.orig.pgcode == "23505":
        return True  # unique_violation
    if hasattr(error.orig, "sqlstate") and error.orig.sqlstate == "23505":
        return True  # unique_violation (asyncpg)

    # SQLite: Check error message
    if "unique constraint failed" in error_msg:
        return True

    # MySQL: Check error code (pymysql uses errno attribute)
    if hasattr(error.orig, "errno") and error.orig.errno == 1062:
        return True

    # If we can't positively identify it as a unique violation, treat it as
    # another type of integrity error (NOT NULL, CHECK, FK, etc.)
    return False


async def seed_admin_user(db: AsyncSession) -> None:
    """
    Create initial admin user from environment variables.

    This function is idempotent - it will only create the admin user
    if one doesn't already exist.

    The admin user credentials are loaded from environment variables:
    - AUTH_USERNAME: Admin username
    - AUTH_PASSWORD: Admin password (will be hashed)
    - AUTH_EMAIL: Admin email
    - AUTH_FULL_NAME: Admin full name

    Args:
        db: Database session

    Raises:
        ValueError: If required environment variables are missing
    """
    settings = get_settings()

    # Check if we have the required environment variables
    if not all(
        [
            settings.auth_username,
            settings.auth_password,
            settings.auth_email,
            settings.auth_full_name,
        ]
    ):
        logger.warning(
            "Cannot create admin user: Missing required environment variables "
            "(AUTH_USERNAME, AUTH_PASSWORD, AUTH_EMAIL, AUTH_FULL_NAME)"
        )
        return

    # Normalize username and email (consistent with UserCreate validator)
    normalized_username = settings.auth_username.lower()
    normalized_email = settings.auth_email.lower()

    # Check if admin user already exists (case-insensitive lookup on both username and email)
    # This ensures idempotency even if admin was previously created with mixed case
    from sqlalchemy import func, or_

    result = await db.execute(
        select(User).where(
            or_(
                func.lower(User.username) == normalized_username,
                func.lower(User.email) == normalized_email
            )
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.info(
            f"Admin user '{existing_user.username}' (email: {existing_user.email}) already exists "
            f"(matched case-insensitively), skipping seed"
        )
        return

    # Create admin user with normalized credentials
    # Use INSERT ... ON CONFLICT to handle race conditions in multi-instance deployments
    admin_user = User(
        username=normalized_username,
        email=normalized_email,
        full_name=settings.auth_full_name,
        hashed_password=get_password_hash(settings.auth_password),
        role="admin",
        is_active=True,
        password_must_change=False,  # Admin created from env doesn't need to change password
    )

    db.add(admin_user)

    try:
        await db.commit()
        await db.refresh(admin_user)
    except IntegrityError as e:
        # IntegrityError can be many things: UNIQUE, NOT NULL, CHECK, FK violations
        # Only suppress UNIQUE constraint violations (expected race conditions)
        # Re-raise all other integrity errors to alert operators
        await db.rollback()

        if is_unique_violation(e):
            # Expected race condition: another instance created the user simultaneously
            # with a conflicting username or email (unique constraint violation)
            logger.info(
                f"Admin user '{normalized_username}' already exists (race condition during creation)"
            )
            return
        else:
            # NOT NULL, CHECK, FK, or other integrity constraint violation
            # This indicates a schema/data problem that needs operator attention
            logger.error(
                f"Failed to create admin user due to integrity constraint violation: {e}",
                exc_info=True
            )
            raise
    except Exception as e:
        # Unexpected database error - re-raise to fail startup and alert operators
        await db.rollback()
        logger.error(
            f"Failed to create admin user due to database error: {e}",
            exc_info=True
        )
        raise

    logger.info(
        f"Created admin user: {admin_user.username} ({admin_user.email}) with ID {admin_user.id}"
    )


async def seed_database(db: AsyncSession) -> None:
    """
    Seed database with initial data.

    This is the main seeding function that should be called during
    application startup. It will create:
    - Initial admin user from environment variables

    This function is idempotent - it will only create users if they
    don't already exist.

    Args:
        db: Database session
    """
    logger.info("Starting database seeding...")

    try:
        await seed_admin_user(db)
        logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise
