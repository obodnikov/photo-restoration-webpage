"""
HuggingFace Inference API service.

This module provides integration with HuggingFace's Inference API
for image processing tasks such as upscaling and enhancement.
"""
import asyncio
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings


class HFInferenceError(Exception):
    """Base exception for HuggingFace Inference API errors."""

    pass


class HFRateLimitError(HFInferenceError):
    """Raised when HuggingFace API rate limit is exceeded."""

    pass


class HFModelError(HFInferenceError):
    """Raised when there's an issue with the model."""

    pass


class HFTimeoutError(HFInferenceError):
    """Raised when HuggingFace API request times out."""

    pass


class HFInferenceService:
    """
    Service for interacting with HuggingFace Inference API.

    This service handles image processing requests to HuggingFace models,
    including proper error handling, timeout management, and response validation.
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize HuggingFace Inference Service.

        Args:
            settings: Application settings (uses global settings if not provided)
        """
        self.settings = settings or get_settings()
        self.api_key = self.settings.hf_api_key
        self.api_url = self.settings.hf_api_url
        self.timeout = self.settings.hf_api_timeout

        if not self.api_key:
            raise ValueError("HuggingFace API key is required")

    def _get_model_url(self, model_path: str) -> str:
        """
        Get the full API URL for a model.

        Args:
            model_path: HuggingFace model path (e.g., "caidas/swin2SR-classical-sr-x2-64")

        Returns:
            Full API URL for the model
        """
        return f"{self.api_url}/{model_path}"

    async def process_image(
        self,
        model_id: str,
        image_bytes: bytes,
        parameters: dict[str, Any] | None = None,
    ) -> bytes:
        """
        Process an image using a HuggingFace model.

        Args:
            model_id: Model ID from models configuration
            image_bytes: Raw image bytes to process
            parameters: Optional model-specific parameters

        Returns:
            Processed image as bytes

        Raises:
            HFModelError: If model not found or invalid
            HFRateLimitError: If rate limit exceeded
            HFTimeoutError: If request times out
            HFInferenceError: For other API errors
        """
        # Get model configuration
        model_config = self.settings.get_model_by_id(model_id)
        if not model_config:
            raise HFModelError(f"Model '{model_id}' not found in configuration")

        model_path = model_config["model"]
        model_url = self._get_model_url(model_path)

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/octet-stream",
        }

        # Prepare parameters if any
        request_params = parameters or model_config.get("parameters", {})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    model_url,
                    headers=headers,
                    content=image_bytes,
                    params=request_params if request_params else None,
                )

                # Handle different response status codes
                if response.status_code == 200:
                    # Validate response is actually an image
                    content_type = response.headers.get("content-type", "")
                    if not content_type.startswith("image/"):
                        # Some models return JSON with error
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("error", "Invalid response from model")
                            raise HFInferenceError(f"Model returned error: {error_msg}")
                        except Exception:
                            raise HFInferenceError("Model did not return a valid image")

                    return response.content

                elif response.status_code == 429:
                    # Rate limit exceeded
                    raise HFRateLimitError("HuggingFace API rate limit exceeded")

                elif response.status_code == 503:
                    # Model loading or unavailable
                    try:
                        error_data = response.json()
                        estimated_time = error_data.get("estimated_time", "unknown")
                        raise HFModelError(
                            f"Model is loading. Estimated time: {estimated_time}s"
                        )
                    except Exception:
                        raise HFModelError("Model is currently unavailable")

                elif response.status_code == 404:
                    raise HFModelError(f"Model '{model_path}' not found on HuggingFace")

                elif response.status_code >= 500:
                    # Server error
                    raise HFInferenceError(
                        f"HuggingFace API server error: {response.status_code}"
                    )

                else:
                    # Other errors
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", f"HTTP {response.status_code}")
                        raise HFInferenceError(f"HuggingFace API error: {error_msg}")
                    except Exception:
                        raise HFInferenceError(
                            f"HuggingFace API error: HTTP {response.status_code}"
                        )

        except httpx.TimeoutException:
            raise HFTimeoutError(
                f"Request to HuggingFace API timed out after {self.timeout}s"
            )
        except httpx.RequestError as e:
            raise HFInferenceError(f"Failed to connect to HuggingFace API: {str(e)}")

    async def check_model_status(self, model_id: str) -> dict[str, Any]:
        """
        Check if a model is available and loaded.

        Args:
            model_id: Model ID from models configuration

        Returns:
            Dictionary with model status information

        Raises:
            HFModelError: If model not found
        """
        model_config = self.settings.get_model_by_id(model_id)
        if not model_config:
            raise HFModelError(f"Model '{model_id}' not found in configuration")

        model_path = model_config["model"]
        model_url = self._get_model_url(model_path)

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send a small dummy request to check status
                response = await client.post(
                    model_url,
                    headers=headers,
                    content=b"",  # Empty content just to check status
                )

                if response.status_code == 503:
                    try:
                        data = response.json()
                        return {
                            "status": "loading",
                            "estimated_time": data.get("estimated_time", 0),
                        }
                    except Exception:
                        return {"status": "loading", "estimated_time": None}

                return {"status": "ready"}

        except Exception as e:
            return {"status": "error", "error": str(e)}


def get_hf_inference_service(settings: Settings | None = None) -> HFInferenceService:
    """
    Get HuggingFace Inference Service instance.

    This function provides a way to get the service that can be
    overridden in tests using dependency injection.

    Args:
        settings: Optional settings instance

    Returns:
        HFInferenceService instance
    """
    return HFInferenceService(settings)
