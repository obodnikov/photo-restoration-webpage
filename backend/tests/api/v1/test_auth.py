"""Tests for authentication API endpoints."""
import time
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.models import Session as SessionModel


@pytest.mark.integration
@pytest.mark.auth
class TestLoginEndpoint:
    """Test POST /api/v1/auth/login endpoint."""

    def test_login_with_valid_credentials(self, client: TestClient, test_user_credentials):
        """Test login with valid credentials returns 200 and token."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data

        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_with_invalid_username(self, client: TestClient):
        """Test login with invalid username returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "wronguser",
                "password": "testpass",
                "remember_me": False
            }
        )

        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "Invalid credentials" in data["detail"] or "invalid" in data["detail"].lower()

    def test_login_with_invalid_password(self, client: TestClient, test_user_credentials):
        """Test login with invalid password returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": "wrongpassword",
                "remember_me": False
            }
        )

        assert response.status_code == 401

        data = response.json()
        assert "detail" in data

    def test_login_with_remember_me_true(self, client: TestClient, test_user_credentials):
        """Test login with remember_me=True returns token with 7 days expiration."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": True
            }
        )

        assert response.status_code == 200

        data = response.json()
        # 7 days = 7 * 24 * 60 * 60 = 604800 seconds
        expected_expiry = 7 * 24 * 60 * 60
        assert data["expires_in"] == expected_expiry

    def test_login_with_remember_me_false(self, client: TestClient, test_user_credentials):
        """Test login with remember_me=False returns token with 24h expiration."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
        )

        assert response.status_code == 200

        data = response.json()
        # Default is 1440 minutes = 24 hours = 86400 seconds
        expected_expiry = 1440 * 60
        assert data["expires_in"] == expected_expiry

    def test_login_missing_username(self, client: TestClient):
        """Test login with missing username returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "password": "testpass",
                "remember_me": False
            }
        )

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self, client: TestClient):
        """Test login with missing password returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "remember_me": False
            }
        )

        assert response.status_code == 422  # Validation error

    def test_login_empty_credentials(self, client: TestClient):
        """Test login with empty credentials returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "",
                "password": "",
                "remember_me": False
            }
        )

        # Could be 401 (invalid credentials) or 422 (validation error)
        # depending on validation rules
        assert response.status_code in [401, 422]

    def test_login_case_sensitive_username(self, client: TestClient):
        """Test login username is case-sensitive."""
        # Valid login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",
                "remember_me": False
            }
        )
        assert response.status_code == 200

        # Different case should fail
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "TestUser",
                "password": "testpass",
                "remember_me": False
            }
        )
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestValidateTokenEndpoint:
    """Test POST /api/v1/auth/validate endpoint."""

    def test_validate_with_valid_token(self, client: TestClient, auth_headers):
        """Test validate endpoint with valid token returns 200."""
        response = client.post(
            "/api/v1/auth/validate",
            headers=auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert "valid" in data
        assert "username" in data

        assert data["valid"] is True
        assert data["username"] == "testuser"

    def test_validate_with_expired_token(self, client: TestClient, expired_token):
        """Test validate endpoint with expired token returns 401."""
        # Ensure token is expired
        time.sleep(0.1)

        response = client.post(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_validate_with_malformed_token(self, client: TestClient):
        """Test validate endpoint with malformed token returns 401."""
        malformed_tokens = [
            "not.a.valid.token",
            "Bearer invalid",
            "invalid"
        ]

        for token in malformed_tokens:
            response = client.post(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 401, \
                f"Expected 401 for malformed token: {token}"

    def test_validate_without_token(self, client: TestClient):
        """Test validate endpoint without token returns 401 or 403."""
        response = client.post("/api/v1/auth/validate")

        # Could be 401 or 403 depending on implementation
        assert response.status_code in [401, 403]

    def test_validate_with_invalid_authorization_header(self, client: TestClient):
        """Test validate endpoint with invalid Authorization header format."""
        invalid_headers = [
            {"Authorization": "invalid"},
            {"Authorization": ""},
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Basic auth instead of Bearer
        ]

        for headers in invalid_headers:
            response = client.post(
                "/api/v1/auth/validate",
                headers=headers
            )

            assert response.status_code in [401, 403], \
                f"Expected 401/403 for invalid header: {headers}"


@pytest.mark.integration
@pytest.mark.auth
class TestGetMeEndpoint:
    """Test GET /api/v1/auth/me endpoint."""

    def test_get_me_with_valid_token(self, client: TestClient, auth_headers):
        """Test /api/v1/auth/me with valid token returns username."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert "username" in data
        assert data["username"] == "testuser"

    def test_get_me_without_token(self, client: TestClient):
        """Test /api/v1/auth/me without token returns 401 or 403."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code in [401, 403]

    def test_get_me_with_expired_token(self, client: TestClient, expired_token):
        """Test /api/v1/auth/me with expired token returns 401."""
        time.sleep(0.1)  # Ensure token is expired

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_get_me_with_invalid_token(self, client: TestClient):
        """Test /api/v1/auth/me with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_full_login_and_access_protected_endpoint(
        self, client: TestClient, test_user_credentials
    ):
        """Test full flow: login → get token → access protected endpoint."""
        # Step 1: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 2: Use token to access protected endpoint
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert me_response.status_code == 200
        assert me_response.json()["username"] == test_user_credentials["username"]

    def test_login_validate_get_me_flow(
        self, client: TestClient, test_user_credentials
    ):
        """Test flow: login → validate token → get user info."""
        # Step 1: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 2: Validate token
        validate_response = client.post(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert validate_response.status_code == 200
        assert validate_response.json()["valid"] is True

        # Step 3: Get user info
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert me_response.status_code == 200
        assert me_response.json()["username"] == test_user_credentials["username"]

    def test_multiple_logins_different_tokens(
        self, client: TestClient, test_user_credentials
    ):
        """Test multiple logins generate different tokens."""
        # Login twice
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
        )

        time.sleep(1.1)  # 1+ second delay to ensure different exp timestamps in JWT

        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        # Tokens should be different (different exp times)
        assert token1 != token2

        # Both tokens should work
        me_response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        me_response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert me_response1.status_code == 200
        assert me_response2.status_code == 200


@pytest.mark.security
@pytest.mark.auth
class TestAuthenticationSecurity:
    """Test authentication security scenarios."""

    def test_invalid_login_does_not_leak_user_existence(self, client: TestClient):
        """Test that error message doesn't reveal if username exists."""
        # Login with non-existent user
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistentuser",
                "password": "wrongpass",
                "remember_me": False
            }
        )

        # Login with existing user but wrong password
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpass",
                "remember_me": False
            }
        )

        # Both should return 401
        assert response1.status_code == 401
        assert response2.status_code == 401

        # Error messages should be generic (don't reveal if user exists)
        # Both should have similar error messages
        assert response1.json()["detail"] == response2.json()["detail"]

    def test_password_not_logged_in_errors(self, client: TestClient):
        """Test that password is not included in error responses."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword123",
                "remember_me": False
            }
        )

        # Password should not appear in response
        response_text = response.text.lower()
        assert "wrongpassword123" not in response_text
        assert "password" not in response_text or "invalid" in response_text

    def test_token_cannot_be_forged(self, client: TestClient):
        """Test that forged tokens are rejected."""
        from jose import jwt
        from app.core.config import get_settings

        settings = get_settings()

        # Create token with wrong secret
        forged_token = jwt.encode(
            {"sub": "testuser"},
            "wrong_secret_key_at_least_32_characters_long",
            algorithm=settings.algorithm
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {forged_token}"}
        )

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestLoginWithSessionMetadata:
    """Test login endpoint captures session metadata."""

    @pytest.mark.asyncio
    async def test_login_captures_user_agent_metadata(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test login captures User-Agent metadata in session."""
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            },
            headers={"User-Agent": user_agent}
        )

        assert response.status_code == 200

        # Get session from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        session = result.scalars().first()

        assert session is not None
        assert session.user_agent == user_agent
        assert session.browser is not None
        assert "Chrome" in session.browser
        assert session.os is not None
        assert "Mac OS X" in session.os
        assert session.device_type == "Desktop"

    @pytest.mark.asyncio
    async def test_login_captures_ip_address_from_x_forwarded_for(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test login captures IP from X-Forwarded-For header."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            },
            headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        )

        assert response.status_code == 200

        # Get session from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        session = result.scalars().first()

        assert session is not None
        assert session.ip_address == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_login_with_mobile_user_agent(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test login correctly identifies mobile devices."""
        mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            },
            headers={"User-Agent": mobile_ua}
        )

        assert response.status_code == 200

        # Get session from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        session = result.scalars().first()

        assert session is not None
        assert session.device_type == "Mobile"
        assert "iOS" in session.os or "iPhone" in session.os

    @pytest.mark.asyncio
    async def test_login_with_geolocation(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test login captures geolocation when GeoIP2 available."""
        with patch("app.utils.session_metadata.get_ip_location", return_value="San Francisco, CA, United States"):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": test_user_credentials["username"],
                    "password": test_user_credentials["password"],
                    "remember_me": False
                },
                headers={"X-Forwarded-For": "8.8.8.8"}
            )

        assert response.status_code == 200

        # Get session from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        session = result.scalars().first()

        assert session is not None
        assert session.location == "San Francisco, CA, United States"
        assert session.ip_address == "8.8.8.8"

    @pytest.mark.asyncio
    async def test_login_handles_missing_metadata_gracefully(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test login succeeds even without metadata headers."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            }
            # No User-Agent or X-Forwarded-For headers
        )

        assert response.status_code == 200

        # Get session from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        session = result.scalars().first()

        assert session is not None
        # Metadata fields should be None or have defaults
        # Session creation should still succeed

    @pytest.mark.asyncio
    async def test_login_handles_geolocation_failure_gracefully(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test login succeeds even if geolocation fails."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        with patch("app.utils.session_metadata.get_ip_location", return_value=None):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": test_user_credentials["username"],
                    "password": test_user_credentials["password"],
                    "remember_me": False
                },
                headers={
                    "User-Agent": user_agent,
                    "X-Forwarded-For": "192.168.1.1"
                }
            )

        assert response.status_code == 200

        # Get session from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        session = result.scalars().first()

        assert session is not None
        assert session.ip_address == "192.168.1.1"
        assert session.location is None  # GeoIP failed
        assert session.browser is not None  # But UA still parsed

    @pytest.mark.asyncio
    async def test_multiple_logins_create_separate_sessions_with_metadata(
        self, client: TestClient, test_user_credentials, test_db
    ):
        """Test multiple logins create separate sessions with different metadata."""
        # First login from Chrome
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
                "X-Forwarded-For": "203.0.113.1"
            }
        )

        assert response1.status_code == 200

        time.sleep(0.1)  # Small delay to ensure different timestamps

        # Second login from Firefox
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_credentials["username"],
                "password": test_user_credentials["password"],
                "remember_me": False
            },
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "X-Forwarded-For": "198.51.100.1"
            }
        )

        assert response2.status_code == 200

        # Get sessions from database
        result = await test_db.execute(
            select(SessionModel).where(SessionModel.user_id == 1).order_by(SessionModel.created_at.desc())
        )
        sessions = result.scalars().all()

        assert len(sessions) >= 2

        # Most recent session should be Firefox
        latest_session = sessions[0]
        assert "Firefox" in latest_session.browser
        assert latest_session.ip_address == "198.51.100.1"

        # Previous session should be Chrome
        previous_session = sessions[1]
        assert "Chrome" in previous_session.browser
        assert previous_session.ip_address == "203.0.113.1"
