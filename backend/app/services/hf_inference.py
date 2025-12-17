"""
HuggingFace Inference API service.

This module provides integration with HuggingFace's Inference API
for image processing tasks such as upscaling and enhancement.
"""
import asyncio
import io
import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from huggingface_hub import InferenceClient
from PIL import Image

from app.core.config import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)


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
        self.timeout = self.settings.hf_api_timeout

        if not self.api_key:
            raise ValueError("HuggingFace API key is required")

        # Initialize InferenceClient
        # Note: Don't use provider="auto" as it causes StopIteration for some models
        # Let the library use the default HuggingFace Inference API
        self.client = InferenceClient(
            token=self.api_key,
        )

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
        model_category = model_config.get("category", "enhance")

        # Get model parameters
        request_params = parameters or model_config.get("parameters", {})

        logger.info(f"Processing image with model: {model_path}, category: {model_category}")

        try:
            # Validate input image (just for logging)
            input_image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"Input image: {input_image.format}, {input_image.size}, {input_image.mode}")

            # Helper function to call InferenceClient synchronously
            # Note: InferenceClient expects bytes, not PIL Image!
            def call_inference():
                try:
                    if model_category == "enhance":
                        # For enhancement models (like Qwen), use image_to_image with prompt
                        prompt = request_params.get("prompt", "enhance details, remove noise and artifacts")
                        logger.info(f"Using image_to_image with prompt: {prompt}")
                        return self.client.image_to_image(
                            image_bytes,  # Use bytes, not PIL Image
                            prompt=prompt,
                            model=model_path,
                        )
                    elif model_category == "upscale":
                        # For upscaling models (like Swin2SR), use image_to_image without prompt
                        logger.info(f"Using image_to_image for upscaling")
                        return self.client.image_to_image(
                            image_bytes,  # Use bytes, not PIL Image
                            model=model_path,
                        )
                    else:
                        # Default: try image_to_image
                        logger.info(f"Using image_to_image (default)")
                        return self.client.image_to_image(
                            image_bytes,  # Use bytes, not PIL Image
                            model=model_path,
                        )
                except StopIteration as e:
                    # Convert StopIteration to a regular exception
                    raise RuntimeError(f"Inference call failed with StopIteration: {e}")

            # Run inference in executor to avoid blocking async loop
            loop = asyncio.get_event_loop()
            output_image = await loop.run_in_executor(None, call_inference)

            # InferenceClient returns a PIL Image, convert to bytes
            if isinstance(output_image, Image.Image):
                output_bytes = io.BytesIO()
                output_format = input_image.format or "PNG"
                output_image.save(output_bytes, format=output_format)
                output_bytes.seek(0)
                logger.info(f"Successfully processed image with {model_path}")
                return output_bytes.read()
            else:
                # If it's already bytes, return as-is
                logger.info(f"Successfully processed image with {model_path} (returned as bytes)")
                return output_image

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"HuggingFace API error: {e}", exc_info=True)

            # Map common errors
            if "rate limit" in error_msg or "429" in error_msg:
                raise HFRateLimitError("HuggingFace API rate limit exceeded")
            elif "timeout" in error_msg:
                raise HFTimeoutError(
                    f"Request to HuggingFace API timed out after {self.timeout}s"
                )
            elif "not found" in error_msg or "404" in error_msg:
                raise HFModelError(f"Model '{model_path}' not found on HuggingFace")
            elif "loading" in error_msg or "503" in error_msg:
                raise HFModelError(f"Model '{model_path}' is still loading. Please try again in a moment.")
            elif "410" in error_msg or "gone" in error_msg:
                raise HFModelError(
                    f"Model '{model_path}' is not available via Inference API. "
                    f"This model may require a dedicated endpoint or local deployment."
                )
            elif "bad request" in error_msg or "400" in error_msg:
                # Bad request - likely model doesn't support this endpoint or parameters
                raise HFModelError(
                    f"Model '{model_path}' returned 400 Bad Request. "
                    f"This model may not support the image-to-image task via Inference API. "
                    f"Try a different model or check the model's documentation."
                )
            else:
                raise HFInferenceError(f"HuggingFace API error: {str(e)}")

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
