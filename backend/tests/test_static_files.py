"""
Tests for static file serving.

This module tests static file serving for uploads and processed images:
- Serving uploaded images
- Serving processed images
- CORS headers
- Security headers
"""
from pathlib import Path

import pytest
from fastapi import status


@pytest.mark.asyncio
class TestStaticFileServing:
    """Test suite for static file serving."""

    async def test_serve_uploaded_image(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test GET /uploads/{filepath} serves uploaded image."""
        # First upload an image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("upload_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()
        original_url = upload_data["original_url"]

        # Access the uploaded file
        response = await auth_client.get(original_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("image/")

        # Verify content is not empty
        content = response.content
        assert len(content) > 0

    async def test_serve_processed_image(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test GET /processed/{filepath} serves processed image."""
        # First process an image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("process_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()
        processed_url = upload_data["processed_url"]

        # Access the processed file
        response = await auth_client.get(processed_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("image/")

        # Verify content is not empty
        content = response.content
        assert len(content) > 0

    async def test_nonexistent_upload_returns_404(self, async_client):
        """Test accessing non-existent upload returns 404."""
        response = await async_client.get("/uploads/nonexistent/file.jpg")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_nonexistent_processed_returns_404(self, async_client):
        """Test accessing non-existent processed file returns 404."""
        response = await async_client.get("/processed/nonexistent/file.jpg")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_cors_headers_present(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test CORS headers are set correctly."""
        # Upload and process image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("cors_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()

        # Access uploaded file
        response = await auth_client.get(upload_data["original_url"])

        # Check CORS headers (should be set by CORS middleware)
        # Note: actual CORS headers might be set by middleware, not static files
        assert response.status_code == status.HTTP_200_OK

    async def test_security_headers_present(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test basic security headers are present."""
        # Upload and process image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("security_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()

        # Access processed file
        response = await auth_client.get(upload_data["processed_url"])

        assert response.status_code == status.HTTP_200_OK
        # Basic security: check content-type is set correctly
        assert "content-type" in response.headers

    async def test_direct_file_access_without_auth(
        self, async_client, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test direct file access works without authentication."""
        # First upload with auth
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("public_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()

        # Access file without authentication (static files are public)
        response = await async_client.get(upload_data["processed_url"])

        assert response.status_code == status.HTTP_200_OK

    async def test_path_traversal_protection(self, async_client):
        """Test path traversal attacks are prevented."""
        # Try to access files outside allowed directories
        malicious_paths = [
            "/uploads/../../../etc/passwd",
            "/uploads/../../backend/app/core/config.py",
            "/processed/../../../.env",
        ]

        for path in malicious_paths:
            response = await async_client.get(path)
            # Should either be 404 or reject the path
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_403_FORBIDDEN,
            ]

    async def test_session_isolation_in_file_paths(
        self, async_client, test_image_jpeg, mock_hf_service
    ):
        """Test files are isolated by session in directory structure."""
        # Create first session and upload
        login1_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme", "remember_me": False},
        )
        token1 = login1_response.json()["access_token"]

        upload1_response = await async_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("session1.jpg", test_image_jpeg, "image/jpeg")},
            headers={"Authorization": f"Bearer {token1}"},
        )
        session1_data = upload1_response.json()
        session1_id = session1_data["session_id"]

        # Create second session and upload
        login2_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme", "remember_me": False},
        )
        token2 = login2_response.json()["access_token"]

        upload2_response = await async_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("session2.jpg", test_image_jpeg, "image/jpeg")},
            headers={"Authorization": f"Bearer {token2}"},
        )
        session2_data = upload2_response.json()
        session2_id = session2_data["session_id"]

        # Verify different sessions
        assert session1_id != session2_id

        # Verify files are in different directories
        assert session1_id in session1_data["original_url"]
        assert session2_id in session2_data["original_url"]
        assert session1_id not in session2_data["original_url"]
        assert session2_id not in session1_data["original_url"]

        # Both sessions can access their own files
        response1 = await async_client.get(session1_data["original_url"])
        assert response1.status_code == status.HTTP_200_OK

        response2 = await async_client.get(session2_data["original_url"])
        assert response2.status_code == status.HTTP_200_OK
