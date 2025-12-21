"""
Integration tests for admin user management endpoints.

Tests all admin CRUD operations and authorization.
"""
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import User


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and return an admin user."""
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Create and return a regular user."""
    user = User(
        username="user",
        email="user@example.com",
        full_name="Regular User",
        hashed_password=get_password_hash("UserPass123"),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create JWT token for admin user."""
    return create_access_token(
        data={
            "sub": admin_user.username,
            "user_id": admin_user.id,
            "role": admin_user.role,
        }
    )


@pytest.fixture
def user_token(regular_user: User) -> str:
    """Create JWT token for regular user."""
    return create_access_token(
        data={
            "sub": regular_user.username,
            "user_id": regular_user.id,
            "role": regular_user.role,
        }
    )


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminCreateUser:
    """Test POST /api/v1/admin/users - Create user."""

    async def test_admin_can_create_user(
        self, async_client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """Admin can create a new user."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "NewPass123",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

        # Verify in database
        result = await db_session.execute(
            select(User).where(User.username == "newuser")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "newuser@example.com"

    async def test_admin_can_create_user_with_password_must_change(
        self, async_client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """Admin can create user with password_must_change flag."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "tempuser",
                "email": "temp@example.com",
                "full_name": "Temp User",
                "password": "TempPass123",
                "role": "user",
                "password_must_change": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["password_must_change"] is True

    async def test_regular_user_cannot_create_user(
        self, async_client: AsyncClient, user_token: str
    ):
        """Regular user cannot create users (403 Forbidden)."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "hacker",
                "email": "hacker@example.com",
                "full_name": "Hacker",
                "password": "HackPass123",
                "role": "admin",  # Trying to create admin
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403

    async def test_create_user_without_auth(self, async_client: AsyncClient):
        """Creating user without authentication fails (401)."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "noauth",
                "email": "noauth@example.com",
                "full_name": "No Auth",
                "password": "Pass123",
                "role": "user",
            },
        )

        assert response.status_code == 401

    async def test_create_user_duplicate_username(
        self, async_client: AsyncClient, admin_token: str, regular_user: User
    ):
        """Creating user with duplicate username fails (400)."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": regular_user.username,  # Already exists
                "email": "different@example.com",
                "full_name": "Different User",
                "password": "Pass123",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    async def test_create_user_duplicate_email(
        self, async_client: AsyncClient, admin_token: str, regular_user: User
    ):
        """Creating user with duplicate email fails (400)."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "differentuser",
                "email": regular_user.email,  # Already exists
                "full_name": "Different User",
                "password": "Pass123",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    async def test_create_user_weak_password(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Creating user with weak password fails (400)."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "weakuser",
                "email": "weak@example.com",
                "full_name": "Weak User",
                "password": "weak",  # Too weak
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    async def test_create_user_invalid_role(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Creating user with invalid role fails (422)."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "username": "baduser",
                "email": "bad@example.com",
                "full_name": "Bad User",
                "password": "GoodPass123",
                "role": "superadmin",  # Invalid role
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminListUsers:
    """Test GET /api/v1/admin/users - List users."""

    async def test_admin_can_list_users(
        self, async_client: AsyncClient, admin_token: str, admin_user: User, regular_user: User
    ):
        """Admin can list all users."""
        response = await async_client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] == 2  # admin + regular user
        assert len(data["users"]) == 2

        usernames = [u["username"] for u in data["users"]]
        assert admin_user.username in usernames
        assert regular_user.username in usernames

    async def test_admin_can_list_users_with_pagination(
        self, async_client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """Admin can list users with pagination."""
        # Create multiple users
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                hashed_password=get_password_hash("Pass123"),
                role="user",
            )
            db_session.add(user)
        await db_session.commit()

        # Get first page (limit 3)
        response = await async_client.get(
            "/api/v1/admin/users?limit=3&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 3
        assert data["total"] >= 5

        # Get second page
        response = await async_client.get(
            "/api/v1/admin/users?limit=3&offset=3",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) >= 2

    async def test_regular_user_cannot_list_users(
        self, async_client: AsyncClient, user_token: str
    ):
        """Regular user cannot list users (403)."""
        response = await async_client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403

    async def test_list_users_without_auth(self, async_client: AsyncClient):
        """Listing users without auth fails (401)."""
        response = await async_client.get("/api/v1/admin/users")
        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminGetUser:
    """Test GET /api/v1/admin/users/{user_id} - Get user details."""

    async def test_admin_can_get_user_details(
        self, async_client: AsyncClient, admin_token: str, regular_user: User
    ):
        """Admin can get specific user details."""
        response = await async_client.get(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regular_user.id
        assert data["username"] == regular_user.username
        assert data["email"] == regular_user.email
        assert data["full_name"] == regular_user.full_name
        assert "hashed_password" not in data

    async def test_admin_get_nonexistent_user(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Getting nonexistent user returns 404."""
        response = await async_client.get(
            "/api/v1/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    async def test_regular_user_cannot_get_user_details(
        self, async_client: AsyncClient, user_token: str, admin_user: User
    ):
        """Regular user cannot get user details (403)."""
        response = await async_client.get(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminUpdateUser:
    """Test PUT /api/v1/admin/users/{user_id} - Update user."""

    async def test_admin_can_update_user(
        self, async_client: AsyncClient, admin_token: str, regular_user: User, db_session: AsyncSession
    ):
        """Admin can update user information."""
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}",
            json={
                "full_name": "Updated Name",
                "email": "updated@example.com",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

        # Verify in database
        await db_session.refresh(regular_user)
        assert regular_user.full_name == "Updated Name"
        assert regular_user.email == "updated@example.com"

    async def test_admin_can_change_user_role(
        self, async_client: AsyncClient, admin_token: str, regular_user: User, db_session: AsyncSession
    ):
        """Admin can change user role."""
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

        await db_session.refresh(regular_user)
        assert regular_user.role == "admin"

    async def test_admin_can_activate_deactivate_user(
        self, async_client: AsyncClient, admin_token: str, regular_user: User, db_session: AsyncSession
    ):
        """Admin can activate/deactivate users."""
        # Deactivate
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

        await db_session.refresh(regular_user)
        assert regular_user.is_active is False

        # Reactivate
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    async def test_update_user_duplicate_email(
        self, async_client: AsyncClient, admin_token: str, admin_user: User, regular_user: User
    ):
        """Updating to duplicate email fails (400)."""
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"email": admin_user.email},  # Duplicate
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    async def test_regular_user_cannot_update_user(
        self, async_client: AsyncClient, user_token: str, admin_user: User
    ):
        """Regular user cannot update users (403)."""
        response = await async_client.put(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"full_name": "Hacked Name"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminDeleteUser:
    """Test DELETE /api/v1/admin/users/{user_id} - Delete user."""

    async def test_admin_can_delete_user(
        self, async_client: AsyncClient, admin_token: str, regular_user: User, db_session: AsyncSession
    ):
        """Admin can delete a user."""
        user_id = regular_user.id

        response = await async_client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Verify deleted from database
        result = await db_session.get(User, user_id)
        assert result is None

    async def test_delete_nonexistent_user(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Deleting nonexistent user returns 404."""
        response = await async_client.delete(
            "/api/v1/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    async def test_regular_user_cannot_delete_user(
        self, async_client: AsyncClient, user_token: str, admin_user: User
    ):
        """Regular user cannot delete users (403)."""
        response = await async_client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminResetPassword:
    """Test PUT /api/v1/admin/users/{user_id}/reset-password - Reset password."""

    async def test_admin_can_reset_user_password(
        self, async_client: AsyncClient, admin_token: str, regular_user: User, db_session: AsyncSession
    ):
        """Admin can reset user password."""
        new_password = "NewSecure123"

        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}/reset-password",
            json={"new_password": new_password},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()

        # Verify new password works
        await db_session.refresh(regular_user)
        assert verify_password(new_password, regular_user.hashed_password)

    async def test_reset_password_sets_must_change_flag(
        self, async_client: AsyncClient, admin_token: str, regular_user: User, db_session: AsyncSession
    ):
        """Resetting password sets password_must_change flag."""
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}/reset-password",
            json={
                "new_password": "NewPass123",
                "require_change_on_login": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        await db_session.refresh(regular_user)
        assert regular_user.password_must_change is True

    async def test_reset_password_weak_password(
        self, async_client: AsyncClient, admin_token: str, regular_user: User
    ):
        """Resetting with weak password fails (400)."""
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}/reset-password",
            json={"new_password": "weak"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    async def test_regular_user_cannot_reset_password(
        self, async_client: AsyncClient, user_token: str, admin_user: User
    ):
        """Regular user cannot reset passwords (403)."""
        response = await async_client.put(
            f"/api/v1/admin/users/{admin_user.id}/reset-password",
            json={"new_password": "HackedPass123"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403
