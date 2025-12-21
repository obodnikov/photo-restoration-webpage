"""
Database seeding utilities.

This module provides functions to seed the database with initial data:
- Create initial admin user from environment variables
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.models import User

logger = logging.getLogger(__name__)


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

    # Check if admin user already exists (use normalized username)
    result = await db.execute(
        select(User).where(User.username == normalized_username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.info(f"Admin user '{normalized_username}' already exists, skipping seed")
        return

    # Create admin user with normalized credentials
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
    await db.commit()
    await db.refresh(admin_user)

    logger.info(
        f"Created admin user: {admin_user.username} ({admin_user.email}) with ID {admin_user.id}"
    )


async def seed_database(db: AsyncSession) -> None:
    """
    Seed database with initial data.

    This is the main seeding function that should be called during
    application startup. It will create:
    - Initial admin user from environment variables

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
