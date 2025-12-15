"""Tests for security utilities (JWT, password hashing)."""
from datetime import timedelta, datetime
import time

import pytest
from jose import jwt, JWTError

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_user,
)
from app.core.config import get_settings


@pytest.mark.unit
@pytest.mark.security
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_get_password_hash_creates_valid_hash(self):
        """Test get_password_hash() creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Bcrypt hashes start with $2b$ and are 60 characters
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_get_password_hash_different_each_time(self):
        """Test get_password_hash() creates different hashes for same password."""
        password = "test_password_123"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_verify_password_with_matching_password(self, test_user_hashed_password):
        """Test verify_password() returns True for matching password."""
        result = verify_password("testpass", test_user_hashed_password)
        assert result is True

    def test_verify_password_with_wrong_password(self, test_user_hashed_password):
        """Test verify_password() returns False for wrong password."""
        result = verify_password("wrongpassword", test_user_hashed_password)
        assert result is False

    def test_verify_password_case_sensitive(self):
        """Test password verification is case-sensitive."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("TestPassword123", hashed) is True
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False

    def test_verify_password_with_empty_password(self):
        """Test verify_password() handles empty password."""
        hashed = get_password_hash("somepassword")

        result = verify_password("", hashed)
        assert result is False


@pytest.mark.unit
@pytest.mark.security
class TestJWTTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token_with_default_expiration(self):
        """Test create_access_token() with default expiration."""
        settings = get_settings()
        data = {"sub": "testuser"}

        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_with_custom_expires_delta(self):
        """Test create_access_token() with custom expiration time."""
        settings = get_settings()
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)

        # Get current time before creating token
        now_before = datetime.utcnow()
        token = create_access_token(data, expires_delta=expires_delta)

        # Decode and verify expiration time
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        exp_time = datetime.utcfromtimestamp(payload["exp"])

        # Expiration should be approximately 30 minutes from when we started
        # (allow 60 second tolerance for test execution time)
        time_diff = (exp_time - now_before).total_seconds()
        assert 1740 < time_diff < 1860  # ~30 minutes (1800 seconds) with tolerance

    def test_create_access_token_preserves_additional_data(self):
        """Test create_access_token() preserves additional data in payload."""
        data = {
            "sub": "testuser",
            "role": "admin",
            "email": "test@example.com"
        }

        token = create_access_token(data)

        # Decode and verify all data is preserved
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["email"] == "test@example.com"

    def test_create_access_token_deterministic_in_test(self):
        """Test token creation is deterministic with fixed SECRET_KEY."""
        # In test environment, we use a fixed SECRET_KEY
        # This test verifies deterministic behavior for debugging

        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=1)

        # Create token
        token = create_access_token(data, expires_delta=expires_delta)

        # Should be able to decode it
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert payload["sub"] == "testuser"


@pytest.mark.unit
@pytest.mark.security
class TestJWTTokenVerification:
    """Test JWT token verification."""

    def test_verify_token_with_valid_token(self, valid_token):
        """Test verify_token() returns payload for valid token."""
        payload = verify_token(valid_token)

        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_verify_token_with_expired_token(self, expired_token):
        """Test verify_token() returns None for expired token."""
        # Small delay to ensure token is definitely expired
        time.sleep(0.1)

        payload = verify_token(expired_token)

        assert payload is None

    def test_verify_token_with_invalid_signature(self):
        """Test verify_token() returns None for token with invalid signature."""
        settings = get_settings()

        # Create token with different secret key
        fake_token = jwt.encode(
            {"sub": "testuser"},
            "wrong_secret_key_that_is_at_least_32_characters_long",
            algorithm=settings.algorithm
        )

        payload = verify_token(fake_token)

        assert payload is None

    def test_verify_token_with_malformed_token(self):
        """Test verify_token() returns None for malformed token."""
        malformed_tokens = [
            "not.a.valid.jwt.token",
            "invalid",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        ]

        for token in malformed_tokens:
            payload = verify_token(token)
            assert payload is None, f"Expected None for malformed token: {token}"

    def test_verify_token_with_wrong_algorithm(self):
        """Test verify_token() returns None for token with wrong algorithm."""
        settings = get_settings()

        # Create token with different algorithm (HS512 instead of HS256)
        wrong_algo_token = jwt.encode(
            {"sub": "testuser"},
            settings.secret_key,
            algorithm="HS512"
        )

        payload = verify_token(wrong_algo_token)

        # Should fail verification because algorithm doesn't match
        assert payload is None


@pytest.mark.unit
@pytest.mark.auth
class TestUserAuthentication:
    """Test user authentication."""

    def test_authenticate_user_with_valid_credentials(self, test_user_credentials):
        """Test authenticate_user() with valid credentials returns user dict."""
        user = authenticate_user(
            test_user_credentials["username"],
            test_user_credentials["password"]
        )

        assert user is not None
        assert isinstance(user, dict)
        assert user["username"] == test_user_credentials["username"]

    def test_authenticate_user_with_invalid_username(self):
        """Test authenticate_user() with invalid username returns None."""
        user = authenticate_user("wronguser", "testpass")

        assert user is None

    def test_authenticate_user_with_invalid_password(self, test_user_credentials):
        """Test authenticate_user() with invalid password returns None."""
        user = authenticate_user(
            test_user_credentials["username"],
            "wrongpassword"
        )

        assert user is None

    def test_authenticate_user_case_sensitive_username(self):
        """Test authenticate_user() username is case-sensitive."""
        # Assuming testuser is the configured username
        user = authenticate_user("testuser", "testpass")
        assert user is not None

        # Different case should fail
        user = authenticate_user("TestUser", "testpass")
        assert user is None

        user = authenticate_user("TESTUSER", "testpass")
        assert user is None

    def test_authenticate_user_with_empty_credentials(self):
        """Test authenticate_user() with empty credentials returns None."""
        assert authenticate_user("", "") is None
        assert authenticate_user("testuser", "") is None
        assert authenticate_user("", "testpass") is None


@pytest.mark.security
class TestSecurityEdgeCases:
    """Test edge cases and security scenarios."""

    def test_password_with_special_characters(self):
        """Test password hashing works with special characters within bcrypt's limits."""
        # Note: bcrypt has a 72-byte limit, so we keep passwords short
        special_passwords = [
            "p@ssw0rd!#$%",
            "пароль",  # Cyrillic (12 bytes in UTF-8)
            "密码test",  # Chinese + ASCII (10 bytes)
            "pass word with spaces",
        ]

        for password in special_passwords:
            # Verify password is within bcrypt's byte limit
            assert len(password.encode('utf-8')) <= 72, \
                f"Password '{password}' exceeds bcrypt's 72-byte limit"
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True

    def test_very_long_password(self):
        """Test that bcrypt handles passwords at and beyond the 72-byte limit."""
        # Bcrypt has a 72-byte limit
        # bcrypt 4.x truncates passwords > 72 bytes automatically
        # This test verifies behavior with long passwords

        # Password within the limit should work fine
        acceptable_password = "a" * 70  # 70 bytes, within limit
        hashed = get_password_hash(acceptable_password)
        assert verify_password(acceptable_password, hashed) is True

        # Password at the limit should work
        limit_password = "a" * 72  # Exactly 72 bytes
        hashed_limit = get_password_hash(limit_password)
        assert verify_password(limit_password, hashed_limit) is True

        # Password exceeding limit - bcrypt 4.x truncates to 72 bytes
        # So "a" * 100 and "a" * 72 should verify the same
        long_password = "a" * 100
        hashed_long = get_password_hash(long_password)
        # The long password verifies against its own hash
        assert verify_password(long_password, hashed_long) is True
        # And also verifies against the 72-byte version (bcrypt truncates)
        assert verify_password(limit_password, hashed_long) is True

    def test_token_with_special_characters_in_subject(self):
        """Test JWT token creation with special characters in subject."""
        special_subjects = [
            "user@example.com",
            "user+test@example.com",
            "user_name-123",
        ]

        for subject in special_subjects:
            token = create_access_token({"sub": subject})
            payload = verify_token(token)

            assert payload is not None
            assert payload["sub"] == subject
