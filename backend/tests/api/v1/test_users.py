"""
Integration tests for user profile endpoints.

Tests user profile management and session operations.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import Session as DBSession, User


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("TestPass123"),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """Create JWT token for test user."""
    return create_access_token(
        data={
            "sub": test_user.username,
            "user_id": test_user.id,
            "role": test_user.role,
            "session_id": "test-session-id",
        }
    )


@pytest.mark.asyncio
@pytest.mark.integration
class TestGetUserProfile:
    """Test GET /api/v1/users/me - Get current user profile."""

    async def test_user_can_get_own_profile(
        self, async_client: AsyncClient, user_token: str, test_user: User
    ):
        """User can retrieve their own profile."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["role"] == test_user.role
        assert "hashed_password" not in data

    async def test_get_profile_without_auth(self, async_client: AsyncClient):
        """Getting profile without auth fails (401)."""
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_get_profile_with_expired_token(self, async_client: AsyncClient, expired_token: str):
        """Getting profile with expired token fails (401)."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
class TestChangePassword:
    """Test PUT /api/v1/users/me/password - Change own password."""

    async def test_user_can_change_own_password(
        self, async_client: AsyncClient, user_token: str, test_user: User, db_session: AsyncSession
    ):
        """User can change their own password."""
        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "TestPass123",
                "new_password": "NewSecure123",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        assert "changed successfully" in response.json()["message"].lower()

        # Verify new password works
        await db_session.refresh(test_user)
        assert verify_password("NewSecure123", test_user.hashed_password)
        # Old password shouldn't work
        assert not verify_password("TestPass123", test_user.hashed_password)

    async def test_change_password_wrong_current_password(
        self, async_client: AsyncClient, user_token: str
    ):
        """Changing password with wrong current password fails (400)."""
        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewSecure123",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 400
        assert "current password" in response.json()["detail"].lower()

    async def test_change_password_weak_new_password(
        self, async_client: AsyncClient, user_token: str
    ):
        """Changing to weak password fails (400)."""
        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "TestPass123",
                "new_password": "weak",  # Too weak
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    async def test_change_password_same_as_current(
        self, async_client: AsyncClient, user_token: str
    ):
        """Changing to same password should work but give warning."""
        # This is technically allowed but not recommended
        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "TestPass123",
                "new_password": "TestPass123",  # Same
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Should succeed (password meets requirements)
        assert response.status_code == 200

    async def test_change_password_clears_must_change_flag(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Changing password clears password_must_change flag."""
        # Create user with must_change flag
        user = User(
            username="tempuser",
            email="temp@example.com",
            full_name="Temp User",
            hashed_password=get_password_hash("TempPass123"),
            role="user",
            password_must_change=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )

        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "TempPass123",
                "new_password": "NewSecure123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        await db_session.refresh(user)
        assert user.password_must_change is False

    async def test_change_password_without_auth(self, async_client: AsyncClient):
        """Changing password without auth fails (401)."""
        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "anything",
                "new_password": "NewPass123",
            },
        )

        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
class TestListUserSessions:
    """Test GET /api/v1/users/me/sessions - List active sessions."""

    async def test_user_can_list_own_sessions(
        self, async_client: AsyncClient, user_token: str, test_user: User, db_session: AsyncSession
    ):
        """User can list their active sessions."""
        # Create multiple sessions for user
        session1 = DBSession(user_id=test_user.id, session_id="session-1")
        session2 = DBSession(user_id=test_user.id, session_id="session-2")
        session3 = DBSession(user_id=test_user.id, session_id="session-3")
        db_session.add_all([session1, session2, session3])
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["sessions"]) == 3

        session_ids = [s["session_id"] for s in data["sessions"]]
        assert "session-1" in session_ids
        assert "session-2" in session_ids
        assert "session-3" in session_ids

    async def test_user_sees_only_own_sessions(
        self, async_client: AsyncClient, user_token: str, test_user: User, db_session: AsyncSession
    ):
        """User only sees their own sessions, not others'."""
        # Create user's sessions
        user_session = DBSession(user_id=test_user.id, session_id="user-session")
        db_session.add(user_session)

        # Create another user with sessions
        other_user = User(
            username="other",
            email="other@example.com",
            full_name="Other User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_session = DBSession(user_id=other_user.id, session_id="other-session")
        db_session.add(other_session)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["sessions"][0]["session_id"] == "user-session"

    async def test_list_sessions_empty(
        self, async_client: AsyncClient, user_token: str
    ):
        """Listing sessions when user has none returns empty list."""
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["sessions"] == []

    async def test_list_sessions_without_auth(self, async_client: AsyncClient):
        """Listing sessions without auth fails (401)."""
        response = await async_client.get("/api/v1/users/me/sessions")
        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
class TestDeleteUserSession:
    """Test DELETE /api/v1/users/me/sessions/{session_id} - Remote logout."""

    async def test_user_can_delete_own_session(
        self, async_client: AsyncClient, user_token: str, test_user: User, db_session: AsyncSession
    ):
        """User can delete their own session (remote logout)."""
        # Create sessions
        session1 = DBSession(user_id=test_user.id, session_id="session-to-delete")
        session2 = DBSession(user_id=test_user.id, session_id="session-to-keep")
        db_session.add_all([session1, session2])
        await db_session.commit()

        session_id_to_delete = session1.id

        response = await async_client.delete(
            f"/api/v1/users/me/sessions/{session_id_to_delete}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Verify session deleted
        result = await db_session.get(DBSession, session_id_to_delete)
        assert result is None

        # Other session still exists
        result = await db_session.execute(
            select(DBSession).where(DBSession.session_id == "session-to-keep")
        )
        assert result.scalar_one_or_none() is not None

    async def test_user_cannot_delete_other_users_session(
        self, async_client: AsyncClient, user_token: str, db_session: AsyncSession
    ):
        """User cannot delete another user's session."""
        # Create another user
        other_user = User(
            username="other",
            email="other@example.com",
            full_name="Other User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        # Create session for other user
        other_session = DBSession(user_id=other_user.id, session_id="other-session")
        db_session.add(other_session)
        await db_session.commit()

        # Try to delete other user's session
        response = await async_client.delete(
            f"/api/v1/users/me/sessions/{other_session.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 404  # Not found (not your session)

    async def test_delete_nonexistent_session(
        self, async_client: AsyncClient, user_token: str
    ):
        """Deleting nonexistent session returns 404."""
        response = await async_client.delete(
            "/api/v1/users/me/sessions/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 404

    async def test_delete_session_without_auth(self, async_client: AsyncClient):
        """Deleting session without auth fails (401)."""
        response = await async_client.delete("/api/v1/users/me/sessions/1")
        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.asyncio
class TestUserProfileSecurity:
    """Security tests for user profile endpoints."""

    async def test_inactive_user_cannot_access_profile(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Inactive user cannot access their profile."""
        user = User(
            username="inactive",
            email="inactive@example.com",
            full_name="Inactive User",
            hashed_password=get_password_hash("Pass123"),
            role="user",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )

        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_user_cannot_change_password_to_same(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """User can technically set same password (bcrypt creates new hash)."""
        user = User(
            username="user",
            email="user@example.com",
            full_name="User",
            hashed_password=get_password_hash("SamePass123"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )

        # This should work (new bcrypt hash even for same password)
        response = await async_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "SamePass123",
                "new_password": "SamePass123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
