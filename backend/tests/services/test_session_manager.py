"""Tests for session manager service."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.services.session_manager import (
    ImageStorageError,
    SessionManager,
    SessionManagerError,
    SessionNotFoundError,
)


class TestSessionManagerInit:
    """Tests for SessionManager initialization."""

    def test_init_with_settings(self, test_settings):
        """Test initialization with custom settings."""
        manager = SessionManager(test_settings)

        assert manager.settings == test_settings
        assert manager.storage_path == Path(test_settings.upload_dir)
        assert manager.processed_path == Path(test_settings.processed_dir)

    def test_init_without_settings(self):
        """Test initialization without settings uses global settings."""
        manager = SessionManager()

        assert manager.settings is not None
        assert isinstance(manager.storage_path, Path)
        assert isinstance(manager.processed_path, Path)

    def test_creates_directories(self, test_settings, tmp_path):
        """Test that required directories are created."""
        test_settings.upload_dir = tmp_path / "uploads"
        test_settings.processed_dir = tmp_path / "processed"

        manager = SessionManager(test_settings)

        assert manager.storage_path.exists()
        assert manager.processed_path.exists()


class TestCreateSession:
    """Tests for create_session method."""

    @pytest.mark.asyncio
    async def test_creates_session(self, db_session, test_settings):
        """Test creating a new session."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        assert session.id is not None
        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID length
        assert session.created_at is not None
        assert session.last_accessed is not None

    @pytest.mark.asyncio
    async def test_creates_unique_session_ids(self, db_session, test_settings):
        """Test that each session has unique ID."""
        manager = SessionManager(test_settings)

        session1 = await manager.create_session(db_session)
        session2 = await manager.create_session(db_session)

        assert session1.session_id != session2.session_id

    @pytest.mark.asyncio
    async def test_handles_database_error(self, test_settings, monkeypatch):
        """Test error handling when database fails."""
        manager = SessionManager(test_settings)

        # Create mock session that raises error
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock(side_effect=Exception("DB Error"))
        mock_session.rollback = Mock()

        # Convert to async mock
        from unittest.mock import AsyncMock

        mock_session.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_session.rollback = AsyncMock()

        with pytest.raises(SessionManagerError, match="Failed to create session"):
            await manager.create_session(mock_session)

        mock_session.rollback.assert_called_once()


class TestGetSession:
    """Tests for get_session method."""

    @pytest.mark.asyncio
    async def test_gets_existing_session(self, db_session, test_settings):
        """Test getting existing session."""
        manager = SessionManager(test_settings)

        # Create session
        created_session = await manager.create_session(db_session)

        # Get session
        retrieved_session = await manager.get_session(
            db_session, created_session.session_id
        )

        assert retrieved_session.id == created_session.id
        assert retrieved_session.session_id == created_session.session_id

    @pytest.mark.asyncio
    async def test_updates_last_accessed(self, db_session, test_settings):
        """Test that last_accessed is updated."""
        manager = SessionManager(test_settings)

        # Create session
        session = await manager.create_session(db_session)
        original_accessed = session.last_accessed

        # Wait a bit
        import asyncio

        await asyncio.sleep(0.1)

        # Get session (should update last_accessed)
        retrieved = await manager.get_session(db_session, session.session_id)

        assert retrieved.last_accessed >= original_accessed

    @pytest.mark.asyncio
    async def test_does_not_update_when_update_access_false(
        self, db_session, test_settings
    ):
        """Test that last_accessed is not updated when update_access=False."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)
        original_accessed = session.last_accessed

        import asyncio

        await asyncio.sleep(0.1)

        # Get without updating
        await manager.get_session(db_session, session.session_id, update_access=False)

        # Re-fetch to verify
        from sqlalchemy import select

        from app.db.models import Session

        stmt = select(Session).where(Session.session_id == session.session_id)
        result = await db_session.execute(stmt)
        fresh_session = result.scalar_one()

        # Should be same or very close (within microseconds)
        assert abs((fresh_session.last_accessed - original_accessed).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_session(self, db_session, test_settings):
        """Test error when session doesn't exist."""
        manager = SessionManager(test_settings)

        with pytest.raises(SessionNotFoundError, match="not found"):
            await manager.get_session(db_session, "nonexistent-id")


class TestGetSessionHistory:
    """Tests for get_session_history method."""

    @pytest.mark.asyncio
    async def test_gets_empty_history(self, db_session, test_settings):
        """Test getting history for session with no images."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)
        history = await manager.get_session_history(db_session, session.session_id)

        assert history == []

    @pytest.mark.asyncio
    async def test_gets_session_history(self, db_session, test_settings):
        """Test getting session history with images."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        # Save some processed images
        for i in range(3):
            await manager.save_processed_image(
                db_session,
                session.session_id,
                f"test{i}.jpg",
                "test-model",
                f"uploads/test{i}.jpg",
                f"processed/test{i}_result.jpg",
            )

        # Get history
        history = await manager.get_session_history(db_session, session.session_id)

        assert len(history) == 3
        assert all(img.session_id == session.id for img in history)

    @pytest.mark.asyncio
    async def test_history_ordered_by_created_desc(self, db_session, test_settings):
        """Test that history is ordered by created_at descending."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        # Save images with slight delays
        import asyncio

        filenames = []
        for i in range(3):
            filename = f"test{i}.jpg"
            filenames.append(filename)
            await manager.save_processed_image(
                db_session,
                session.session_id,
                filename,
                "test-model",
                f"uploads/{filename}",
                f"processed/{filename}_result.jpg",
            )
            await asyncio.sleep(0.01)

        # Get history
        history = await manager.get_session_history(db_session, session.session_id)

        # Most recent should be first
        assert history[0].original_filename == filenames[-1]
        assert history[-1].original_filename == filenames[0]

    @pytest.mark.asyncio
    async def test_history_with_limit(self, db_session, test_settings):
        """Test getting history with limit."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        # Save 5 images
        for i in range(5):
            await manager.save_processed_image(
                db_session,
                session.session_id,
                f"test{i}.jpg",
                "test-model",
                f"uploads/test{i}.jpg",
                f"processed/test{i}_result.jpg",
            )

        # Get with limit
        history = await manager.get_session_history(
            db_session, session.session_id, limit=3
        )

        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_history_with_offset(self, db_session, test_settings):
        """Test getting history with offset."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        # Save 5 images
        for i in range(5):
            await manager.save_processed_image(
                db_session,
                session.session_id,
                f"test{i}.jpg",
                "test-model",
                f"uploads/test{i}.jpg",
                f"processed/test{i}_result.jpg",
            )

        # Get with offset
        history = await manager.get_session_history(
            db_session, session.session_id, offset=2
        )

        assert len(history) == 3  # 5 - 2 offset

    @pytest.mark.asyncio
    async def test_history_for_nonexistent_session(self, db_session, test_settings):
        """Test error when getting history for nonexistent session."""
        manager = SessionManager(test_settings)

        with pytest.raises(SessionNotFoundError):
            await manager.get_session_history(db_session, "nonexistent-id")


class TestSaveProcessedImage:
    """Tests for save_processed_image method."""

    @pytest.mark.asyncio
    async def test_saves_processed_image(self, db_session, test_settings):
        """Test saving processed image."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        image = await manager.save_processed_image(
            db_session,
            session.session_id,
            "test.jpg",
            "test-model",
            "uploads/test.jpg",
            "processed/test_result.jpg",
        )

        assert image.id is not None
        assert image.session_id == session.id
        assert image.original_filename == "test.jpg"
        assert image.model_id == "test-model"
        assert image.original_path == "uploads/test.jpg"
        assert image.processed_path == "processed/test_result.jpg"

    @pytest.mark.asyncio
    async def test_saves_with_model_parameters(self, db_session, test_settings):
        """Test saving with model parameters."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        params = {"scale": 2, "denoise": True}
        image = await manager.save_processed_image(
            db_session,
            session.session_id,
            "test.jpg",
            "test-model",
            "uploads/test.jpg",
            "processed/test_result.jpg",
            model_parameters=params,
        )

        assert image.model_parameters is not None
        parsed_params = json.loads(image.model_parameters)
        assert parsed_params == params

    @pytest.mark.asyncio
    async def test_updates_session_last_accessed(self, db_session, test_settings):
        """Test that saving image updates session last_accessed."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)
        original_accessed = session.last_accessed

        import asyncio

        await asyncio.sleep(0.1)

        await manager.save_processed_image(
            db_session,
            session.session_id,
            "test.jpg",
            "test-model",
            "uploads/test.jpg",
            "processed/test_result.jpg",
        )

        # Re-fetch session
        from sqlalchemy import select

        from app.db.models import Session

        stmt = select(Session).where(Session.session_id == session.session_id)
        result = await db_session.execute(stmt)
        updated_session = result.scalar_one()

        assert updated_session.last_accessed > original_accessed

    @pytest.mark.asyncio
    async def test_error_for_nonexistent_session(self, db_session, test_settings):
        """Test error when saving to nonexistent session."""
        manager = SessionManager(test_settings)

        with pytest.raises(SessionNotFoundError):
            await manager.save_processed_image(
                db_session,
                "nonexistent-id",
                "test.jpg",
                "test-model",
                "uploads/test.jpg",
                "processed/test_result.jpg",
            )


class TestCleanupOldSessions:
    """Tests for cleanup_old_sessions method."""

    @pytest.mark.asyncio
    async def test_cleans_up_old_sessions(self, db_session, test_settings, tmp_path):
        """Test cleanup of old sessions."""
        test_settings.upload_dir = tmp_path / "uploads"
        test_settings.processed_dir = tmp_path / "processed"
        manager = SessionManager(test_settings)

        # Create old session
        from app.db.models import Session

        old_session = Session(
            session_id="old-session",
            created_at=datetime.utcnow() - timedelta(hours=48),
            last_accessed=datetime.utcnow() - timedelta(hours=48),
        )
        db_session.add(old_session)
        await db_session.commit()
        await db_session.refresh(old_session)

        # Create recent session
        recent_session = await manager.create_session(db_session)

        # Cleanup sessions older than 24 hours
        sessions_deleted, files_deleted = await manager.cleanup_old_sessions(
            db_session, hours=24
        )

        assert sessions_deleted == 1

        # Verify old session is gone
        from sqlalchemy import select

        stmt = select(Session).where(Session.session_id == "old-session")
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

        # Verify recent session still exists
        stmt = select(Session).where(Session.session_id == recent_session.session_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_deletes_associated_files(self, db_session, test_settings, tmp_path):
        """Test that associated files are deleted."""
        test_settings.upload_dir = tmp_path / "uploads"
        test_settings.processed_dir = tmp_path / "processed"
        manager = SessionManager(test_settings)

        # Create old session with image
        from app.db.models import ProcessedImage, Session

        old_session = Session(
            session_id="old-with-files",
            created_at=datetime.utcnow() - timedelta(hours=48),
            last_accessed=datetime.utcnow() - timedelta(hours=48),
        )
        db_session.add(old_session)
        await db_session.commit()
        await db_session.refresh(old_session)

        # Create files
        original_file = manager.storage_path / "old_original.jpg"
        processed_file = manager.processed_path / "old_processed.jpg"
        original_file.parent.mkdir(parents=True, exist_ok=True)
        processed_file.parent.mkdir(parents=True, exist_ok=True)
        original_file.write_text("test")
        processed_file.write_text("test")

        # Add image record
        image = ProcessedImage(
            session_id=old_session.id,
            original_filename="old.jpg",
            model_id="test",
            original_path="old_original.jpg",
            processed_path="old_processed.jpg",
            created_at=datetime.utcnow(),
        )
        db_session.add(image)
        await db_session.commit()

        # Cleanup
        sessions_deleted, files_deleted = await manager.cleanup_old_sessions(
            db_session, hours=24
        )

        assert sessions_deleted == 1
        assert files_deleted == 2
        assert not original_file.exists()
        assert not processed_file.exists()

    @pytest.mark.asyncio
    async def test_handles_missing_files(self, db_session, test_settings, tmp_path):
        """Test that cleanup handles missing files gracefully."""
        test_settings.upload_dir = tmp_path / "uploads"
        test_settings.processed_dir = tmp_path / "processed"
        manager = SessionManager(test_settings)

        # Create old session with image record but no files
        from app.db.models import ProcessedImage, Session

        old_session = Session(
            session_id="old-no-files",
            created_at=datetime.utcnow() - timedelta(hours=48),
            last_accessed=datetime.utcnow() - timedelta(hours=48),
        )
        db_session.add(old_session)
        await db_session.commit()
        await db_session.refresh(old_session)

        image = ProcessedImage(
            session_id=old_session.id,
            original_filename="missing.jpg",
            model_id="test",
            original_path="missing_original.jpg",
            processed_path="missing_processed.jpg",
            created_at=datetime.utcnow(),
        )
        db_session.add(image)
        await db_session.commit()

        # Should not raise error
        sessions_deleted, files_deleted = await manager.cleanup_old_sessions(
            db_session, hours=24
        )

        assert sessions_deleted == 1
        assert files_deleted == 0


class TestDeleteSession:
    """Tests for delete_session method."""

    @pytest.mark.asyncio
    async def test_deletes_session(self, db_session, test_settings):
        """Test deleting a session."""
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)
        session_id = session.session_id

        await manager.delete_session(db_session, session_id)

        # Verify deleted
        with pytest.raises(SessionNotFoundError):
            await manager.get_session(db_session, session_id, update_access=False)

    @pytest.mark.asyncio
    async def test_deletes_session_files(self, db_session, test_settings, tmp_path):
        """Test that session files are deleted."""
        test_settings.upload_dir = tmp_path / "uploads"
        test_settings.processed_dir = tmp_path / "processed"
        manager = SessionManager(test_settings)

        session = await manager.create_session(db_session)

        # Create files
        original_file = manager.storage_path / "delete_original.jpg"
        processed_file = manager.processed_path / "delete_processed.jpg"
        original_file.parent.mkdir(parents=True, exist_ok=True)
        processed_file.parent.mkdir(parents=True, exist_ok=True)
        original_file.write_text("test")
        processed_file.write_text("test")

        # Save image
        await manager.save_processed_image(
            db_session,
            session.session_id,
            "delete.jpg",
            "test-model",
            "delete_original.jpg",
            "delete_processed.jpg",
        )

        # Delete session
        files_deleted = await manager.delete_session(db_session, session.session_id)

        assert files_deleted == 2
        assert not original_file.exists()
        assert not processed_file.exists()

    @pytest.mark.asyncio
    async def test_error_for_nonexistent_session(self, db_session, test_settings):
        """Test error when deleting nonexistent session."""
        manager = SessionManager(test_settings)

        with pytest.raises(SessionNotFoundError):
            await manager.delete_session(db_session, "nonexistent-id")


class TestGetStoragePaths:
    """Tests for get_storage_path_for_session and get_processed_path_for_session."""

    def test_get_storage_path(self, test_settings, tmp_path):
        """Test getting storage path for session."""
        test_settings.upload_dir = tmp_path / "uploads"
        manager = SessionManager(test_settings)

        session_id = "test-session-123"
        path = manager.get_storage_path_for_session(session_id)

        assert path == manager.storage_path / session_id
        assert path.exists()

    def test_get_processed_path(self, test_settings, tmp_path):
        """Test getting processed path for session."""
        test_settings.processed_dir = tmp_path / "processed"
        manager = SessionManager(test_settings)

        session_id = "test-session-456"
        path = manager.get_processed_path_for_session(session_id)

        assert path == manager.processed_path / session_id
        assert path.exists()

    def test_creates_paths_if_not_exist(self, test_settings, tmp_path):
        """Test that paths are created if they don't exist."""
        test_settings.upload_dir = tmp_path / "uploads"
        test_settings.processed_dir = tmp_path / "processed"
        manager = SessionManager(test_settings)

        # Remove directories
        import shutil

        if manager.storage_path.exists():
            shutil.rmtree(manager.storage_path)
        if manager.processed_path.exists():
            shutil.rmtree(manager.processed_path)

        # Should create them
        session_id = "new-session"
        storage_path = manager.get_storage_path_for_session(session_id)
        processed_path = manager.get_processed_path_for_session(session_id)

        assert storage_path.exists()
        assert processed_path.exists()
