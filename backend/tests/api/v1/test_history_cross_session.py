"""
Integration tests for cross-session history access.

Tests that users can view ALL their images across all sessions.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models import ProcessedImage, Session as DBSession, User


@pytest.fixture
async def user1(db_session: AsyncSession) -> User:
    """Create first test user."""
    user = User(
        username="user1",
        email="user1@example.com",
        full_name="User One",
        hashed_password=get_password_hash("Pass123"),
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user2(db_session: AsyncSession) -> User:
    """Create second test user."""
    user = User(
        username="user2",
        email="user2@example.com",
        full_name="User Two",
        hashed_password=get_password_hash("Pass123"),
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def create_user_token(user: User, session_id: str = "test-session") -> str:
    """Create JWT token for user."""
    return create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "session_id": session_id,
        }
    )


@pytest.mark.asyncio
@pytest.mark.integration
class TestCrossSessionHistory:
    """Test cross-session history access."""

    async def test_user_sees_images_from_all_sessions(
        self, async_client: AsyncClient, user1: User, db_session: AsyncSession
    ):
        """User can see images from ALL their sessions."""
        # Create multiple sessions for user1
        session1 = DBSession(user_id=user1.id, session_id="session-1")
        session2 = DBSession(user_id=user1.id, session_id="session-2")
        session3 = DBSession(user_id=user1.id, session_id="session-3")
        db_session.add_all([session1, session2, session3])
        await db_session.commit()
        await db_session.refresh(session1)
        await db_session.refresh(session2)
        await db_session.refresh(session3)

        # Create images in different sessions
        image1 = ProcessedImage(
            session_id=session1.id,
            original_filename="photo1.jpg",
            model_id="model1",
            original_path="/uploads/photo1.jpg",
            processed_path="/processed/photo1.jpg",
        )
        image2 = ProcessedImage(
            session_id=session2.id,
            original_filename="photo2.jpg",
            model_id="model1",
            original_path="/uploads/photo2.jpg",
            processed_path="/processed/photo2.jpg",
        )
        image3 = ProcessedImage(
            session_id=session3.id,
            original_filename="photo3.jpg",
            model_id="model1",
            original_path="/uploads/photo3.jpg",
            processed_path="/processed/photo3.jpg",
        )
        db_session.add_all([image1, image2, image3])
        await db_session.commit()

        # User requests history (from any session)
        token = create_user_token(user1, session_id="session-1")
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) == 3  # All images across all sessions

        filenames = [img["original_filename"] for img in data["images"]]
        assert "photo1.jpg" in filenames
        assert "photo2.jpg" in filenames
        assert "photo3.jpg" in filenames

    async def test_user_only_sees_own_images(
        self, async_client: AsyncClient, user1: User, user2: User, db_session: AsyncSession
    ):
        """User only sees their own images, not other users'."""
        # Create sessions for both users
        user1_session = DBSession(user_id=user1.id, session_id="user1-session")
        user2_session = DBSession(user_id=user2.id, session_id="user2-session")
        db_session.add_all([user1_session, user2_session])
        await db_session.commit()
        await db_session.refresh(user1_session)
        await db_session.refresh(user2_session)

        # Create images for both users
        user1_image = ProcessedImage(
            session_id=user1_session.id,
            original_filename="user1_photo.jpg",
            model_id="model1",
            original_path="/uploads/user1_photo.jpg",
            processed_path="/processed/user1_photo.jpg",
        )
        user2_image = ProcessedImage(
            session_id=user2_session.id,
            original_filename="user2_photo.jpg",
            model_id="model1",
            original_path="/uploads/user2_photo.jpg",
            processed_path="/processed/user2_photo.jpg",
        )
        db_session.add_all([user1_image, user2_image])
        await db_session.commit()

        # User1 requests history
        token = create_user_token(user1)
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1
        assert data["images"][0]["original_filename"] == "user1_photo.jpg"

        # User2 requests history
        token = create_user_token(user2)
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1
        assert data["images"][0]["original_filename"] == "user2_photo.jpg"

    async def test_empty_history_for_new_user(
        self, async_client: AsyncClient, user1: User
    ):
        """New user with no images sees empty history."""
        token = create_user_token(user1)
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["images"] == []
        assert data["total"] == 0

    async def test_history_pagination_across_sessions(
        self, async_client: AsyncClient, user1: User, db_session: AsyncSession
    ):
        """History pagination works across multiple sessions."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = DBSession(user_id=user1.id, session_id=f"session-{i}")
            db_session.add(session)
            sessions.append(session)
        await db_session.commit()

        # Create 10 images across sessions
        for i, session in enumerate(sessions):
            await db_session.refresh(session)
            for j in range(3):
                image = ProcessedImage(
                    session_id=session.id,
                    original_filename=f"photo_{i}_{j}.jpg",
                    model_id="model1",
                    original_path=f"/uploads/photo_{i}_{j}.jpg",
                    processed_path=f"/processed/photo_{i}_{j}.jpg",
                )
                db_session.add(image)
        await db_session.commit()

        token = create_user_token(user1)

        # Get first page (limit 5)
        response = await async_client.get(
            "/api/v1/restore/history?limit=5&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 5
        assert data["total"] == 9

        # Get second page
        response = await async_client.get(
            "/api/v1/restore/history?limit=5&offset=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 4  # Remaining images
        assert data["total"] == 9

    async def test_history_ordered_by_created_at(
        self, async_client: AsyncClient, user1: User, db_session: AsyncSession
    ):
        """History is ordered by created_at DESC (newest first)."""
        # Create session
        session = DBSession(user_id=user1.id, session_id="session-1")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Create images (SQLite auto timestamps)
        image1 = ProcessedImage(
            session_id=session.id,
            original_filename="old.jpg",
            model_id="model1",
            original_path="/uploads/old.jpg",
            processed_path="/processed/old.jpg",
        )
        db_session.add(image1)
        await db_session.commit()

        image2 = ProcessedImage(
            session_id=session.id,
            original_filename="new.jpg",
            model_id="model1",
            original_path="/uploads/new.jpg",
            processed_path="/processed/new.jpg",
        )
        db_session.add(image2)
        await db_session.commit()

        token = create_user_token(user1)
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Newest first
        assert data["images"][0]["original_filename"] == "new.jpg"
        assert data["images"][1]["original_filename"] == "old.jpg"

    async def test_deleting_session_keeps_user_images(
        self, async_client: AsyncClient, user1: User, db_session: AsyncSession
    ):
        """Deleting a session still shows user's other images."""
        # Create two sessions
        session1 = DBSession(user_id=user1.id, session_id="session-1")
        session2 = DBSession(user_id=user1.id, session_id="session-2")
        db_session.add_all([session1, session2])
        await db_session.commit()
        await db_session.refresh(session1)
        await db_session.refresh(session2)

        # Create images in both sessions
        image1 = ProcessedImage(
            session_id=session1.id,
            original_filename="session1.jpg",
            model_id="model1",
            original_path="/uploads/session1.jpg",
            processed_path="/processed/session1.jpg",
        )
        image2 = ProcessedImage(
            session_id=session2.id,
            original_filename="session2.jpg",
            model_id="model1",
            original_path="/uploads/session2.jpg",
            processed_path="/processed/session2.jpg",
        )
        db_session.add_all([image1, image2])
        await db_session.commit()

        # Delete session1 (should cascade delete image1)
        await db_session.delete(session1)
        await db_session.commit()

        # User should still see image from session2
        token = create_user_token(user1)
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1
        assert data["images"][0]["original_filename"] == "session2.jpg"

    async def test_history_without_auth(self, async_client: AsyncClient):
        """Getting history without auth fails (401)."""
        response = await async_client.get("/api/v1/restore/history")
        assert response.status_code == 401


@pytest.mark.unit
class TestHistoryAccessUnit:
    """Quick unit tests for history access."""

    @pytest.mark.asyncio
    async def test_basic_history_access(
        self, async_client: AsyncClient, user1: User, db_session: AsyncSession
    ):
        """Basic history access works."""
        session = DBSession(user_id=user1.id, session_id="s1")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        image = ProcessedImage(
            session_id=session.id,
            original_filename="test.jpg",
            model_id="m1",
            original_path="/test.jpg",
            processed_path="/test_out.jpg",
        )
        db_session.add(image)
        await db_session.commit()

        token = create_user_token(user1)
        response = await async_client.get(
            "/api/v1/restore/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert len(response.json()["images"]) == 1
