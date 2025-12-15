"""Tests for HuggingFace Inference API service."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.services.hf_inference import (
    HFInferenceError,
    HFInferenceService,
    HFModelError,
    HFRateLimitError,
    HFTimeoutError,
)
from tests.mocks.hf_api import (
    create_test_image_bytes,
    mock_connection_error,
    mock_invalid_response,
    mock_model_loading_response,
    mock_model_not_found_response,
    mock_rate_limit_response,
    mock_server_error_response,
    mock_successful_response,
    mock_timeout_exception,
)


@pytest.fixture
def test_image_bytes():
    """Get test image bytes."""
    test_data_dir = Path(__file__).parent.parent / "data"
    with open(test_data_dir / "old_photo_small.jpg", "rb") as f:
        return f.read()


@pytest.fixture
def hf_service():
    """Create HFInferenceService with test settings."""
    settings = Settings(
        hf_api_key="test-api-key",
        hf_api_url="https://api-inference.huggingface.co/models",
        hf_api_timeout=60,
        models_config=json.dumps(
            [
                {
                    "id": "test-model",
                    "name": "Test Model",
                    "model": "test/model",
                    "category": "upscale",
                    "description": "Test",
                    "parameters": {"scale": 2},
                }
            ]
        ),
    )
    return HFInferenceService(settings)


class TestHFInferenceServiceInit:
    """Tests for HFInferenceService initialization."""

    def test_init_with_settings(self, hf_service):
        """Test service initialization with settings."""
        assert hf_service.api_key == "test-api-key"
        assert hf_service.api_url == "https://api-inference.huggingface.co/models"
        assert hf_service.timeout == 60

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises error."""
        settings = Settings(
            hf_api_key="",  # Empty API key
            models_config=json.dumps([{"id": "test", "name": "Test", "model": "test/model", "category": "test", "description": "Test"}]),
        )

        with pytest.raises(ValueError, match="HuggingFace API key is required"):
            HFInferenceService(settings)

    def test_get_model_url(self, hf_service):
        """Test model URL construction."""
        url = hf_service._get_model_url("test/model")
        assert url == "https://api-inference.huggingface.co/models/test/model"


class TestProcessImage:
    """Tests for process_image method."""

    @pytest.mark.asyncio
    async def test_process_image_success(self, hf_service, test_image_bytes):
        """Test successful image processing."""
        mock_response = mock_successful_response()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await hf_service.process_image("test-model", test_image_bytes)

            assert result == mock_response.content
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_process_image_with_invalid_model_id(self, hf_service, test_image_bytes):
        """Test processing with invalid model ID."""
        with pytest.raises(HFModelError, match="Model 'invalid-model' not found"):
            await hf_service.process_image("invalid-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_rate_limit(self, hf_service, test_image_bytes):
        """Test handling of rate limit (429) response."""
        mock_response = mock_rate_limit_response()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFRateLimitError, match="rate limit exceeded"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_model_loading(self, hf_service, test_image_bytes):
        """Test handling of model loading (503) response."""
        mock_response = mock_model_loading_response(estimated_time=20.0)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFModelError, match="loading|unavailable"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_model_not_found(self, hf_service, test_image_bytes):
        """Test handling of model not found (404) response."""
        mock_response = mock_model_not_found_response()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFModelError, match="not found on HuggingFace"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_server_error_500(self, hf_service, test_image_bytes):
        """Test handling of server error (500) response."""
        mock_response = mock_server_error_response(500)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFInferenceError, match="server error: 500"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_server_error_503(self, hf_service, test_image_bytes):
        """Test handling of server error (503) without loading info."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.json.side_effect = Exception("No JSON")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFModelError, match="currently unavailable"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_invalid_response(self, hf_service, test_image_bytes):
        """Test handling of non-image response."""
        mock_response = mock_invalid_response()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFInferenceError, match="did not return a valid image"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_timeout(self, hf_service, test_image_bytes):
        """Test handling of request timeout."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = mock_timeout_exception()

            with pytest.raises(HFTimeoutError, match="timed out"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_connection_error(self, hf_service, test_image_bytes):
        """Test handling of connection error."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = mock_connection_error()

            with pytest.raises(HFInferenceError, match="Failed to connect"):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_process_image_with_custom_parameters(self, hf_service, test_image_bytes):
        """Test processing with custom parameters."""
        mock_response = mock_successful_response()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            custom_params = {"scale": 4, "denoise": True}
            result = await hf_service.process_image(
                "test-model", test_image_bytes, parameters=custom_params
            )

            assert result == mock_response.content
            # Verify custom parameters were passed
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["params"] == custom_params


class TestCheckModelStatus:
    """Tests for check_model_status method."""

    @pytest.mark.asyncio
    async def test_check_model_status_ready(self, hf_service):
        """Test checking status of ready model."""
        mock_response = mock_successful_response()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            status = await hf_service.check_model_status("test-model")

            assert status["status"] == "ready"

    @pytest.mark.asyncio
    async def test_check_model_status_loading(self, hf_service):
        """Test checking status of loading model."""
        mock_response = mock_model_loading_response(estimated_time=15.0)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            status = await hf_service.check_model_status("test-model")

            assert status["status"] == "loading"
            assert status["estimated_time"] == 15.0

    @pytest.mark.asyncio
    async def test_check_model_status_invalid_model(self, hf_service):
        """Test checking status of invalid model."""
        with pytest.raises(HFModelError, match="not found in configuration"):
            await hf_service.check_model_status("invalid-model")

    @pytest.mark.asyncio
    async def test_check_model_status_error(self, hf_service):
        """Test checking status when error occurs."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection failed")

            status = await hf_service.check_model_status("test-model")

            assert status["status"] == "error"
            assert "Connection failed" in status["error"]


class TestResponseValidation:
    """Tests for response validation."""

    @pytest.mark.asyncio
    async def test_validates_content_type_header(self, hf_service, test_image_bytes):
        """Test that content-type header is validated."""
        # Create response with JSON content-type but image content
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"error": "Not an image"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(HFInferenceError):
                await hf_service.process_image("test-model", test_image_bytes)

    @pytest.mark.asyncio
    async def test_accepts_various_image_content_types(self, hf_service, test_image_bytes):
        """Test that various image content types are accepted."""
        image_bytes = create_test_image_bytes()

        for content_type in ["image/jpeg", "image/png", "image/webp"]:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": content_type}
            mock_response.content = image_bytes

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                result = await hf_service.process_image("test-model", test_image_bytes)
                assert result == image_bytes
