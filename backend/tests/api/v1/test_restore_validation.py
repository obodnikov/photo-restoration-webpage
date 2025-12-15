"""
Tests for image restoration validation.

This module tests validation logic for the restoration API:
- File format validation
- File size validation
- Authentication requirements
"""
import io
from pathlib import Path

import pytest
from fastapi import status
from PIL import Image

from app.core.config import get_settings


@pytest.mark.asyncio
class TestRestoreValidation:
    """Test suite for restoration endpoint validation."""

    async def test_upload_valid_jpeg(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test uploading a valid JPEG image."""
        # Upload valid JPEG
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "original_url" in data
        assert "processed_url" in data
        assert data["model_id"] == "swin2sr-2x"

    async def test_upload_valid_png(
        self, auth_client, test_image_png, mock_hf_service
    ):
        """Test uploading a valid PNG image."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.png", test_image_png, "image/png")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["model_id"] == "swin2sr-2x"

    async def test_upload_unsupported_format_bmp(
        self, auth_client, test_image_bmp
    ):
        """Test uploading unsupported BMP format returns 400."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.bmp", test_image_bmp, "image/bmp")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "not allowed" in data["detail"].lower()

    async def test_upload_unsupported_format_txt(self, auth_client):
        """Test uploading text file returns 400."""
        text_content = b"This is not an image"

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.txt", text_content, "text/plain")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "not allowed" in data["detail"].lower()

    async def test_upload_exceeds_max_size(
        self, auth_client, test_image_large
    ):
        """Test uploading file exceeding MAX_UPLOAD_SIZE returns 413."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("large.jpg", test_image_large, "image/jpeg")},
        )

        # Should be 413 or 400 depending on implementation
        assert response.status_code in [
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_400_BAD_REQUEST,
        ]
        data = response.json()
        assert "size" in data["detail"].lower() or "large" in data["detail"].lower()

    async def test_upload_corrupted_image(
        self, auth_client
    ):
        """Test uploading corrupted image returns 400."""
        # Create corrupted JPEG (truncated)
        corrupted_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # Incomplete JPEG header

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("corrupted.jpg", corrupted_data, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "invalid" in data["detail"].lower() or "corrupted" in data["detail"].lower()

    async def test_upload_without_authentication(
        self, async_client, test_image_jpeg
    ):
        """Test uploading without auth token returns 401."""
        response = await async_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_upload_with_expired_token(
        self, async_client, test_image_jpeg, expired_token
    ):
        """Test uploading with expired token returns 401."""
        response = await async_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_upload_empty_file(self, auth_client):
        """Test uploading empty file returns 400."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "empty" in data["detail"].lower() or "0 bytes" in data["detail"].lower()

    async def test_upload_without_model_id(
        self, auth_client, test_image_jpeg
    ):
        """Test uploading without model_id returns 422."""
        response = await auth_client.post(
            "/api/v1/restore",
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        # FastAPI validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_upload_without_file(self, auth_client):
        """Test uploading without file returns 422."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
        )

        # FastAPI validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
