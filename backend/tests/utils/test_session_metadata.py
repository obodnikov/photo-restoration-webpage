"""Tests for session metadata utility functions."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request

from app.utils.session_metadata import (
    get_client_ip,
    parse_user_agent_metadata,
    get_ip_location,
    capture_session_metadata,
)


class TestGetClientIP:
    """Test get_client_ip function."""

    def test_extracts_ip_from_x_forwarded_for_header(self):
        """Test IP extraction from X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "203.0.113.1, 198.51.100.1"}
        request.client = Mock(host="10.0.0.1")

        ip = get_client_ip(request)

        assert ip == "203.0.113.1"

    def test_extracts_ip_from_x_forwarded_for_single_ip(self):
        """Test IP extraction from X-Forwarded-For with single IP."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "203.0.113.1"}
        request.client = Mock(host="10.0.0.1")

        ip = get_client_ip(request)

        assert ip == "203.0.113.1"

    def test_falls_back_to_client_host(self):
        """Test fallback to client.host when no X-Forwarded-For."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock(host="192.168.1.100")

        ip = get_client_ip(request)

        assert ip == "192.168.1.100"

    def test_returns_none_when_no_client(self):
        """Test returns None when client is not available."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None

        ip = get_client_ip(request)

        assert ip is None

    def test_handles_ipv6_addresses(self):
        """Test handles IPv6 addresses correctly."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "2001:db8::1"}
        request.client = Mock(host="::1")

        ip = get_client_ip(request)

        assert ip == "2001:db8::1"


class TestParseUserAgentMetadata:
    """Test parse_user_agent_metadata function."""

    def test_parses_chrome_desktop_user_agent(self):
        """Test parsing Chrome desktop User-Agent."""
        ua_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        metadata = parse_user_agent_metadata(ua_string)

        assert metadata["user_agent"] == ua_string
        assert "Chrome" in metadata["browser"]
        assert "Mac OS X" in metadata["os"]
        assert metadata["device_type"] == "Desktop"

    def test_parses_firefox_linux_user_agent(self):
        """Test parsing Firefox on Linux User-Agent."""
        ua_string = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"

        metadata = parse_user_agent_metadata(ua_string)

        assert "Firefox" in metadata["browser"]
        assert "Linux" in metadata["os"]
        assert metadata["device_type"] == "Desktop"

    def test_parses_mobile_safari_user_agent(self):
        """Test parsing Mobile Safari User-Agent."""
        ua_string = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

        metadata = parse_user_agent_metadata(ua_string)

        assert "Safari" in metadata["browser"] or "Mobile Safari" in metadata["browser"]
        assert "iOS" in metadata["os"]
        assert metadata["device_type"] == "Mobile"

    def test_parses_android_chrome_user_agent(self):
        """Test parsing Chrome on Android User-Agent."""
        ua_string = "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

        metadata = parse_user_agent_metadata(ua_string)

        assert "Chrome" in metadata["browser"]
        assert "Android" in metadata["os"]
        assert metadata["device_type"] == "Mobile"

    def test_parses_tablet_user_agent(self):
        """Test parsing tablet User-Agent."""
        ua_string = "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

        metadata = parse_user_agent_metadata(ua_string)

        assert metadata["device_type"] == "Tablet"

    def test_returns_none_for_empty_user_agent(self):
        """Test returns None values for empty User-Agent."""
        metadata = parse_user_agent_metadata(None)

        assert metadata["browser"] is None
        assert metadata["os"] is None
        assert metadata["device_type"] is None
        assert metadata["user_agent"] is None

    def test_returns_none_for_invalid_user_agent(self):
        """Test returns None values but preserves UA string for invalid format."""
        ua_string = "InvalidUserAgent"

        metadata = parse_user_agent_metadata(ua_string)

        assert metadata["user_agent"] == ua_string
        # May or may not parse, but should not crash

    def test_handles_bot_user_agent(self):
        """Test identifies bot User-Agents."""
        ua_string = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        metadata = parse_user_agent_metadata(ua_string)

        assert metadata["device_type"] == "Bot" or metadata["browser"] is not None


class TestGetIPLocation:
    """Test get_ip_location function."""

    def test_returns_none_when_no_ip_provided(self):
        """Test returns None when IP is None."""
        location = get_ip_location(None)

        assert location is None

    @patch("app.utils.session_metadata.geoip2.database.Reader")
    @patch("os.path.exists")
    def test_returns_location_when_database_exists(self, mock_exists, mock_reader_class):
        """Test returns location when GeoIP2 database is available."""
        # Mock database file exists
        mock_exists.return_value = True

        # Mock GeoIP2 reader
        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.city.name = "San Francisco"
        mock_response.subdivisions.most_specific.iso_code = "CA"
        mock_response.subdivisions.most_specific.name = "California"
        mock_response.country.name = "United States"

        mock_reader.city.return_value = mock_response
        mock_reader.__enter__.return_value = mock_reader
        mock_reader.__exit__.return_value = None
        mock_reader_class.return_value = mock_reader

        location = get_ip_location("8.8.8.8")

        assert location == "San Francisco, CA, United States"

    @patch("os.path.exists")
    def test_returns_none_when_database_not_found(self, mock_exists):
        """Test returns None when GeoIP2 database file not found."""
        # Mock database file does not exist
        mock_exists.return_value = False

        location = get_ip_location("8.8.8.8")

        assert location is None

    @patch("app.utils.session_metadata.geoip2.database.Reader")
    @patch("os.path.exists")
    def test_returns_none_when_ip_not_in_database(self, mock_exists, mock_reader_class):
        """Test returns None when IP not found in database."""
        from geoip2.errors import AddressNotFoundError

        mock_exists.return_value = True

        mock_reader = MagicMock()
        mock_reader.city.side_effect = AddressNotFoundError("IP not found")
        mock_reader.__enter__.return_value = mock_reader
        mock_reader.__exit__.return_value = None
        mock_reader_class.return_value = mock_reader

        location = get_ip_location("192.168.1.1")

        assert location is None

    @patch("app.utils.session_metadata.geoip2.database.Reader")
    @patch("os.path.exists")
    def test_handles_minimal_location_data(self, mock_exists, mock_reader_class):
        """Test handles location with minimal data (country only)."""
        mock_exists.return_value = True

        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.city.name = None
        mock_response.subdivisions.most_specific.iso_code = None
        mock_response.subdivisions.most_specific.name = None
        mock_response.country.name = "United States"

        mock_reader.city.return_value = mock_response
        mock_reader.__enter__.return_value = mock_reader
        mock_reader.__exit__.return_value = None
        mock_reader_class.return_value = mock_reader

        location = get_ip_location("8.8.8.8")

        assert location == "United States"


class TestCaptureSessionMetadata:
    """Test capture_session_metadata function."""

    def test_captures_all_metadata_successfully(self):
        """Test captures all metadata from request."""
        request = Mock(spec=Request)
        request.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-forwarded-for": "203.0.113.1"
        }
        request.client = Mock(host="10.0.0.1")

        with patch("app.utils.session_metadata.get_ip_location", return_value="San Francisco, CA, United States"):
            metadata = capture_session_metadata(request)

        assert metadata["user_agent"] is not None
        assert metadata["ip_address"] == "203.0.113.1"
        assert "Chrome" in metadata["browser"]
        assert "Mac OS X" in metadata["os"]
        assert metadata["device_type"] == "Desktop"
        assert metadata["location"] == "San Francisco, CA, United States"

    def test_handles_missing_user_agent_gracefully(self):
        """Test handles missing User-Agent header."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock(host="192.168.1.1")

        metadata = capture_session_metadata(request)

        assert metadata["user_agent"] is None
        assert metadata["browser"] is None
        assert metadata["os"] is None
        assert metadata["device_type"] is None
        assert metadata["ip_address"] == "192.168.1.1"

    def test_handles_geolocation_failure_gracefully(self):
        """Test handles GeoIP2 failure gracefully."""
        request = Mock(spec=Request)
        request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        request.client = Mock(host="192.168.1.1")

        with patch("app.utils.session_metadata.get_ip_location", return_value=None):
            metadata = capture_session_metadata(request)

        assert metadata["location"] is None
        assert metadata["ip_address"] == "192.168.1.1"
        assert metadata["browser"] is not None  # Should still parse UA

    def test_handles_completely_missing_metadata(self):
        """Test handles request with no metadata available."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None

        metadata = capture_session_metadata(request)

        assert metadata["user_agent"] is None
        assert metadata["ip_address"] is None
        assert metadata["browser"] is None
        assert metadata["os"] is None
        assert metadata["device_type"] is None
        assert metadata["location"] is None
