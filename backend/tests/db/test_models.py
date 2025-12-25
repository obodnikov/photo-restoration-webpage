"""Tests for database models."""
import json
from datetime import datetime

import pytest
from sqlalchemy import select

from app.db.models import ProcessedImage, Session


class TestSessionModel:
    """Tests for Session model."""

    @pytest.mark.asyncio
    async def test_create_session(self, db_session, test_user):
        """Test creating a session."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert session.session_id == "test-session-123"
        assert session.created_at is not None
        assert session.last_accessed is not None
        assert session.processed_images == []

    @pytest.mark.asyncio
    async def test_session_unique_session_id(self, db_session, test_user):
        """Test that session_id must be unique."""
        session1 = Session(
            user_id=test_user.id,
            session_id="duplicate-id",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        db_session.add(session1)
        await db_session.commit()

        # Try to create another session with same session_id
        session2 = Session(
            user_id=test_user.id,
            session_id="duplicate-id",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        db_session.add(session2)

        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_session_to_dict(self, db_session, test_user):
        """Test Session.to_dict() method."""
        session = Session(
            user_id=test_user.id,
            session_id="test-dict-session",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        result = session.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == session.id
        assert result["session_id"] == "test-dict-session"
        assert "created_at" in result
        assert "last_accessed" in result
        assert result["image_count"] == 0

    @pytest.mark.asyncio
    async def test_session_repr(self, db_session, test_user):
        """Test Session.__repr__() method."""
        session = Session(
            user_id=test_user.id,
            session_id="test-repr-session",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        repr_str = repr(session)

        assert "Session" in repr_str
        assert "test-repr-session" in repr_str
        assert str(session.id) in repr_str


class TestProcessedImageModel:
    """Tests for ProcessedImage model."""

    @pytest.mark.asyncio
    async def test_create_processed_image(self, db_session, test_user):
        """Test creating a processed image."""
        # Create session first
        session = Session(
            user_id=test_user.id,
            session_id="test-session-img",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Create processed image
        processed_image = ProcessedImage(
            session_id=session.id,
            original_filename="test.jpg",
            model_id="test-model",
            original_path="uploads/test.jpg",
            processed_path="processed/test_result.jpg",
            model_parameters='{"scale": 2}',
            created_at=datetime.utcnow(),
        )

        db_session.add(processed_image)
        await db_session.commit()
        await db_session.refresh(processed_image)

        assert processed_image.id is not None
        assert processed_image.session_id == session.id
        assert processed_image.original_filename == "test.jpg"
        assert processed_image.model_id == "test-model"
        assert processed_image.original_path == "uploads/test.jpg"
        assert processed_image.processed_path == "processed/test_result.jpg"
        assert processed_image.model_parameters == '{"scale": 2}'

    @pytest.mark.asyncio
    async def test_processed_image_without_parameters(self, db_session, test_user):
        """Test creating processed image without model parameters."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-no-params",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        processed_image = ProcessedImage(
            session_id=session.id,
            original_filename="test2.jpg",
            model_id="test-model-2",
            original_path="uploads/test2.jpg",
            processed_path="processed/test2_result.jpg",
            created_at=datetime.utcnow(),
        )

        db_session.add(processed_image)
        await db_session.commit()
        await db_session.refresh(processed_image)

        assert processed_image.model_parameters is None

    @pytest.mark.asyncio
    async def test_processed_image_to_dict(self, db_session, test_user):
        """Test ProcessedImage.to_dict() method."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-dict",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        processed_image = ProcessedImage(
            session_id=session.id,
            original_filename="dict_test.jpg",
            model_id="dict-model",
            original_path="uploads/dict_test.jpg",
            processed_path="processed/dict_test_result.jpg",
            model_parameters='{"test": true}',
            created_at=datetime.utcnow(),
        )

        db_session.add(processed_image)
        await db_session.commit()
        await db_session.refresh(processed_image)

        result = processed_image.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == processed_image.id
        assert result["session_id"] == session.id
        assert result["original_filename"] == "dict_test.jpg"
        assert result["model_id"] == "dict-model"
        assert result["original_path"] == "uploads/dict_test.jpg"
        assert result["processed_path"] == "processed/dict_test_result.jpg"
        assert result["model_parameters"] == '{"test": true}'
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_processed_image_repr(self, db_session, test_user):
        """Test ProcessedImage.__repr__() method."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-repr",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        processed_image = ProcessedImage(
            session_id=session.id,
            original_filename="repr_test.jpg",
            model_id="repr-model",
            original_path="uploads/repr_test.jpg",
            processed_path="processed/repr_test_result.jpg",
            created_at=datetime.utcnow(),
        )

        db_session.add(processed_image)
        await db_session.commit()
        await db_session.refresh(processed_image)

        repr_str = repr(processed_image)

        assert "ProcessedImage" in repr_str
        assert "repr_test.jpg" in repr_str
        assert "repr-model" in repr_str


class TestSessionImageRelationship:
    """Tests for Session-ProcessedImage relationship."""

    @pytest.mark.asyncio
    async def test_session_with_multiple_images(self, db_session, test_user):
        """Test session with multiple processed images."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-multi",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Create multiple images
        for i in range(3):
            image = ProcessedImage(
                session_id=session.id,
                original_filename=f"test{i}.jpg",
                model_id="test-model",
                original_path=f"uploads/test{i}.jpg",
                processed_path=f"processed/test{i}_result.jpg",
                created_at=datetime.utcnow(),
            )
            db_session.add(image)

        await db_session.commit()
        await db_session.refresh(session)

        assert len(session.processed_images) == 3
        assert session.to_dict()["image_count"] == 3

    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session, test_user):
        """Test that deleting session cascades to processed images."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-cascade",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Store session_id before deletion
        session_db_id = session.id

        # Create images
        for i in range(2):
            image = ProcessedImage(
                session_id=session.id,
                original_filename=f"cascade{i}.jpg",
                model_id="test-model",
                original_path=f"uploads/cascade{i}.jpg",
                processed_path=f"processed/cascade{i}_result.jpg",
                created_at=datetime.utcnow(),
            )
            db_session.add(image)

        await db_session.commit()

        # Delete session
        await db_session.delete(session)
        await db_session.commit()

        # Verify images are also deleted (use stored session_db_id)
        stmt = select(ProcessedImage).where(ProcessedImage.session_id == session_db_id)
        result = await db_session.execute(stmt)
        images = result.scalars().all()

        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_access_image_from_session(self, db_session, test_user):
        """Test accessing images through session relationship."""
        session = Session(
            user_id=test_user.id,
            session_id="test-session-access",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        image = ProcessedImage(
            session_id=session.id,
            original_filename="access_test.jpg",
            model_id="access-model",
            original_path="uploads/access_test.jpg",
            processed_path="processed/access_test_result.jpg",
            created_at=datetime.utcnow(),
        )
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(session)

        # Access through relationship
        assert len(session.processed_images) == 1
        assert session.processed_images[0].original_filename == "access_test.jpg"
        assert session.processed_images[0].model_id == "access-model"
