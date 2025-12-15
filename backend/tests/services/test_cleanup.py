"""
Tests for cleanup service.

This module tests the background cleanup task:
- Old session deletion
- Associated file deletion
- Recent session preservation
- Missing file handling
"""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.services.cleanup import cleanup_old_sessions
from app.services.session_manager import SessionManager


@pytest.mark.asyncio
class TestCleanupService:
    """Test suite for cleanup service."""

    async def test_cleanup_deletes_old_sessions(
        self, async_session, test_settings
    ):
        """Test cleanup deletes sessions older than threshold."""
        session_manager = SessionManager(test_settings)

        # Create an old session (25 hours ago)
        old_session = await session_manager.create_session(async_session)
        old_session.last_accessed = datetime.utcnow() - timedelta(hours=25)
        await async_session.commit()

        # Create a recent session (1 hour ago)
        recent_session = await session_manager.create_session(async_session)
        recent_session.last_accessed = datetime.utcnow() - timedelta(hours=1)
        await async_session.commit()

        # Run cleanup (default 24 hours)
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=24
        )

        # Should delete old session only
        assert sessions_deleted == 1

        # Verify old session is gone
        from app.db.models import Session
        from sqlalchemy import select

        stmt = select(Session).where(Session.session_id == old_session.session_id)
        result = await async_session.execute(stmt)
        assert result.scalar_one_or_none() is None

        # Verify recent session still exists
        stmt = select(Session).where(Session.session_id == recent_session.session_id)
        result = await async_session.execute(stmt)
        assert result.scalar_one_or_none() is not None

    async def test_cleanup_deletes_associated_files(
        self, async_session, test_settings, test_image_jpeg
    ):
        """Test cleanup deletes files associated with old sessions."""
        session_manager = SessionManager(test_settings)

        # Create old session with files
        old_session = await session_manager.create_session(async_session)
        old_session.last_accessed = datetime.utcnow() - timedelta(hours=25)
        await async_session.commit()

        # Create files for this session
        original_dir = session_manager.get_storage_path_for_session(
            old_session.session_id
        )
        processed_dir = session_manager.get_processed_path_for_session(
            old_session.session_id
        )

        original_file = original_dir / "test_original.jpg"
        processed_file = processed_dir / "test_processed.jpg"

        original_file.write_bytes(test_image_jpeg)
        processed_file.write_bytes(test_image_jpeg)

        # Save metadata
        await session_manager.save_processed_image(
            db=async_session,
            session_id=old_session.session_id,
            original_filename="test.jpg",
            model_id="swin2sr-2x",
            original_path=f"{old_session.session_id}/test_original.jpg",
            processed_path=f"{old_session.session_id}/test_processed.jpg",
        )

        # Verify files exist before cleanup
        assert original_file.exists()
        assert processed_file.exists()

        # Run cleanup
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=24
        )

        assert sessions_deleted == 1
        assert files_deleted == 2

        # Verify files are deleted
        assert not original_file.exists()
        assert not processed_file.exists()

    async def test_cleanup_preserves_recent_sessions(
        self, async_session, test_settings, test_image_jpeg
    ):
        """Test cleanup preserves recent sessions and their files."""
        session_manager = SessionManager(test_settings)

        # Create recent session with files
        recent_session = await session_manager.create_session(async_session)
        recent_session.last_accessed = datetime.utcnow() - timedelta(hours=1)
        await async_session.commit()

        # Create files
        original_dir = session_manager.get_storage_path_for_session(
            recent_session.session_id
        )
        original_file = original_dir / "recent_original.jpg"
        original_file.write_bytes(test_image_jpeg)

        # Save metadata
        await session_manager.save_processed_image(
            db=async_session,
            session_id=recent_session.session_id,
            original_filename="recent.jpg",
            model_id="swin2sr-2x",
            original_path=f"{recent_session.session_id}/recent_original.jpg",
            processed_path=f"{recent_session.session_id}/recent_processed.jpg",
        )

        # Run cleanup
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=24
        )

        # Should not delete anything
        assert sessions_deleted == 0
        assert files_deleted == 0

        # Verify session still exists
        from app.db.models import Session
        from sqlalchemy import select

        stmt = select(Session).where(Session.session_id == recent_session.session_id)
        result = await async_session.execute(stmt)
        assert result.scalar_one_or_none() is not None

        # Verify file still exists
        assert original_file.exists()

    async def test_cleanup_handles_missing_files_gracefully(
        self, async_session, test_settings
    ):
        """Test cleanup handles missing files without errors."""
        session_manager = SessionManager(test_settings)

        # Create old session
        old_session = await session_manager.create_session(async_session)
        old_session.last_accessed = datetime.utcnow() - timedelta(hours=25)
        await async_session.commit()

        # Save metadata for files that don't exist
        await session_manager.save_processed_image(
            db=async_session,
            session_id=old_session.session_id,
            original_filename="missing.jpg",
            model_id="swin2sr-2x",
            original_path=f"{old_session.session_id}/missing_original.jpg",
            processed_path=f"{old_session.session_id}/missing_processed.jpg",
        )

        # Run cleanup (should not raise exception)
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=24
        )

        # Should delete session even though files are missing
        assert sessions_deleted == 1
        assert files_deleted == 0  # No actual files to delete

    async def test_cleanup_with_multiple_old_sessions(
        self, async_session, test_settings
    ):
        """Test cleanup handles multiple old sessions correctly."""
        session_manager = SessionManager(test_settings)

        # Create 3 old sessions
        old_sessions = []
        for i in range(3):
            session = await session_manager.create_session(async_session)
            session.last_accessed = datetime.utcnow() - timedelta(hours=25 + i)
            old_sessions.append(session)
        await async_session.commit()

        # Create 2 recent sessions
        for i in range(2):
            session = await session_manager.create_session(async_session)
            session.last_accessed = datetime.utcnow() - timedelta(hours=i)
        await async_session.commit()

        # Run cleanup
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=24
        )

        # Should delete 3 old sessions
        assert sessions_deleted == 3

    async def test_cleanup_with_custom_hours_threshold(
        self, async_session, test_settings
    ):
        """Test cleanup with custom hours threshold."""
        session_manager = SessionManager(test_settings)

        # Create session 10 hours old
        session_10h = await session_manager.create_session(async_session)
        session_10h.last_accessed = datetime.utcnow() - timedelta(hours=10)

        # Create session 5 hours old
        session_5h = await session_manager.create_session(async_session)
        session_5h.last_accessed = datetime.utcnow() - timedelta(hours=5)

        await async_session.commit()

        # Cleanup with 8 hour threshold
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=8
        )

        # Should only delete 10-hour old session
        assert sessions_deleted == 1

        # Verify which session was deleted
        from app.db.models import Session
        from sqlalchemy import select

        stmt = select(Session).where(Session.session_id == session_10h.session_id)
        result = await async_session.execute(stmt)
        assert result.scalar_one_or_none() is None

        stmt = select(Session).where(Session.session_id == session_5h.session_id)
        result = await async_session.execute(stmt)
        assert result.scalar_one_or_none() is not None

    async def test_cleanup_empty_database(
        self, async_session, test_settings
    ):
        """Test cleanup with no sessions returns zero."""
        session_manager = SessionManager(test_settings)

        # Run cleanup on empty database
        sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
            async_session, hours=24
        )

        assert sessions_deleted == 0
        assert files_deleted == 0
