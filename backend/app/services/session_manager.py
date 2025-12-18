"""
Session management service.

This module handles user sessions, image storage, and history tracking
for the photo restoration application.
"""
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.db.models import ProcessedImage, Session

# Configure logging
logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """Base exception for session manager errors."""

    pass


class SessionNotFoundError(SessionManagerError):
    """Raised when session is not found."""

    pass


class ImageStorageError(SessionManagerError):
    """Raised when image storage operation fails."""

    pass


class SessionManager:
    """
    Session management service.

    Handles:
    - Creating and retrieving user sessions
    - Storing processed images
    - Retrieving session history
    - Cleaning up old sessions
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize session manager.

        Args:
            settings: Application settings (defaults to global settings)
        """
        self.settings = settings or get_settings()
        self.storage_path = Path(self.settings.upload_dir)
        self.processed_path = Path(self.settings.processed_dir)

        # Ensure directories exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)

    async def create_session(self, db: AsyncSession) -> Session:
        """
        Create a new user session.

        Args:
            db: Database session

        Returns:
            Created Session object

        Raises:
            SessionManagerError: If session creation fails
        """
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())

            # Create session object
            session = Session(
                session_id=session_id,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
            )

            # Add to database
            db.add(session)
            await db.commit()
            await db.refresh(session)

            return session

        except Exception as e:
            await db.rollback()
            raise SessionManagerError(f"Failed to create session: {str(e)}") from e

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
        update_access: bool = True,
        load_images: bool = False,
    ) -> Session:
        """
        Get session by ID.

        Args:
            db: Database session
            session_id: Session identifier
            update_access: Whether to update last_accessed timestamp
            load_images: Whether to eagerly load processed_images relationship

        Returns:
            Session object

        Raises:
            SessionNotFoundError: If session not found
            SessionManagerError: If retrieval fails
        """
        try:
            # Query session
            stmt = select(Session).where(Session.session_id == session_id)
            if load_images:
                stmt = stmt.options(selectinload(Session.processed_images))

            result = await db.execute(stmt)
            session = result.scalar_one_or_none()

            if session is None:
                raise SessionNotFoundError(f"Session '{session_id}' not found")

            # Update last accessed time
            if update_access:
                session.last_accessed = datetime.utcnow()
                await db.commit()
                # Don't refresh if we loaded images - it would clear the relationship
                if not load_images:
                    await db.refresh(session)

            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise SessionManagerError(f"Failed to get session: {str(e)}") from e

    async def get_session_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ProcessedImage]:
        """
        Get processing history for a session.

        Args:
            db: Database session
            session_id: Session identifier
            limit: Maximum number of results (None = all)
            offset: Number of results to skip

        Returns:
            List of ProcessedImage objects

        Raises:
            SessionNotFoundError: If session not found
            SessionManagerError: If retrieval fails
        """
        try:
            # Get session (validates it exists)
            session = await self.get_session(db, session_id, update_access=False)

            # Query processed images
            stmt = (
                select(ProcessedImage)
                .where(ProcessedImage.session_id == session.id)
                .order_by(ProcessedImage.created_at.desc())
                .offset(offset)
            )

            if limit is not None:
                stmt = stmt.limit(limit)

            result = await db.execute(stmt)
            images = list(result.scalars().all())

            return images

        except SessionNotFoundError:
            raise
        except Exception as e:
            raise SessionManagerError(
                f"Failed to get session history: {str(e)}"
            ) from e

    async def save_processed_image(
        self,
        db: AsyncSession,
        session_id: str,
        original_filename: str,
        model_id: str,
        original_path: str,
        processed_path: str,
        model_parameters: dict[str, Any] | None = None,
    ) -> ProcessedImage:
        """
        Save processed image metadata to database.

        Args:
            db: Database session
            session_id: Session identifier
            original_filename: Original filename
            model_id: Model used for processing
            original_path: Relative path to original image
            processed_path: Relative path to processed image
            model_parameters: Model parameters used (optional)

        Returns:
            Created ProcessedImage object

        Raises:
            SessionNotFoundError: If session not found
            SessionManagerError: If save fails
        """
        try:
            # Get session (validates it exists and updates access time)
            session = await self.get_session(db, session_id, update_access=True)

            # Convert parameters to JSON string if provided
            params_json = None
            if model_parameters:
                import json

                params_json = json.dumps(model_parameters)

            # Create processed image record
            processed_image = ProcessedImage(
                session_id=session.id,
                original_filename=original_filename,
                model_id=model_id,
                original_path=original_path,
                processed_path=processed_path,
                model_parameters=params_json,
                created_at=datetime.utcnow(),
            )

            # Add to database
            db.add(processed_image)
            await db.commit()
            await db.refresh(processed_image)

            return processed_image

        except SessionNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise SessionManagerError(
                f"Failed to save processed image: {str(e)}"
            ) from e

    async def cleanup_old_sessions(
        self, db: AsyncSession, hours: int = 24
    ) -> tuple[int, int]:
        """
        Clean up old sessions and their files.

        Removes sessions that haven't been accessed in the specified time period.

        Args:
            db: Database session
            hours: Number of hours of inactivity before cleanup (default: 24)

        Returns:
            Tuple of (sessions_deleted, files_deleted)

        Raises:
            SessionManagerError: If cleanup fails
        """
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Query old sessions with processed_images eagerly loaded
            stmt = (
                select(Session)
                .where(Session.last_accessed < cutoff_time)
                .options(selectinload(Session.processed_images))
            )
            result = await db.execute(stmt)
            old_sessions = list(result.scalars().all())

            sessions_deleted = 0
            files_deleted = 0

            for session in old_sessions:
                # Query images separately to ensure they're loaded
                img_stmt = select(ProcessedImage).where(
                    ProcessedImage.session_id == session.id
                )
                img_result = await db.execute(img_stmt)
                images = list(img_result.scalars().all())

                # Delete associated files
                for image in images:
                    # Delete original file
                    original_file = self.storage_path / image.original_path
                    if original_file.exists():
                        try:
                            original_file.unlink()
                            files_deleted += 1
                        except OSError:
                            # Log error but continue
                            pass

                    # Delete processed file
                    processed_file = self.processed_path / image.processed_path
                    if processed_file.exists():
                        try:
                            processed_file.unlink()
                            files_deleted += 1
                        except OSError:
                            # Log error but continue
                            pass

                # Delete session (cascade will delete processed_images)
                await db.delete(session)
                sessions_deleted += 1

            # Commit all deletions
            await db.commit()

            return (sessions_deleted, files_deleted)

        except Exception as e:
            await db.rollback()
            raise SessionManagerError(f"Failed to cleanup sessions: {str(e)}") from e

    async def delete_session(self, db: AsyncSession, session_id: str) -> int:
        """
        Delete a specific session and its files.

        Args:
            db: Database session
            session_id: Session identifier

        Returns:
            Number of files deleted

        Raises:
            SessionNotFoundError: If session not found
            SessionManagerError: If deletion fails
        """
        try:
            # Query session
            stmt = select(Session).where(Session.session_id == session_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()

            if session is None:
                raise SessionNotFoundError(f"Session '{session_id}' not found")

            # Query images separately to ensure they're loaded
            img_stmt = select(ProcessedImage).where(
                ProcessedImage.session_id == session.id
            )
            img_result = await db.execute(img_stmt)
            images = list(img_result.scalars().all())

            files_deleted = 0

            # Delete associated files
            for image in images:
                # Delete original file
                original_file = self.storage_path / image.original_path
                if original_file.exists():
                    try:
                        original_file.unlink()
                        files_deleted += 1
                    except OSError:
                        pass

                # Delete processed file
                processed_file = self.processed_path / image.processed_path
                if processed_file.exists():
                    try:
                        processed_file.unlink()
                        files_deleted += 1
                    except OSError:
                        pass

            # Delete session from database
            await db.delete(session)
            await db.commit()

            return files_deleted

        except SessionNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise SessionManagerError(f"Failed to delete session: {str(e)}") from e

    def get_storage_path_for_session(self, session_id: str) -> Path:
        """
        Get storage directory path for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to session's storage directory
        """
        session_dir = self.storage_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def get_processed_path_for_session(self, session_id: str) -> Path:
        """
        Get processed images directory path for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to session's processed directory
        """
        session_dir = self.processed_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
