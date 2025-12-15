"""Tests for image processing utilities."""
import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import UploadFile
from PIL import Image

from app.core.config import Settings
from app.utils.image_processing import (
    ImageFormatError,
    ImageSizeError,
    ImageValidationError,
    bytes_to_pil_image,
    get_image_info,
    pil_image_to_bytes,
    postprocess_image_from_model,
    preprocess_image_for_model,
    read_upload_file_bytes,
    validate_image_format,
    validate_image_size,
    validate_pil_image,
    validate_upload_file,
)


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        max_upload_size=10 * 1024 * 1024,  # 10MB
        allowed_extensions={".jpg", ".jpeg", ".png"},
        hf_api_key="test-key",
        models_config=json.dumps([{"id": "test", "name": "Test", "model": "test/model", "category": "test", "description": "Test"}]),
    )


@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def valid_image_bytes(test_data_dir):
    """Get valid image bytes."""
    with open(test_data_dir / "old_photo_small.jpg", "rb") as f:
        return f.read()


@pytest.fixture
def corrupted_image_bytes(test_data_dir):
    """Get corrupted image bytes."""
    with open(test_data_dir / "corrupted_image.jpg", "rb") as f:
        return f.read()


class TestValidateImageFormat:
    """Tests for validate_image_format function."""

    def test_validate_allowed_jpg(self, test_settings):
        """Test that .jpg format is allowed."""
        assert validate_image_format(".jpg", test_settings) is True

    def test_validate_allowed_jpeg(self, test_settings):
        """Test that .jpeg format is allowed."""
        assert validate_image_format(".jpeg", test_settings) is True

    def test_validate_allowed_png(self, test_settings):
        """Test that .png format is allowed."""
        assert validate_image_format(".png", test_settings) is True

    def test_validate_case_insensitive(self, test_settings):
        """Test that validation is case-insensitive."""
        assert validate_image_format(".JPG", test_settings) is True
        assert validate_image_format(".PNG", test_settings) is True

    def test_validate_disallowed_txt(self, test_settings):
        """Test that .txt format is not allowed."""
        with pytest.raises(ImageFormatError, match="not allowed"):
            validate_image_format(".txt", test_settings)

    def test_validate_disallowed_bmp(self, test_settings):
        """Test that .bmp format is not allowed."""
        with pytest.raises(ImageFormatError, match="not allowed"):
            validate_image_format(".bmp", test_settings)

    def test_validate_disallowed_gif(self, test_settings):
        """Test that .gif format is not allowed."""
        with pytest.raises(ImageFormatError, match="not allowed"):
            validate_image_format(".gif", test_settings)


class TestValidateImageSize:
    """Tests for validate_image_size function."""

    def test_validate_size_within_limit(self, test_settings):
        """Test that size within limit is valid."""
        size = 5 * 1024 * 1024  # 5MB
        assert validate_image_size(size, test_settings) is True

    def test_validate_size_at_limit(self, test_settings):
        """Test that size exactly at limit is valid."""
        size = 10 * 1024 * 1024  # Exactly 10MB
        assert validate_image_size(size, test_settings) is True

    def test_validate_size_exceeds_limit(self, test_settings):
        """Test that size exceeding limit raises error."""
        size = 11 * 1024 * 1024  # 11MB
        with pytest.raises(ImageSizeError, match="exceeds maximum"):
            validate_image_size(size, test_settings)

    def test_validate_zero_size(self, test_settings):
        """Test that zero size raises error."""
        with pytest.raises(ImageSizeError, match="empty"):
            validate_image_size(0, test_settings)

    def test_validate_small_file(self, test_settings):
        """Test that small files are valid."""
        size = 1024  # 1KB
        assert validate_image_size(size, test_settings) is True


class TestValidateUploadFile:
    """Tests for validate_upload_file function."""

    @pytest.mark.asyncio
    async def test_validate_valid_upload(self, test_settings):
        """Test validation of valid upload file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.size = 1024 * 1024  # 1MB

        # Should not raise
        await validate_upload_file(mock_file, test_settings)

    @pytest.mark.asyncio
    async def test_validate_missing_filename(self, test_settings):
        """Test validation fails for missing filename."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None

        with pytest.raises(ImageValidationError, match="No filename"):
            await validate_upload_file(mock_file, test_settings)

    @pytest.mark.asyncio
    async def test_validate_no_extension(self, test_settings):
        """Test validation fails for file without extension."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test"
        mock_file.size = 1024

        with pytest.raises(ImageFormatError, match="no extension"):
            await validate_upload_file(mock_file, test_settings)

    @pytest.mark.asyncio
    async def test_validate_invalid_format(self, test_settings):
        """Test validation fails for invalid format."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.size = 1024

        with pytest.raises(ImageFormatError, match="not allowed"):
            await validate_upload_file(mock_file, test_settings)

    @pytest.mark.asyncio
    async def test_validate_oversized_file(self, test_settings):
        """Test validation fails for oversized file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.size = 11 * 1024 * 1024  # 11MB

        with pytest.raises(ImageSizeError, match="exceeds maximum"):
            await validate_upload_file(mock_file, test_settings)


class TestImageConversion:
    """Tests for image conversion functions."""

    def test_pil_to_bytes_png(self):
        """Test converting PIL Image to PNG bytes."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img_bytes = pil_image_to_bytes(img, format="PNG")

        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0

        # Verify can be loaded back
        loaded_img = bytes_to_pil_image(img_bytes)
        assert loaded_img.size == (100, 100)

    def test_pil_to_bytes_jpeg(self):
        """Test converting PIL Image to JPEG bytes."""
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        img_bytes = pil_image_to_bytes(img, format="JPEG")

        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0

    def test_bytes_to_pil_valid(self, valid_image_bytes):
        """Test converting valid bytes to PIL Image."""
        img = bytes_to_pil_image(valid_image_bytes)

        assert isinstance(img, Image.Image)
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_bytes_to_pil_corrupted(self, corrupted_image_bytes):
        """Test converting corrupted bytes raises error."""
        with pytest.raises(ImageValidationError, match="Invalid or corrupted"):
            bytes_to_pil_image(corrupted_image_bytes)

    def test_bytes_to_pil_empty(self):
        """Test converting empty bytes raises error."""
        with pytest.raises(ImageValidationError):
            bytes_to_pil_image(b"")

    def test_bytes_to_pil_invalid_data(self):
        """Test converting invalid data raises error."""
        with pytest.raises(ImageValidationError):
            bytes_to_pil_image(b"This is not an image")


class TestValidatePilImage:
    """Tests for validate_pil_image function."""

    def test_validate_valid_rgb_image(self):
        """Test validation of valid RGB image."""
        img = Image.new("RGB", (100, 100))
        assert validate_pil_image(img) is True

    def test_validate_valid_rgba_image(self):
        """Test validation of valid RGBA image."""
        img = Image.new("RGBA", (100, 100))
        assert validate_pil_image(img) is True

    def test_validate_valid_grayscale_image(self):
        """Test validation of valid grayscale image."""
        img = Image.new("L", (100, 100))
        assert validate_pil_image(img) is True

    def test_validate_none_image(self):
        """Test validation fails for None."""
        with pytest.raises(ImageValidationError, match="Image is None"):
            validate_pil_image(None)

    def test_validate_zero_width(self):
        """Test validation fails for zero width."""
        img = Image.new("RGB", (0, 100))
        with pytest.raises(ImageValidationError, match="invalid dimensions"):
            validate_pil_image(img)

    def test_validate_zero_height(self):
        """Test validation fails for zero height."""
        img = Image.new("RGB", (100, 0))
        with pytest.raises(ImageValidationError, match="invalid dimensions"):
            validate_pil_image(img)


class TestPreprocessPostprocess:
    """Tests for preprocessing and postprocessing functions."""

    def test_preprocess_valid_image(self, valid_image_bytes):
        """Test preprocessing valid image."""
        result = preprocess_image_for_model(valid_image_bytes)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_preprocess_invalid_image(self):
        """Test preprocessing invalid image raises error."""
        with pytest.raises(ImageValidationError):
            preprocess_image_for_model(b"not an image")

    def test_postprocess_valid_image(self, valid_image_bytes):
        """Test postprocessing valid image."""
        result = postprocess_image_from_model(valid_image_bytes)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_postprocess_invalid_image(self):
        """Test postprocessing invalid image raises error."""
        with pytest.raises(ImageValidationError):
            postprocess_image_from_model(b"not an image")


class TestReadUploadFileBytes:
    """Tests for read_upload_file_bytes function."""

    @pytest.mark.asyncio
    async def test_read_valid_upload(self, valid_image_bytes):
        """Test reading bytes from valid upload."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=valid_image_bytes)
        mock_file.seek = AsyncMock()

        result = await read_upload_file_bytes(mock_file)

        assert result == valid_image_bytes
        mock_file.read.assert_called_once()
        mock_file.seek.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_read_upload_error(self):
        """Test reading bytes when error occurs."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(side_effect=Exception("Read failed"))

        with pytest.raises(ImageValidationError, match="Failed to read"):
            await read_upload_file_bytes(mock_file)


class TestGetImageInfo:
    """Tests for get_image_info function."""

    def test_get_info_jpeg(self, valid_image_bytes):
        """Test getting info from JPEG image."""
        info = get_image_info(valid_image_bytes)

        assert "format" in info
        assert "mode" in info
        assert "width" in info
        assert "height" in info
        assert "size_bytes" in info

        assert info["width"] > 0
        assert info["height"] > 0
        assert info["size_bytes"] == len(valid_image_bytes)

    def test_get_info_png(self, test_data_dir):
        """Test getting info from PNG image."""
        with open(test_data_dir / "test_image.png", "rb") as f:
            png_bytes = f.read()

        info = get_image_info(png_bytes)

        assert info["width"] > 0
        assert info["height"] > 0
        assert info["size_bytes"] == len(png_bytes)

    def test_get_info_invalid_image(self):
        """Test getting info from invalid image raises error."""
        with pytest.raises(ImageValidationError):
            get_image_info(b"not an image")


class TestImageProcessingIntegration:
    """Integration tests for image processing workflow."""

    def test_full_conversion_cycle(self):
        """Test full cycle: PIL -> bytes -> PIL."""
        # Create original image
        original = Image.new("RGB", (200, 150), color=(128, 128, 255))

        # Convert to bytes
        img_bytes = pil_image_to_bytes(original, format="PNG")

        # Convert back to PIL
        result = bytes_to_pil_image(img_bytes)

        # Verify dimensions match
        assert result.size == original.size
        assert result.mode == original.mode

    def test_preprocessing_and_postprocessing_cycle(self, valid_image_bytes):
        """Test preprocessing and postprocessing cycle."""
        # Preprocess
        preprocessed = preprocess_image_for_model(valid_image_bytes)

        # Postprocess
        postprocessed = postprocess_image_from_model(preprocessed)

        # Verify result is valid
        img = bytes_to_pil_image(postprocessed)
        assert validate_pil_image(img)
