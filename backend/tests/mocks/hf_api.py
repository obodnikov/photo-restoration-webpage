"""Mock HuggingFace API for testing."""
import io
from typing import Any

from PIL import Image


class MockHFResponse:
    """Mock response from HuggingFace API."""

    def __init__(
        self,
        status_code: int,
        content: bytes | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize mock response.

        Args:
            status_code: HTTP status code
            content: Response content (bytes)
            json_data: JSON response data
            headers: Response headers
        """
        self.status_code = status_code
        self.content = content or b""
        self._json_data = json_data
        self.headers = headers or {}

    def json(self) -> dict[str, Any]:
        """Get JSON data from response."""
        if self._json_data is None:
            raise ValueError("No JSON data available")
        return self._json_data


def create_test_image_bytes(width: int = 100, height: int = 100, color: tuple = (255, 0, 0)) -> bytes:
    """
    Create test image bytes.

    Args:
        width: Image width
        height: Image height
        color: RGB color tuple

    Returns:
        Image bytes (JPEG format)
    """
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.read()


def mock_successful_response() -> MockHFResponse:
    """Create a mock successful response with a processed image."""
    # Create a test image (green to simulate processed image)
    image_bytes = create_test_image_bytes(200, 200, color=(0, 255, 0))

    return MockHFResponse(
        status_code=200,
        content=image_bytes,
        headers={"content-type": "image/jpeg"},
    )


def mock_rate_limit_response() -> MockHFResponse:
    """Create a mock rate limit (429) response."""
    return MockHFResponse(
        status_code=429,
        json_data={"error": "Rate limit exceeded"},
        headers={"content-type": "application/json"},
    )


def mock_model_loading_response(estimated_time: float = 20.0) -> MockHFResponse:
    """
    Create a mock model loading (503) response.

    Args:
        estimated_time: Estimated loading time in seconds

    Returns:
        Mock response
    """
    return MockHFResponse(
        status_code=503,
        json_data={
            "error": "Model is currently loading",
            "estimated_time": estimated_time,
        },
        headers={"content-type": "application/json"},
    )


def mock_model_not_found_response() -> MockHFResponse:
    """Create a mock model not found (404) response."""
    return MockHFResponse(
        status_code=404,
        json_data={"error": "Model not found"},
        headers={"content-type": "application/json"},
    )


def mock_server_error_response(status_code: int = 500) -> MockHFResponse:
    """
    Create a mock server error (5xx) response.

    Args:
        status_code: HTTP status code (500-599)

    Returns:
        Mock response
    """
    return MockHFResponse(
        status_code=status_code,
        json_data={"error": "Internal server error"},
        headers={"content-type": "application/json"},
    )


def mock_invalid_response() -> MockHFResponse:
    """Create a mock response with non-image content."""
    return MockHFResponse(
        status_code=200,
        content=b'{"error": "Not an image"}',
        headers={"content-type": "application/json"},
    )


def mock_timeout_exception():
    """Create a mock timeout exception."""
    import httpx

    return httpx.TimeoutException("Request timed out")


def mock_connection_error():
    """Create a mock connection error."""
    import httpx

    return httpx.ConnectError("Failed to connect")
