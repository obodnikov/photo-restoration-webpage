"""
Tests for password validation utilities.

Tests password complexity requirements and validation logic.
"""
import pytest

from app.utils.password_validator import (
    PasswordValidationError,
    validate_password,
    validate_password_or_raise,
)


class TestPasswordValidator:
    """Test password validation functionality."""

    def test_valid_password_minimum_requirements(self):
        """Valid password with minimum requirements should pass."""
        # 8 chars, 1 upper, 1 lower, 1 digit
        is_valid, error = validate_password("Pass123word")
        assert is_valid is True
        assert error is None

        is_valid, error = validate_password("Abcd1234")
        assert is_valid is True

        is_valid, error = validate_password("Test1234")
        assert is_valid is True

    def test_valid_password_with_special_chars(self):
        """Valid password with special characters should pass."""
        is_valid, _ = validate_password("P@ssw0rd!")
        assert is_valid is True

        is_valid, _ = validate_password("MyP@ss123")
        assert is_valid is True

        is_valid, _ = validate_password("Test#123$")
        assert is_valid is True

    def test_valid_password_longer(self):
        """Valid password longer than minimum should pass."""
        is_valid, _ = validate_password("ThisIsAVeryLongPassword123")
        assert is_valid is True

        is_valid, _ = validate_password("SuperSecurePassword999!")
        assert is_valid is True

    def test_invalid_password_too_short(self):
        """Password shorter than 8 characters should fail."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("Pass12")

        assert "at least 8 characters" in str(exc_info.value)

    def test_invalid_password_no_uppercase(self):
        """Password without uppercase letter should fail."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("password123")

        assert "uppercase letter" in str(exc_info.value)

    def test_invalid_password_no_lowercase(self):
        """Password without lowercase letter should fail."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("PASSWORD123")

        assert "lowercase letter" in str(exc_info.value)

    def test_invalid_password_no_digit(self):
        """Password without digit should fail."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("PasswordWord")

        assert "digit" in str(exc_info.value)

    def test_empty_password(self):
        """Empty password should fail."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("")

        assert "empty" in str(exc_info.value).lower() or "8 characters" in str(exc_info.value)

    def test_none_password(self):
        """None password should fail."""
        # None should cause validation error
        is_valid, error = validate_password(None)
        assert is_valid is False
        assert error is not None

    def test_whitespace_only_password(self):
        """Whitespace-only password should fail."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("        ")

        # Should fail on character requirements
        assert "letter" in str(exc_info.value).lower() or "digit" in str(exc_info.value).lower()

    def test_password_with_spaces(self):
        """Password with spaces is allowed if it meets requirements."""
        # Spaces are allowed, as long as other requirements are met
        is_valid, _ = validate_password("Pass Word 123")
        assert is_valid is True

        is_valid, _ = validate_password("My Pass 1234")
        assert is_valid is True

    def test_password_exactly_8_chars(self):
        """Password with exactly 8 characters should pass if valid."""
        is_valid, _ = validate_password("Passw0rd")
        assert is_valid is True

        is_valid, _ = validate_password("Test1234")
        assert is_valid is True

    def test_password_with_unicode(self):
        """Password with unicode characters should pass if valid."""
        is_valid, _ = validate_password("Pässw0rd")
        assert is_valid is True

        is_valid, _ = validate_password("Tëst1234")
        assert is_valid is True

    def test_multiple_validation_errors(self):
        """Password failing multiple requirements should report first error."""
        # Too short, no uppercase, no digit - should report first failing check
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password_or_raise("pass")

        # Should mention "at least 8 characters" (checked first)
        assert "at least 8 characters" in str(exc_info.value)

    def test_password_validation_error_inheritance(self):
        """PasswordValidationError should inherit from Exception."""
        assert issubclass(PasswordValidationError, Exception)

    def test_password_validation_error_message(self):
        """PasswordValidationError should preserve error message."""
        error = PasswordValidationError("Custom error")
        assert str(error) == "Custom error"

    def test_common_weak_passwords_rejected(self):
        """Common weak passwords should be rejected."""
        weak_passwords = [
            "password",      # no uppercase, no digit
            "Password",      # no digit
            "12345678",      # no letters
            "abcdefgh",      # no uppercase, no digit
            "ABCDEFGH",      # no lowercase, no digit
        ]

        for pwd in weak_passwords:
            with pytest.raises(PasswordValidationError):
                validate_password_or_raise(pwd)

    def test_edge_case_all_same_char(self):
        """Password with all same character type should fail."""
        with pytest.raises(PasswordValidationError):
            validate_password_or_raise("aaaaaaaa")  # No uppercase, no digit

        with pytest.raises(PasswordValidationError):
            validate_password_or_raise("AAAAAAAA")  # No lowercase, no digit

        with pytest.raises(PasswordValidationError):
            validate_password_or_raise("11111111")  # No letters

    def test_very_long_password(self):
        """Very long password should pass if valid."""
        long_password = "A" + "b" * 100 + "1"
        is_valid, _ = validate_password(long_password)
        assert is_valid is True

    def test_password_with_all_character_types(self):
        """Password with letters, digits, and special chars should pass."""
        is_valid, _ = validate_password("P@ssw0rd!123")
        assert is_valid is True

        is_valid, _ = validate_password("MyS3cur3P@ss!")
        assert is_valid is True

        is_valid, _ = validate_password("T3st#Passw0rd$")
        assert is_valid is True


@pytest.mark.unit
class TestPasswordValidatorUnit:
    """Unit tests specifically marked for fast execution."""

    def test_basic_validation(self):
        """Basic password validation works."""
        is_valid, _ = validate_password("ValidPass123")
        assert is_valid is True

        with pytest.raises(PasswordValidationError):
            validate_password_or_raise("invalid")


@pytest.mark.security
class TestPasswordValidatorSecurity:
    """Security-focused password validation tests."""

    def test_prevents_sql_injection_patterns(self):
        """Password with SQL injection patterns should be validated normally."""
        # These should still meet password requirements
        is_valid, _ = validate_password("Pass123'; DROP TABLE users--")
        assert is_valid is True

        is_valid, _ = validate_password("Admin' OR '1'='1")
        assert is_valid is True

    def test_prevents_xss_patterns(self):
        """Password with XSS patterns should be validated normally."""
        # These are allowed in passwords (stored hashed)
        is_valid, _ = validate_password("<script>Alert1</script>")
        assert is_valid is True

        is_valid, _ = validate_password("Test<img>123")
        assert is_valid is True

    def test_password_not_leaked_in_error(self):
        """Error messages should not leak the actual password."""
        try:
            validate_password_or_raise("invalid")
        except PasswordValidationError as e:
            # Error message should not contain the password
            assert "invalid" not in str(e)
