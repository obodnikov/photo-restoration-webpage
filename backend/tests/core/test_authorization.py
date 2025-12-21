"""
Tests for authorization middleware and dependencies.

Tests role-based access control and user verification.
"""
from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_active_user, require_admin
from app.core.security import create_access_token
from app.db.models import User
from app.core.security import get_password_hash


@pytest.mark.asyncio
class TestAuthorization:
    """Test authorization dependencies."""

    async def test_require_admin_with_admin_user(self, db_session: AsyncSession):
        """Admin user passes require_admin check."""
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("Pass123"),
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create token
        token_data = {
            "sub": "admin",
            "user_id": admin.id,
            "role": "admin",
        }
        token = create_access_token(data=token_data)

        # Verify token and get user (simulating get_current_user dependency)
        from app.core.security import verify_token
        payload = verify_token(token)
        assert payload is not None

        # Mock current_user for dependency
        current_user = {
            "user_id": payload["user_id"],
            "username": payload["sub"],
            "role": payload["role"],
        }

        # Fetch from database
        result = await db_session.get(User, current_user["user_id"])
        assert result is not None

        # Should not raise exception
        user = await require_admin(current_user, db_session)
        assert user.role == "admin"
        assert user.id == admin.id

    async def test_require_admin_with_regular_user(self, db_session: AsyncSession):
        """Regular user fails require_admin check."""
        # Create regular user
        user = User(
            username="user",
            email="user@example.com",
            full_name="Regular User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Mock current_user
        current_user = {
            "user_id": user.id,
            "username": "user",
            "role": "user",
        }

        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user, db_session)

        assert exc_info.value.status_code == 403
        assert "Admin" in exc_info.value.detail or "admin" in exc_info.value.detail

    async def test_require_admin_with_inactive_admin(self, db_session: AsyncSession):
        """Inactive admin user fails require_admin check."""
        # Create inactive admin
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("Pass123"),
            role="admin",
            is_active=False,  # Inactive
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        current_user = {
            "user_id": admin.id,
            "username": "admin",
            "role": "admin",
        }

        # Should raise 403 (inactive user)
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user, db_session)

        assert exc_info.value.status_code == 403
        assert "inactive" in exc_info.value.detail.lower()

    async def test_require_admin_user_not_found(self, db_session: AsyncSession):
        """require_admin fails if user not found in database."""
        current_user = {
            "user_id": 99999,  # Non-existent ID
            "username": "ghost",
            "role": "admin",
        }

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user, db_session)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_require_active_user_with_active_user(self, db_session: AsyncSession):
        """Active user passes require_active_user check."""
        user = User(
            username="user",
            email="user@example.com",
            full_name="Active User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        current_user = {
            "user_id": user.id,
            "username": "user",
            "role": "user",
        }

        # Should not raise exception
        result = await require_active_user(current_user, db_session)
        assert result.id == user.id
        assert result.is_active is True

    async def test_require_active_user_with_inactive_user(self, db_session: AsyncSession):
        """Inactive user fails require_active_user check."""
        user = User(
            username="user",
            email="user@example.com",
            full_name="Inactive User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        current_user = {
            "user_id": user.id,
            "username": "user",
            "role": "user",
        }

        with pytest.raises(HTTPException) as exc_info:
            await require_active_user(current_user, db_session)

        assert exc_info.value.status_code == 403
        assert "inactive" in exc_info.value.detail.lower()

    async def test_require_active_user_not_found(self, db_session: AsyncSession):
        """require_active_user fails if user not found."""
        current_user = {
            "user_id": 88888,
            "username": "phantom",
            "role": "user",
        }

        with pytest.raises(HTTPException) as exc_info:
            await require_active_user(current_user, db_session)

        assert exc_info.value.status_code == 404

    async def test_admin_can_pass_active_user_check(self, db_session: AsyncSession):
        """Admin user can also pass active user check."""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("Pass123"),
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        current_user = {
            "user_id": admin.id,
            "username": "admin",
            "role": "admin",
        }

        # Admin should pass active user check
        result = await require_active_user(current_user, db_session)
        assert result.role == "admin"
        assert result.is_active is True


@pytest.mark.unit
class TestAuthorizationUnit:
    """Fast unit tests for authorization."""

    @pytest.mark.asyncio
    async def test_admin_authorization_quick(self, db_session: AsyncSession):
        """Quick test for admin authorization."""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin",
            hashed_password="hashed",
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        current_user = {"user_id": admin.id, "username": "admin", "role": "admin"}
        user = await require_admin(current_user, db_session)
        assert user.role == "admin"


@pytest.mark.auth
class TestAuthorizationSecurity:
    """Security-focused authorization tests."""

    @pytest.mark.asyncio
    async def test_role_spoofing_prevented(self, db_session: AsyncSession):
        """User cannot spoof admin role in database."""
        # Create regular user
        user = User(
            username="user",
            email="user@example.com",
            full_name="User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Attacker tries to claim admin role in token
        current_user = {
            "user_id": user.id,
            "username": "user",
            "role": "admin",  # Spoofed role
        }

        # Should fail because database has role="user"
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user, db_session)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_deleted_user_cannot_access(self, db_session: AsyncSession):
        """Deleted user cannot access even with valid token."""
        user = User(
            username="user",
            email="user@example.com",
            full_name="User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        user_id = user.id

        # Delete user
        await db_session.delete(user)
        await db_session.commit()

        # Token still valid but user deleted
        current_user = {
            "user_id": user_id,
            "username": "user",
            "role": "user",
        }

        with pytest.raises(HTTPException) as exc_info:
            await require_active_user(current_user, db_session)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_concurrent_role_change(self, db_session: AsyncSession):
        """Authorization checks current database state, not token."""
        # Create admin
        user = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin",
            hashed_password=get_password_hash("Pass123"),
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Token issued when user was admin
        current_user = {
            "user_id": user.id,
            "username": "admin",
            "role": "admin",
        }

        # User demoted to regular user (by another admin)
        user.role = "user"
        await db_session.commit()

        # Should fail even though token says admin
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user, db_session)

        assert exc_info.value.status_code == 403
