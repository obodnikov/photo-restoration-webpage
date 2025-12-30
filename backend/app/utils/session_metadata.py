"""
Session metadata utilities for capturing browser, device, and location information.

This module provides utilities to extract metadata from HTTP requests including:
- User-Agent parsing (browser, OS, device type)
- IP address extraction
- IP-based geolocation (optional, requires GeoIP2 database)
"""
import logging
from typing import Optional

from user_agents import parse as parse_user_agent
from fastapi import Request

# Optional GeoIP2 imports - available only if library is installed
try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request.

    Checks X-Forwarded-For header first (for reverse proxy scenarios),
    then falls back to direct client host.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address or None if not available
    """
    # Check X-Forwarded-For header (reverse proxy scenario)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return None


def parse_user_agent_metadata(user_agent_string: Optional[str]) -> dict:
    """
    Parse User-Agent string to extract browser, OS, and device information.

    Args:
        user_agent_string: Raw User-Agent header string

    Returns:
        Dictionary with keys: browser, os, device_type, user_agent
    """
    if not user_agent_string:
        return {
            "browser": None,
            "os": None,
            "device_type": None,
            "user_agent": None,
        }

    try:
        ua = parse_user_agent(user_agent_string)

        # Format browser name and version
        browser = None
        if ua.browser.family and ua.browser.family != "Other":
            browser = ua.browser.family
            if ua.browser.version_string:
                browser = f"{browser} {ua.browser.version_string}"

        # Format OS name and version
        os = None
        if ua.os.family and ua.os.family != "Other":
            os = ua.os.family
            if ua.os.version_string:
                os = f"{os} {ua.os.version_string}"

        # Determine device type
        device_type = None
        if ua.is_mobile:
            device_type = "Mobile"
        elif ua.is_tablet:
            device_type = "Tablet"
        elif ua.is_pc:
            device_type = "Desktop"
        elif ua.is_bot:
            device_type = "Bot"

        return {
            "browser": browser,
            "os": os,
            "device_type": device_type,
            "user_agent": user_agent_string,
        }
    except Exception as e:
        logger.warning(f"Failed to parse User-Agent string: {e}")
        return {
            "browser": None,
            "os": None,
            "device_type": None,
            "user_agent": user_agent_string,
        }


def get_ip_location(ip_address: Optional[str]) -> Optional[str]:
    """
    Get approximate geographic location from IP address using GeoIP2.

    Note: This requires a GeoIP2 database file. If not available, returns None.
    For free database, download GeoLite2-City.mmdb from MaxMind.

    Args:
        ip_address: IP address to lookup

    Returns:
        Location string (e.g., "San Francisco, CA, United States") or None
    """
    if not ip_address:
        logger.debug("No IP address provided for location lookup")
        return None

    if not GEOIP2_AVAILABLE:
        logger.warning(
            "geoip2 library not installed - IP geolocation disabled. "
            "Install with: pip install geoip2"
        )
        return None

    try:
        import os

        logger.debug(f"Attempting to locate IP address: {ip_address}")

        # Check for GeoIP2 database file
        # Try common locations (including Docker path /app)
        db_paths = [
            os.environ.get("GEOIP_DB_PATH"),  # Custom path from environment
            "/app/GeoLite2-City.mmdb",  # Docker container location
            "/var/lib/GeoIP/GeoLite2-City.mmdb",  # Default geoipupdate location (2025+)
            "/usr/share/GeoIP/GeoLite2-City.mmdb",  # Legacy system location
            "GeoLite2-City.mmdb",  # Current directory
            "backend/GeoLite2-City.mmdb",  # Development location
        ]

        # Filter out None values (from env var if not set)
        db_paths = [p for p in db_paths if p]

        logger.debug(f"Searching for GeoIP2 database in {len(db_paths)} locations...")

        db_path = None
        for path in db_paths:
            logger.debug(f"  Checking: {path}")
            if os.path.exists(path):
                db_path = path
                logger.debug(f"  ✓ Found database at: {path}")
                break
            else:
                logger.debug(f"  ✗ Not found: {path}")

        if not db_path:
            logger.warning(
                "GeoIP2 database not found - IP geolocation disabled. "
                "Session location will show as 'Unknown location'. "
                "To enable: Download GeoLite2-City.mmdb from MaxMind and place at /app/GeoLite2-City.mmdb "
                "See docs/GEOIP_SETUP.md for instructions."
            )
            return None

        # Perform IP lookup
        logger.debug(f"Opening GeoIP2 database: {db_path}")
        with geoip2.database.Reader(db_path) as reader:
            response = reader.city(ip_address)

            # Build location string
            location_parts = []

            if response.city.name:
                location_parts.append(response.city.name)

            # Add state/province for US/CA
            if response.subdivisions.most_specific.iso_code:
                location_parts.append(response.subdivisions.most_specific.iso_code)
            elif response.subdivisions.most_specific.name:
                location_parts.append(response.subdivisions.most_specific.name)

            if response.country.name:
                location_parts.append(response.country.name)

            location = ", ".join(location_parts) if location_parts else None

            if location:
                logger.debug(f"Successfully resolved IP {ip_address} to: {location}")
            else:
                logger.debug(f"IP {ip_address} found but no location data available")

            return location

    except geoip2.errors.AddressNotFoundError:
        logger.debug(f"IP address {ip_address} not found in GeoIP2 database (may be private/local IP)")
        return None
    except Exception as e:
        logger.warning(f"Failed to lookup IP location for {ip_address}: {e}")
        return None


def capture_session_metadata(request: Request) -> dict:
    """
    Capture complete session metadata from HTTP request.

    This is the main function to call during login to extract all
    session metadata in one go.

    Args:
        request: FastAPI Request object

    Returns:
        Dictionary with keys: user_agent, ip_address, browser, os, device_type, location
    """
    # Get User-Agent header
    user_agent_string = request.headers.get("user-agent")

    # Parse User-Agent
    ua_metadata = parse_user_agent_metadata(user_agent_string)

    # Get IP address
    ip_address = get_client_ip(request)

    # Get location from IP (optional, may return None)
    location = get_ip_location(ip_address)

    return {
        "user_agent": ua_metadata["user_agent"],
        "ip_address": ip_address,
        "browser": ua_metadata["browser"],
        "os": ua_metadata["os"],
        "device_type": ua_metadata["device_type"],
        "location": location,
    }
