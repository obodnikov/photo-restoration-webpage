"""
Replicate API service.

This module provides integration with Replicate's API
for image processing tasks such as restoration, upscaling, and enhancement.
"""
import io
import logging
from typing import Any

import replicate
from PIL import Image

from app.core.config import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)


class ReplicateInferenceError(Exception):
    """Base exception for Replicate API errors."""

    pass


class ReplicateRateLimitError(ReplicateInferenceError):
    """Raised when Replicate API rate limit is exceeded."""

    pass


class ReplicateModelError(ReplicateInferenceError):
    """Raised when there's an issue with the model."""

    pass


class ReplicateTimeoutError(ReplicateInferenceError):
    """Raised when Replicate API request times out."""

    pass


class ReplicateInferenceService:
    """
    Service for interacting with Replicate API.

    This service handles image processing requests to Replicate models,
    including proper error handling, timeout management, and response validation.
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize Replicate Inference Service.

        Args:
            settings: Application settings (uses global settings if not provided)
        """
        self.settings = settings or get_settings()
        self.api_token = self.settings.replicate_api_token

        if not self.api_token:
            raise ValueError("Replicate API token is required")

        # Set Replicate API token
        replicate.Client(api_token=self.api_token)

    async def process_image(
        self,
        model_id: str,
        image_bytes: bytes,
        parameters: dict[str, Any] | None = None,
    ) -> bytes:
        """
        Process an image using a Replicate model.

        Args:
            model_id: Model ID from models configuration
            image_bytes: Raw image bytes to process
            parameters: Optional model-specific parameters

        Returns:
            Processed image as bytes

        Raises:
            ReplicateModelError: If model not found or invalid
            ReplicateRateLimitError: If rate limit exceeded
            ReplicateTimeoutError: If request times out
            ReplicateInferenceError: For other API errors
        """
        # Get model configuration
        model_config = self.settings.get_model_by_id(model_id)
        if not model_config:
            raise ReplicateModelError(f"Model '{model_id}' not found in configuration")

        model_path = model_config["model"]
        model_category = model_config.get("category", "restore")

        # Get model parameters
        request_params = parameters or model_config.get("parameters", {})

        logger.info(f"Processing image with Replicate model: {model_path}, category: {model_category}")

        try:
            # Validate input image (just for logging)
            input_image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"Input image: {input_image.format}, {input_image.size}, {input_image.mode}")

            # Convert image bytes to data URI for Replicate
            # Replicate accepts images as URLs or data URIs
            import base64
            image_data_uri = f"data:image/{input_image.format.lower()};base64,{base64.b64encode(image_bytes).decode()}"

            # Prepare input for Replicate
            # Different models use different parameter names for the input image
            # Common names: "image", "input_image", "img", "input"
            # Check if model config specifies the input parameter name
            input_param_name = model_config.get("input_param_name", "image")

            replicate_input = {input_param_name: image_data_uri}

            # Add any additional parameters from model configuration
            if request_params:
                replicate_input.update(request_params)

            logger.info(f"Calling Replicate model {model_path} with parameters: {list(replicate_input.keys())}")

            # Run the model
            # Note: replicate.run is synchronous, we're wrapping it for async compatibility
            output = replicate.run(
                model_path,
                input=replicate_input
            )

            logger.info(f"Replicate model returned output type: {type(output)}")

            # Process output based on type
            # Replicate models can return different output types
            if isinstance(output, str):
                # If output is a URL, download the image
                if output.startswith("http://") or output.startswith("https://"):
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(output)
                        response.raise_for_status()
                        output_bytes = response.content
                        logger.info(f"Downloaded output image from URL: {len(output_bytes)} bytes")
                        return output_bytes
                # If output is a data URI, decode it
                elif output.startswith("data:"):
                    # Extract base64 data from data URI
                    base64_data = output.split(",", 1)[1]
                    output_bytes = base64.b64decode(base64_data)
                    logger.info(f"Decoded output image from data URI: {len(output_bytes)} bytes")
                    return output_bytes
                else:
                    raise ReplicateInferenceError(f"Unexpected string output format: {output[:100]}")

            elif isinstance(output, list):
                # If output is a list, take the first item (common for multi-output models)
                if len(output) > 0:
                    first_output = output[0]
                    if isinstance(first_output, str):
                        # Recursively process the URL/data URI
                        if first_output.startswith("http://") or first_output.startswith("https://"):
                            import httpx
                            async with httpx.AsyncClient() as client:
                                response = await client.get(first_output)
                                response.raise_for_status()
                                output_bytes = response.content
                                logger.info(f"Downloaded output image from URL (list): {len(output_bytes)} bytes")
                                return output_bytes
                        elif first_output.startswith("data:"):
                            base64_data = first_output.split(",", 1)[1]
                            output_bytes = base64.b64decode(base64_data)
                            logger.info(f"Decoded output image from data URI (list): {len(output_bytes)} bytes")
                            return output_bytes
                    else:
                        raise ReplicateInferenceError(f"Unexpected list item type: {type(first_output)}")
                else:
                    raise ReplicateInferenceError("Model returned empty list")

            elif isinstance(output, bytes):
                # If output is already bytes, return as-is
                logger.info(f"Model returned bytes directly: {len(output)} bytes")
                return output

            elif hasattr(output, 'aread'):
                # If output is a FileOutput object (from replicate.helpers)
                # It has an aread() method to get bytes asynchronously
                output_bytes = await output.aread()
                logger.info(f"Read output from FileOutput object: {len(output_bytes)} bytes")
                return output_bytes

            else:
                raise ReplicateInferenceError(f"Unexpected output type: {type(output)}")

        except replicate.exceptions.ReplicateError as e:
            error_msg = str(e).lower()
            logger.error(f"Replicate API error: {e}", exc_info=True)

            # Map common errors
            if "rate limit" in error_msg or "429" in error_msg:
                raise ReplicateRateLimitError("Replicate API rate limit exceeded")
            elif "timeout" in error_msg:
                raise ReplicateTimeoutError("Request to Replicate API timed out")
            elif "not found" in error_msg or "404" in error_msg:
                raise ReplicateModelError(f"Model '{model_path}' not found on Replicate")
            elif "unauthorized" in error_msg or "401" in error_msg:
                raise ReplicateModelError("Invalid Replicate API token")
            else:
                raise ReplicateInferenceError(f"Replicate API error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error processing image with Replicate: {e}", exc_info=True)
            raise ReplicateInferenceError(f"Unexpected error: {str(e)}")


def get_replicate_inference_service(settings: Settings | None = None) -> ReplicateInferenceService:
    """
    Get Replicate Inference Service instance.

    This function provides a way to get the service that can be
    overridden in tests using dependency injection.

    Args:
        settings: Optional settings instance

    Returns:
        ReplicateInferenceService instance
    """
    return ReplicateInferenceService(settings)
