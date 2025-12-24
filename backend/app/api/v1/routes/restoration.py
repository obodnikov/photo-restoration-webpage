"""
Restoration API routes for image processing and history.

This module provides endpoints for:
- Image upload and restoration
- Processing history
- Image download and deletion
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.restoration import (
    DeleteResponse,
    HistoryItemResponse,
    HistoryResponse,
    ImageDetailResponse,
    RestoreResponse,
)
from app.core.config import get_settings
from app.core.security import get_current_user, get_current_user_validated
from app.db.database import get_db
from app.db.models import ProcessedImage
from app.services.hf_inference import (
    HFInferenceError,
    HFInferenceService,
    HFModelError,
    HFRateLimitError,
    HFTimeoutError,
)
from app.services.replicate_inference import (
    ReplicateInferenceError,
    ReplicateInferenceService,
    ReplicateModelError,
    ReplicateRateLimitError,
    ReplicateTimeoutError,
)
from app.services.session_manager import SessionManager, SessionNotFoundError
from app.utils.image_processing import (
    ImageFormatError,
    ImageSizeError,
    ImageValidationError,
    preprocess_image_for_model,
    read_upload_file_bytes,
    validate_upload_file,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/restore", tags=["Restoration"])

# Track concurrent uploads per session (in-memory for now)
# In production, use Redis or similar
_session_upload_counts: Dict[str, int] = {}
_upload_count_lock = asyncio.Lock()


async def check_concurrent_limit(session_id: str) -> None:
    """
    Check if session has reached concurrent upload limit.

    Args:
        session_id: Session identifier

    Raises:
        HTTPException 429: If limit exceeded
    """
    settings = get_settings()
    async with _upload_count_lock:
        current_count = _session_upload_counts.get(session_id, 0)
        if current_count >= settings.max_concurrent_uploads_per_session:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum {settings.max_concurrent_uploads_per_session} "
                f"concurrent uploads allowed per session",
            )
        _session_upload_counts[session_id] = current_count + 1


async def release_concurrent_slot(session_id: str) -> None:
    """Release concurrent upload slot for session."""
    async with _upload_count_lock:
        if session_id in _session_upload_counts:
            _session_upload_counts[session_id] -= 1
            if _session_upload_counts[session_id] <= 0:
                del _session_upload_counts[session_id]


@router.post(
    "",
    response_model=RestoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore/enhance image",
    description="""
    Upload and process an image using AI models for restoration, upscaling, or enhancement.

    **Processing Flow:**
    1. Upload image file (JPEG or PNG)
    2. Select AI model for processing
    3. Image is processed using HuggingFace or Replicate AI
    4. Receive URLs for original and processed images

    **Supported Models:**
    - `swin2sr-2x`: 2x upscaling (fast)
    - `swin2sr-4x`: 4x upscaling (fast)
    - `qwen-edit`: AI enhancement and restoration
    - `replicate-restore`: Advanced photo restoration (if configured)

    **File Requirements:**
    - Formats: JPEG, PNG
    - Max size: 10 MB (configurable)
    - Dimensions: No strict limits (model-dependent)

    **Authentication:**
    - Requires valid JWT token in Authorization header
    - Token obtained from `/api/v1/auth/login`

    **Rate Limits:**
    - Max 3 concurrent uploads per session

    **Example using cURL:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/restore" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
      -F "file=@photo.jpg" \\
      -F "model_id=swin2sr-2x"
    ```

    **Example Response:**
    ```json
    {
        "image_id": "abc123...",
        "original_url": "/uploads/abc123_photo.jpg",
        "processed_url": "/processed/abc123_photo.jpg",
        "model_used": "swin2sr-2x",
        "created_at": "2024-12-18T10:30:00Z"
    }
    ```
    """,
    responses={
        200: {
            "description": "Image processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "image_id": "550e8400-e29b-41d4-a716-446655440000",
                        "original_url": "/uploads/550e8400_old_photo.jpg",
                        "processed_url": "/processed/550e8400_old_photo.jpg",
                        "model_used": "swin2sr-2x",
                        "created_at": "2024-12-18T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid file format or model ID",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_format": {
                            "value": {"detail": "Only JPEG and PNG formats are supported"}
                        },
                        "invalid_model": {
                            "value": {"detail": "Unknown model: invalid-model-id"}
                        }
                    }
                }
            }
        },
        401: {
            "description": "Not authenticated or invalid token",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        413: {
            "description": "File too large",
            "content": {
                "application/json": {
                    "example": {"detail": "File size (15 MB) exceeds maximum allowed size (10 MB)"}
                }
            }
        },
        429: {
            "description": "Too many concurrent uploads",
            "content": {
                "application/json": {
                    "example": {"detail": "Maximum 3 concurrent uploads allowed per session"}
                }
            }
        },
        502: {
            "description": "AI model API error",
            "content": {
                "application/json": {
                    "example": {"detail": "HuggingFace API rate limit exceeded"}
                }
            }
        },
        504: {
            "description": "Processing timeout",
            "content": {
                "application/json": {
                    "example": {"detail": "Request to HuggingFace API timed out after 60s"}
                }
            }
        }
    }
)
async def restore_image(
    file: UploadFile = File(..., description="Image file to process"),
    model_id: str = Form(..., description="Model ID to use for processing"),
    parameters: str = Form(None, description="Optional model parameters (JSON string)"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_validated()),
) -> RestoreResponse:
    """
    Upload and restore an image.

    Process flow:
    1. Validate authentication and file
    2. Check concurrent upload limit
    3. Get session from token
    4. Process image with appropriate model provider (HuggingFace or Replicate)
    5. Save original and processed images
    6. Store metadata in database
    7. Return URLs

    Args:
        file: Uploaded image file
        model_id: ID of model to use
        db: Database session
        user: Current authenticated user

    Returns:
        RestoreResponse with URLs and metadata

    Raises:
        HTTPException 400: Invalid file or model
        HTTPException 401: Not authenticated
        HTTPException 413: File too large
        HTTPException 429: Concurrent upload limit exceeded
        HTTPException 502: HuggingFace API error
        HTTPException 503: Service unavailable
        HTTPException 504: Timeout
    """
    settings = get_settings()
    session_manager = SessionManager()

    # Get session_id from token
    session_id = user.get("session_id")
    if not session_id:
        logger.error(f"No session_id in token for user {user.get('sub')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing session information",
        )

    logger.debug(f"Restore request - User: {user.get('sub')}, Session: {session_id}, Model: {model_id}, File: {file.filename}")

    try:
        # Check concurrent upload limit
        logger.debug(f"Checking concurrent upload limit for session {session_id}")
        await check_concurrent_limit(session_id)
        logger.debug(f"Concurrent upload check passed for session {session_id}")

        # Validate uploaded file
        try:
            logger.debug(f"Validating upload file: {file.filename} ({file.content_type})")
            await validate_upload_file(file, settings)
            logger.debug(f"File validation passed for: {file.filename}")
        except ImageFormatError as e:
            logger.warning(f"Invalid image format: {file.filename} - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except ImageSizeError as e:
            logger.warning(f"Image size error: {file.filename} - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=str(e),
            )
        except ImageValidationError as e:
            logger.warning(f"Image validation error: {file.filename} - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Verify session exists
        try:
            await session_manager.get_session(db, session_id)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Read file bytes
        try:
            logger.debug(f"Reading file bytes: {file.filename}")
            image_bytes = await read_upload_file_bytes(file)
            logger.debug(f"Read {len(image_bytes)} bytes from {file.filename}")
        except ImageValidationError as e:
            logger.error(f"Failed to read file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file: {str(e)}",
            )

        # Preprocess image
        try:
            logger.debug(f"Preprocessing image for model")
            preprocessed_bytes = preprocess_image_for_model(image_bytes)
            logger.debug(f"Preprocessed image: {len(preprocessed_bytes)} bytes")
        except ImageValidationError as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image data: {str(e)}",
            )

        # Get model configuration to determine provider
        model_config = settings.get_model_by_id(model_id)
        if not model_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown model: {model_id}",
            )

        provider = model_config.get("provider", "huggingface")
        logger.info(
            f"Processing image with model {model_id} (provider: {provider}) "
            f"for session {session_id}"
        )

        # Parse parameters if provided
        parsed_parameters = None
        if parameters:
            try:
                import json
                parsed_parameters = json.loads(parameters)
                logger.info(f"Using user-provided parameters: {list(parsed_parameters.keys())}")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid parameters JSON: {str(e)}",
                )

        # Process image with appropriate provider
        try:
            if provider == "replicate":
                # Use Replicate service
                replicate_service = ReplicateInferenceService(settings)
                processed_bytes = await replicate_service.process_image(
                    model_id=model_id,
                    image_bytes=preprocessed_bytes,
                    parameters=parsed_parameters,
                )
            else:
                # Use HuggingFace service (default)
                hf_service = HFInferenceService(settings)
                processed_bytes = await hf_service.process_image(
                    model_id=model_id,
                    image_bytes=preprocessed_bytes,
                )
        except (HFModelError, ReplicateModelError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model error: {str(e)}",
            )
        except (HFRateLimitError, ReplicateRateLimitError) as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
                headers={"Retry-After": "60"},
            )
        except (HFTimeoutError, ReplicateTimeoutError) as e:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=str(e),
            )
        except (HFInferenceError, ReplicateInferenceError) as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Model service error: {str(e)}",
            )

        # Generate unique filename with original name preserved
        file_extension = Path(file.filename).suffix
        unique_id = str(uuid.uuid4())
        original_filename_stem = Path(file.filename).stem
        original_filename = f"{unique_id}_{original_filename_stem}{file_extension}"
        processed_filename = f"{unique_id}_{original_filename_stem}_processed{file_extension}"

        # Save original image
        original_dir = session_manager.get_storage_path_for_session(session_id)
        original_file_path = original_dir / original_filename
        with open(original_file_path, "wb") as f:
            f.write(image_bytes)

        # Save processed image
        processed_dir = session_manager.get_processed_path_for_session(session_id)
        processed_file_path = processed_dir / processed_filename
        with open(processed_file_path, "wb") as f:
            f.write(processed_bytes)

        # Save metadata to database
        original_relative_path = f"{session_id}/{original_filename}"
        processed_relative_path = f"{session_id}/{processed_filename}"

        processed_image = await session_manager.save_processed_image(
            db=db,
            session_id=session_id,
            original_filename=file.filename,
            model_id=model_id,
            original_path=original_relative_path,
            processed_path=processed_relative_path,
        )

        logger.info(
            f"Successfully processed image {processed_image.id} "
            f"for session {session_id}"
        )

        # Return response with URLs
        return RestoreResponse(
            id=processed_image.id,
            session_id=session_id,
            original_url=f"/uploads/{original_relative_path}",
            processed_url=f"/processed/{processed_relative_path}",
            model_id=model_id,
            original_filename=file.filename,
            timestamp=processed_image.created_at,
        )

    finally:
        # Always release concurrent slot
        await release_concurrent_slot(session_id)


@router.get(
    "/history",
    response_model=HistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get processing history",
    description="""
    Get list of ALL processed images for the current user across all sessions.

    Phase 2.4: Returns all images the user has ever processed, regardless of
    which session they were processed in. This allows users to access their
    complete history from any device.
    """,
)
async def get_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of items to skip (must be >= 0)"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_validated()),
) -> HistoryResponse:
    """
    Get processing history for current user (all sessions).

    Phase 2.4: Returns ALL images for the user across all sessions.

    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
        db: Database session
        user: Current authenticated user

    Returns:
        HistoryResponse with paginated list of processed images
    """
    from app.db.models import Session
    from sqlalchemy import func

    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user information",
        )

    from sqlalchemy.exc import SQLAlchemyError

    try:
        # Get ALL user's images across ALL sessions, ordered by most recent first
        # This ensures users can ONLY see their own images, not other users' images
        logger.debug(f"Querying history for user_id {user_id}")
        query = (
            select(ProcessedImage)
            .join(ProcessedImage.session)
            .where(Session.user_id == user_id)
            .order_by(ProcessedImage.created_at.desc())
        )

        # Get total count efficiently
        logger.debug(f"Counting total images for user_id {user_id}")
        count_query = (
            select(func.count(ProcessedImage.id))
            .join(ProcessedImage.session)
            .where(Session.user_id == user_id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        paginated_query = query.offset(offset).limit(limit)
        result = await db.execute(paginated_query)
        images = result.scalars().all()

        # Convert to response models
        items = [
            HistoryItemResponse(
                id=img.id,
                original_filename=img.original_filename,
                model_id=img.model_id,
                original_url=f"/uploads/{img.original_path}",
                processed_url=f"/processed/{img.processed_path}",
                created_at=img.created_at,
                model_parameters=img.model_parameters,
            )
            for img in images
        ]

        logger.debug(
            f"User {user['username']} (ID: {user_id}) retrieved {len(items)} images "
            f"from {total} total (offset: {offset}, limit: {limit})"
        )

        return HistoryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    except SQLAlchemyError as e:
        logger.error(
            f"Database error retrieving history for user {user_id}: {type(e).__name__}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while retrieving image history",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving history for user {user_id}: {type(e).__name__}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image history",
        )


@router.get(
    "/{image_id}",
    response_model=ImageDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get image details",
    description="Get detailed information about a processed image",
)
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_validated()),
) -> ImageDetailResponse:
    """
    Get details of a specific processed image.

    Args:
        image_id: Processed image ID
        db: Database session
        user: Current authenticated user

    Returns:
        ImageDetailResponse with full image metadata

    Raises:
        HTTPException 404: Image not found
        HTTPException 403: Not authorized to access this image
    """
    session_id = user.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing session information",
        )

    # Query image with session validation
    stmt = (
        select(ProcessedImage)
        .join(ProcessedImage.session)
        .where(
            ProcessedImage.id == image_id,
            ProcessedImage.session.has(session_id=session_id),
        )
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found or not accessible",
        )

    return ImageDetailResponse(
        id=image.id,
        session_id=image.session_id,
        original_filename=image.original_filename,
        model_id=image.model_id,
        original_url=f"/uploads/{image.original_path}",
        processed_url=f"/processed/{image.processed_path}",
        original_path=image.original_path,
        processed_path=image.processed_path,
        model_parameters=image.model_parameters,
        created_at=image.created_at,
    )


@router.get(
    "/{image_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download processed image",
    description="Download the processed image file",
)
async def download_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_validated()),
) -> FileResponse:
    """
    Download processed image.

    Args:
        image_id: Processed image ID
        db: Database session
        user: Current authenticated user

    Returns:
        FileResponse with processed image

    Raises:
        HTTPException 404: Image not found or file missing
        HTTPException 403: Not authorized to access this image
    """
    session_id = user.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing session information",
        )

    # Query image with session validation
    stmt = (
        select(ProcessedImage)
        .join(ProcessedImage.session)
        .where(
            ProcessedImage.id == image_id,
            ProcessedImage.session.has(session_id=session_id),
        )
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found or not accessible",
        )

    # Get file path
    settings = get_settings()
    file_path = Path(settings.processed_dir) / image.processed_path

    if not file_path.exists():
        logger.error(f"Processed file not found: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed image file not found",
        )

    # Return file with download headers
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=f"restored_{image.original_filename}",
        headers={"Content-Disposition": "attachment"},
    )


@router.delete(
    "/{image_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete processed image",
    description="Delete a processed image and its files",
)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_validated()),
) -> DeleteResponse:
    """
    Delete a processed image.

    Removes both database record and files.

    Args:
        image_id: Processed image ID
        db: Database session
        user: Current authenticated user

    Returns:
        DeleteResponse with deletion status

    Raises:
        HTTPException 404: Image not found
        HTTPException 403: Not authorized to delete this image
    """
    session_id = user.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing session information",
        )

    # Query image with session validation
    stmt = (
        select(ProcessedImage)
        .join(ProcessedImage.session)
        .where(
            ProcessedImage.id == image_id,
            ProcessedImage.session.has(session_id=session_id),
        )
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found or not accessible",
        )

    # Delete files
    settings = get_settings()
    files_deleted = 0

    # Delete original file
    original_path = Path(settings.upload_dir) / image.original_path
    if original_path.exists():
        try:
            original_path.unlink()
            files_deleted += 1
        except OSError as e:
            logger.warning(f"Failed to delete original file {original_path}: {e}")

    # Delete processed file
    processed_path = Path(settings.processed_dir) / image.processed_path
    if processed_path.exists():
        try:
            processed_path.unlink()
            files_deleted += 1
        except OSError as e:
            logger.warning(f"Failed to delete processed file {processed_path}: {e}")

    # Delete database record
    await db.delete(image)
    await db.commit()

    logger.info(f"Deleted image {image_id} and {files_deleted} files")

    return DeleteResponse(
        success=True,
        message=f"Image {image_id} deleted successfully",
        files_deleted=files_deleted,
    )
