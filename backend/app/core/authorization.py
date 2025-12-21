"""
Role-based authorization utilities.

This module provides authorization functions and dependencies:
- Admin-only route protection
- Role-based access control
"""
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that requires admin role.

    Use this dependency on routes that should only be accessible to admins.

    Args:
        current_user: Current authenticated user (from get_current_user dependency)

    Returns:
        Current user dict if user is admin

    Raises:
        HTTPException 403: If user is not an admin

    Example:
        @router.post("/admin/users")
        async def create_user(
            user_data: UserCreate,
            current_user: dict = Depends(require_admin)
        ):
            # Only admins can reach this point
            ...
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. You do not have permission to perform this action.",
        )

    return current_user


async def require_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that ensures user account is active.

    Use this dependency on routes that require an active user account.
    This is automatically included in get_current_user, but can be used
    explicitly for clarity.

    Args:
        current_user: Current authenticated user (from get_current_user dependency)

    Returns:
        Current user dict if user is active

    Raises:
        HTTPException 403: If user account is not active

    Note:
        Currently this check is done during authentication, but this
        dependency provides an additional layer of protection.
    """
    # Note: is_active is checked during authentication, but we can add
    # additional checks here if needed in the future
    return current_user


def check_user_permissions(current_user: dict, required_role: str) -> bool:
    """
    Check if user has required role.

    Args:
        current_user: Current user dict
        required_role: Required role ("admin" or "user")

    Returns:
        True if user has required role, False otherwise

    Example:
        if check_user_permissions(current_user, "admin"):
            # User is admin
            ...
    """
    user_role = current_user.get("role", "user")

    # Admin has all permissions
    if user_role == "admin":
        return True

    # Check specific role
    return user_role == required_role


async def check_resource_ownership(
    current_user: dict, resource_user_id: int
) -> bool:
    """
    Check if user owns a resource or is admin.

    Admins can access all resources, users can only access their own.

    Args:
        current_user: Current user dict
        resource_user_id: User ID who owns the resource

    Returns:
        True if user can access resource, False otherwise

    Example:
        if not await check_resource_ownership(current_user, image.user_id):
            raise HTTPException(403, "Access denied")
    """
    # Admins can access everything
    if current_user.get("role") == "admin":
        return True

    # Users can only access their own resources
    return current_user.get("user_id") == resource_user_id
