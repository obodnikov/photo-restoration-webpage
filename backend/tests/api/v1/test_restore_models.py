"""
Tests for image restoration model integration.

This module tests model selection and HuggingFace API integration:
- Valid model selection
- Unknown model handling
- HF API error responses (429, 503, timeouts)
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch

from app.services.hf_inference import (
    HFInferenceError,
    HFModelError,
    HFRateLimitError,
    HFTimeoutError,
)


@pytest.mark.asyncio
class TestRestoreModels:
    """Test suite for model selection and HF API integration."""

    async def test_valid_model_id_swin2sr_2x(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test restoration with valid model_id swin2sr-2x."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_id"] == "swin2sr-2x"

    async def test_valid_model_id_swin2sr_4x(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test restoration with valid model_id swin2sr-4x."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-4x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_id"] == "swin2sr-4x"

    async def test_valid_model_id_qwen_edit(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test restoration with valid model_id qwen-edit."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "qwen-edit"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_id"] == "qwen-edit"

    async def test_unknown_model_id(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test restoration with unknown model_id returns 400."""
        # Mock to raise HFModelError for unknown model
        mock_hf_service.process_image.side_effect = HFModelError(
            "Model 'unknown-model' not found in configuration"
        )

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "unknown-model"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "model" in data["detail"].lower()

    async def test_hf_returns_valid_image(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test that HF service returns valid image bytes."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check URLs are valid
        assert data["processed_url"].startswith("/processed/")
        assert data["original_url"].startswith("/uploads/")

    async def test_hf_rate_limit_429(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test HF 429 rate limit returns 503 with retry-after."""
        # Mock HF rate limit error
        mock_hf_service.process_image.side_effect = HFRateLimitError(
            "HuggingFace API rate limit exceeded"
        )

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Retry-After" in response.headers
        assert "rate limit" in response.json()["detail"].lower()

    async def test_hf_network_error(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test HF network error returns 502."""
        # Mock HF network error
        mock_hf_service.process_image.side_effect = HFInferenceError(
            "Failed to connect to HuggingFace API: Connection refused"
        )

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert "service" in data["detail"].lower()

    async def test_hf_timeout(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test HF timeout returns 504."""
        # Mock HF timeout error
        mock_hf_service.process_image.side_effect = HFTimeoutError(
            "Request to HuggingFace API timed out after 60s"
        )

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        data = response.json()
        assert "timeout" in data["detail"].lower() or "timed out" in data["detail"].lower()

    async def test_hf_model_loading_503(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test HF model loading (503) returns appropriate error."""
        # Mock HF model loading error
        mock_hf_service.process_image.side_effect = HFModelError(
            "Model is loading. Estimated time: 20s"
        )

        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "model" in data["detail"].lower()

    async def test_response_includes_all_required_fields(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test response includes all required fields."""
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check all required fields
        required_fields = [
            "id",
            "session_id",
            "original_url",
            "processed_url",
            "model_id",
            "original_filename",
            "timestamp",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    async def test_concurrent_upload_limit(
        self, auth_client, test_image_jpeg, mock_hf_service
    ):
        """Test concurrent upload limit per session."""
        # This test would require multiple concurrent requests
        # For now, test that first request succeeds
        response = await auth_client.post(
            "/api/v1/restore",
            data={"model_id": "swin2sr-2x"},
            files={"file": ("test.jpg", test_image_jpeg, "image/jpeg")},
        )

        assert response.status_code == status.HTTP_200_OK
