"""
Tests for complete restoration workflow integration.

This module tests end-to-end restoration flows:
- Upload → process → save → return
- File storage validation
- Database metadata storage
- History retrieval
- Download functionality
- Deletion
- User isolation
"""
import json
from pathlib import Path

import pytest
from fastapi import status


@pytest.mark.asyncio
class TestRestoreIntegration:
    """Test suite for full restoration workflow."""

    async def test_full_restore_flow(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test complete restore flow: upload → process → save → return."""
        # Upload and process image
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test_photo.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "original_url" in data
        assert "processed_url" in data
        assert data["model_id"] == "swin2sr-2x"
        assert data["original_filename"] == "test_photo.jpg"

        image_id = data["id"]

        # Verify files were saved
        upload_dir = Path(test_settings.upload_dir)
        processed_dir = Path(test_settings.processed_dir)

        # Check original file exists
        original_path = data["original_url"].replace("/uploads/", "")
        original_file = upload_dir / original_path
        assert original_file.exists()

        # Check processed file exists
        processed_path = data["processed_url"].replace("/processed/", "")
        processed_file = processed_dir / processed_path
        assert processed_file.exists()

        # Verify both files have content
        assert original_file.stat().st_size > 0
        assert processed_file.stat().st_size > 0

    async def test_original_saved_to_upload_dir(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test original image is saved to UPLOAD_DIR."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("original.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check file in upload directory
        upload_dir = Path(test_settings.upload_dir)
        original_path = data["original_url"].replace("/uploads/", "")
        original_file = upload_dir / original_path

        assert original_file.exists()
        assert original_file.parent.name == data["session_id"]

    async def test_processed_saved_to_processed_dir(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test processed image is saved to PROCESSED_DIR."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check file in processed directory
        processed_dir = Path(test_settings.processed_dir)
        processed_path = data["processed_url"].replace("/processed/", "")
        processed_file = processed_dir / processed_path

        assert processed_file.exists()
        assert processed_file.parent.name == data["session_id"]

    async def test_metadata_stored_in_database(
        self, auth_client, test_image_jpeg, mock_hf_service, async_session
    ):
        """Test metadata is correctly stored in database."""
        # Process image
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("metadata_test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Query database directly
        from app.db.models import ProcessedImage
        from sqlalchemy import select

        stmt = select(ProcessedImage).where(ProcessedImage.id == data["id"])
        result = await async_session.execute(stmt)
        db_image = result.scalar_one()

        assert db_image is not None
        assert db_image.original_filename == "metadata_test.jpg"
        assert db_image.model_id == "swin2sr-2x"
        assert db_image.original_path is not None
        assert db_image.processed_path is not None

    async def test_get_history_returns_processed_images(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test GET /restore/history returns user's processed images."""
        # Process multiple images
        for i in range(3):
            await auth_client.post(
                "/api/v1/restore",
                data={"model_id": "swin2sr-2x"},
                files={"file": (f"test_{i}.jpg", test_image_jpeg, "image/jpeg")},
            )

        # Get history
        response = await auth_client.get("/api/v1/restore/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3
        assert data["total"] == 3

    async def test_get_history_pagination(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test history endpoint pagination works correctly."""
        # Process 5 images
        for i in range(5):
            await auth_client.post(
                "/api/v1/restore",
                data={"model_id": "swin2sr-2x"},
                files={"file": (f"test_{i}.jpg", test_image_jpeg, "image/jpeg")},
            )

        # Get first page (limit=2)
        response = await auth_client.get("/api/v1/restore/history?limit=2&offset=0")
        data = response.json()

        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Get second page
        response = await auth_client.get("/api/v1/restore/history?limit=2&offset=2")
        data = response.json()

        assert len(data["items"]) == 2
        assert data["total"] == 5

    async def test_get_specific_image(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test GET /restore/{image_id} returns specific image."""
        # Process image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("specific.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()
        image_id = upload_data["id"]

        # Get specific image
        response = await auth_client.get(f"/api/v1/restore/{image_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == image_id
        assert data["original_filename"] == "specific.jpg"
        assert data["model_id"] == "swin2sr-2x"

    async def test_download_processed_image(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test GET /restore/{image_id}/download downloads image."""
        # Process image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("download_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()
        image_id = upload_data["id"]

        # Download image
        response = await auth_client.get(f"/api/v1/restore/{image_id}/download")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("image/")
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]

        # Check file content is not empty
        content = response.content
        assert len(content) > 0

    async def test_delete_image_removes_files_and_record(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test DELETE /restore/{image_id} deletes files and database record."""
        # Process image
        upload_response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("delete_test.jpg", test_image_jpeg, "image/jpeg")},
        )
        upload_data = upload_response.json()
        image_id = upload_data["id"]

        # Get file paths before deletion
        original_path = Path(test_settings.upload_dir) / upload_data["original_url"].replace(
            "/uploads/", ""
        )
        processed_path = Path(test_settings.processed_dir) / upload_data[
            "processed_url"
        ].replace("/processed/", "")

        # Verify files exist before deletion
        assert original_path.exists()
        assert processed_path.exists()

        # Delete image
        delete_response = await auth_client.delete(f"/api/v1/restore/{image_id}")

        assert delete_response.status_code == status.HTTP_200_OK
        delete_data = delete_response.json()
        assert delete_data["success"] is True
        assert delete_data["files_deleted"] == 2

        # Verify files are deleted
        assert not original_path.exists()
        assert not processed_path.exists()

        # Verify can't get deleted image
        get_response = await auth_client.get(f"/api/v1/restore/{image_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_nonexistent_image(self, auth_client):
        """Test deleting non-existent image returns 404."""
        response = await auth_client.delete("/api/v1/restore/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_user_isolation_cannot_access_other_user_images(
        self, async_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test users cannot access images from other sessions."""
        # Create first user session and upload image
        login1_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme", "remember_me": False},
        )
        token1 = login1_response.json()["access_token"]

        upload_response = await async_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("user1.jpg", test_image_jpeg, "image/jpeg")},
            headers={"Authorization": f"Bearer {token1}"},
        )
        image_id = upload_response.json()["id"]

        # Create second user session (new login = new session)
        login2_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme", "remember_me": False},
        )
        token2 = login2_response.json()["access_token"]

        # Try to access first user's image with second session
        get_response = await async_client.get(
            f"/api/v1/restore/{image_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert get_response.status_code == status.HTTP_404_NOT_FOUND

        # Try to delete first user's image with second session
        delete_response = await async_client.delete(
            f"/api/v1/restore/{image_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert delete_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_filename_preserved_with_uuid(
        self, auth_client, test_image_jpeg, mock_hf_service, test_settings
    ):
        """Test that original filename is preserved with UUID prefix."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("my_family_photo.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check filename in database
        assert data["original_filename"] == "my_family_photo.jpg"

        # Check actual file has UUID prefix
        original_path = data["original_url"].replace("/uploads/", "")
        filename = Path(original_path).name
        # Should be like: uuid_my_family_photo.jpg
        assert "_my_family_photo.jpg" in filename
        assert len(filename) > len("my_family_photo.jpg")  # UUID added

    async def test_history_ordered_by_created_at_desc(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test history is ordered by created_at in descending order."""
        # Upload images with small delay
        import asyncio

        image_ids = []
        for i in range(3):
            response = await auth_client.post(
                "/api/v1/restore",
                data={"model_id": "swin2sr-2x"},
                files={"file": (f"img_{i}.jpg", test_image_jpeg, "image/jpeg")},
            )
            image_ids.append(response.json()["id"])
            await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

        # Get history
        response = await auth_client.get("/api/v1/restore/history")
        data = response.json()

        # Most recent should be first
        assert data["items"][0]["id"] == image_ids[2]
        assert data["items"][2]["id"] == image_ids[0]
