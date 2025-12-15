"""
Image processing utilities.

This module provides utilities for image validation, conversion,
and preprocessing/postprocessing for AI model processing.
"""
import io
from pathlib import Path
from typing import BinaryIO

from PIL import Image
from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings, get_settings


class ImageValidationError(Exception):
    """Base exception for image validation errors."""

    pass


class ImageFormatError(ImageValidationError):
    """Raised when image format is invalid or unsupported."""

    pass


class ImageSizeError(ImageValidationError):
    """Raised when image size exceeds limits."""

    pass


def validate_image_format(file_extension: str, settings: Settings | None = None) -> bool:
    """
    Validate if file extension is an allowed image format.

    Args:
        file_extension: File extension (e.g., ".jpg", ".png")
        settings: Application settings (uses global if not provided)

    Returns:
        True if format is allowed

    Raises:
        ImageFormatError: If format is not allowed
    """
    settings = settings or get_settings()
    file_extension = file_extension.lower()

    if file_extension not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise ImageFormatError(
            f"File format '{file_extension}' not allowed. "
            f"Allowed formats: {allowed}"
        )

    return True


def validate_image_size(file_size: int, settings: Settings | None = None) -> bool:
    """
    Validate if file size is within limits.

    Args:
        file_size: File size in bytes
        settings: Application settings (uses global if not provided)

    Returns:
        True if size is acceptable

    Raises:
        ImageSizeError: If size exceeds limit
    """
    settings = settings or get_settings()

    if file_size > settings.max_upload_size:
        max_mb = settings.max_upload_size / (1024 * 1024)
        current_mb = file_size / (1024 * 1024)
        raise ImageSizeError(
            f"File size ({current_mb:.2f}MB) exceeds maximum allowed "
            f"size ({max_mb:.2f}MB)"
        )

    if file_size == 0:
        raise ImageSizeError("File is empty (0 bytes)")

    return True


async def validate_upload_file(
    upload_file: UploadFile, settings: Settings | None = None
) -> None:
    """
    Validate an uploaded file for image processing.

    Args:
        upload_file: FastAPI UploadFile object
        settings: Application settings (uses global if not provided)

    Raises:
        ImageFormatError: If format is not allowed
        ImageSizeError: If size exceeds limit
        ImageValidationError: For other validation errors
    """
    settings = settings or get_settings()

    # Check filename exists
    if not upload_file.filename:
        raise ImageValidationError("No filename provided")

    # Validate file extension
    file_extension = Path(upload_file.filename).suffix
    if not file_extension:
        raise ImageFormatError("File has no extension")

    validate_image_format(file_extension, settings)

    # Validate file size
    if upload_file.size:
        validate_image_size(upload_file.size, settings)


def pil_image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    Convert PIL Image to bytes.

    Args:
        image: PIL Image object
        format: Output format (PNG, JPEG, etc.)

    Returns:
        Image as bytes

    Raises:
        ImageValidationError: If conversion fails
    """
    try:
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        raise ImageValidationError(f"Failed to convert image to bytes: {str(e)}")


def bytes_to_pil_image(image_bytes: bytes) -> Image.Image:
    """
    Convert bytes to PIL Image.

    Args:
        image_bytes: Image data as bytes

    Returns:
        PIL Image object

    Raises:
        ImageValidationError: If image data is invalid
    """
    try:
        buffer = io.BytesIO(image_bytes)
        image = Image.open(buffer)
        # Verify it's a valid image by loading it
        image.load()
        return image
    except Exception as e:
        raise ImageValidationError(f"Invalid or corrupted image data: {str(e)}")


def validate_pil_image(image: Image.Image) -> bool:
    """
    Validate a PIL Image object.

    Args:
        image: PIL Image to validate

    Returns:
        True if image is valid

    Raises:
        ImageValidationError: If image is invalid
    """
    if image is None:
        raise ImageValidationError("Image is None")

    if not hasattr(image, "size") or not image.size:
        raise ImageValidationError("Image has no size information")

    width, height = image.size
    if width == 0 or height == 0:
        raise ImageValidationError(f"Image has invalid dimensions: {width}x{height}")

    # Check if image has a valid mode
    valid_modes = ["L", "RGB", "RGBA", "P", "CMYK"]
    if image.mode not in valid_modes:
        raise ImageValidationError(
            f"Image mode '{image.mode}' not supported. "
            f"Supported modes: {', '.join(valid_modes)}"
        )

    return True


def preprocess_image_for_model(image_bytes: bytes) -> bytes:
    """
    Preprocess image bytes before sending to model.

    Currently just validates and passes through, but can be extended
    for resizing, normalization, etc.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Preprocessed image bytes

    Raises:
        ImageValidationError: If image is invalid
    """
    # Validate image can be loaded
    image = bytes_to_pil_image(image_bytes)
    validate_pil_image(image)

    # For now, just return original bytes
    # Can add preprocessing steps here if needed
    return image_bytes


def postprocess_image_from_model(image_bytes: bytes) -> bytes:
    """
    Postprocess image bytes received from model.

    Validates the image and can apply additional processing if needed.

    Args:
        image_bytes: Raw image bytes from model

    Returns:
        Postprocessed image bytes

    Raises:
        ImageValidationError: If image is invalid
    """
    # Validate image can be loaded
    image = bytes_to_pil_image(image_bytes)
    validate_pil_image(image)

    # For now, just return original bytes
    # Can add postprocessing steps here if needed
    return image_bytes


async def read_upload_file_bytes(upload_file: UploadFile) -> bytes:
    """
    Read bytes from an uploaded file.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        File contents as bytes

    Raises:
        ImageValidationError: If file cannot be read
    """
    try:
        contents = await upload_file.read()
        await upload_file.seek(0)  # Reset file pointer
        return contents
    except Exception as e:
        raise ImageValidationError(f"Failed to read uploaded file: {str(e)}")


def get_image_info(image_bytes: bytes) -> dict[str, any]:
    """
    Get information about an image.

    Args:
        image_bytes: Image data as bytes

    Returns:
        Dictionary with image information (format, size, mode, dimensions)

    Raises:
        ImageValidationError: If image is invalid
    """
    image = bytes_to_pil_image(image_bytes)

    return {
        "format": image.format,
        "mode": image.mode,
        "width": image.size[0],
        "height": image.size[1],
        "size_bytes": len(image_bytes),
    }
