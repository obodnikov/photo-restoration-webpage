"""
Password validation utilities.

This module provides password validation and policy enforcement:
- Password complexity requirements
- Password strength validation
- Clear error messages for password requirements
"""
import re
from typing import List, Optional


class PasswordValidationError(Exception):
    """Exception raised when password validation fails."""

    pass


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password against policy requirements.

    Password must meet the following criteria:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit

    Args:
        password: Plain text password to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if password meets all requirements
        - error_message: None if valid, error description if invalid

    Examples:
        >>> validate_password("MyPass123")
        (True, None)

        >>> validate_password("short")
        (False, "Password must be at least 8 characters long")
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    return True, None


def get_password_requirements() -> List[str]:
    """
    Get list of password requirements for display to users.

    Returns:
        List of password requirement strings
    """
    return [
        "At least 8 characters long",
        "Contains at least one uppercase letter (A-Z)",
        "Contains at least one lowercase letter (a-z)",
        "Contains at least one digit (0-9)",
    ]


def validate_password_or_raise(password: str) -> None:
    """
    Validate password and raise exception if invalid.

    This is a convenience function for use in routes where you want
    to raise an exception on validation failure.

    Args:
        password: Plain text password to validate

    Raises:
        PasswordValidationError: If password does not meet requirements

    Example:
        try:
            validate_password_or_raise(new_password)
        except PasswordValidationError as e:
            return {"error": str(e)}
    """
    is_valid, error_message = validate_password(password)

    if not is_valid:
        raise PasswordValidationError(error_message)
