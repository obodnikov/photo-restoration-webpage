"""
Tests for JWT session validation security features.

This module tests the get_current_user_validated() dependency to ensure:
- Valid tokens with active users and valid sessions work correctly
- Inactive users are rejected
- Deleted sessions are rejected
- Non-existent users are rejected
- Session-less tokens remain valid for backwards compatibility
- Remote logout and user disabling take effect immediately
"""
import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_validated, get_password_hash
from app.db.models import Session as SessionModel, User


async def invoke_validator(db_session: AsyncSession, user_data: dict) -> dict:
    """Helper to execute the validated user dependency exactly as FastAPI would."""
    validate_user = get_current_user_validated()
    return await validate_user(user_data=user_data, db=db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create an active user for security validation tests."""
    user = User(
        username="security_test_user",
        email="security_test@example.com",
        full_name="Security Test User",
        hashed_password=get_password_hash("securepassword123"),
        role="user",
        is_active=True,
        password_must_change=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_validated_user_with_valid_session(
    db_session: AsyncSession, test_user: User
):
    """get_current_user_validated returns the token payload for active user/session."""
    session = SessionModel(user_id=test_user.id, session_id="test-session-123")
    db_session.add(session)
    await db_session.commit()

    user_data = {
        "username": test_user.username,
        "user_id": test_user.id,
        "role": test_user.role,
        "session_id": session.session_id,
        "password_must_change": test_user.password_must_change,
    }

    result = await invoke_validator(db_session, user_data)

    assert result == user_data
    assert result["username"] == test_user.username


@pytest.mark.asyncio
async def test_validated_user_rejects_inactive_user(
    db_session: AsyncSession, test_user: User
):
    """Inactive users cause the dependency to raise HTTP 401."""
    test_user.is_active = False
    await db_session.commit()

    session = SessionModel(user_id=test_user.id, session_id="inactive-session")
    db_session.add(session)
    await db_session.commit()

    user_data = {
        "username": test_user.username,
        "user_id": test_user.id,
        "role": test_user.role,
        "session_id": session.session_id,
        "password_must_change": test_user.password_must_change,
    }

    with pytest.raises(HTTPException) as exc_info:
        await invoke_validator(db_session, user_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "User account has been disabled"


@pytest.mark.asyncio
async def test_validated_user_rejects_deleted_session(
    db_session: AsyncSession, test_user: User
):
    """Deleted sessions result in HTTP 401 errors."""
    session = SessionModel(user_id=test_user.id, session_id="test-session-789")
    db_session.add(session)
    await db_session.commit()

    session_id = session.session_id

    await db_session.delete(session)
    await db_session.commit()

    user_data = {
        "username": test_user.username,
        "user_id": test_user.id,
        "role": test_user.role,
        "session_id": session_id,
        "password_must_change": test_user.password_must_change,
    }

    with pytest.raises(HTTPException) as exc_info:
        await invoke_validator(db_session, user_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Session has been terminated"


@pytest.mark.asyncio
async def test_validated_user_rejects_nonexistent_user(db_session: AsyncSession):
    """Tokens referencing users that no longer exist are rejected."""
    user_data = {
        "username": "ghost",
        "user_id": 999_999,
        "role": "user",
        "session_id": None,
        "password_must_change": False,
    }

    with pytest.raises(HTTPException) as exc_info:
        await invoke_validator(db_session, user_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "User account no longer exists"


@pytest.mark.asyncio
async def test_validated_user_works_without_session_id(
    db_session: AsyncSession, test_user: User
):
    """Legacy tokens without session_id remain valid (session check skipped)."""
    user_data = {
        "username": test_user.username,
        "user_id": test_user.id,
        "role": test_user.role,
        "session_id": None,
        "password_must_change": test_user.password_must_change,
    }

    result = await invoke_validator(db_session, user_data)

    assert result["username"] == test_user.username
    assert result["session_id"] is None


@pytest.mark.asyncio
async def test_security_validation_integration(db_session: AsyncSession, test_user: User):
    """Complete flow: session valid, then user disabled blocks future requests."""
    session = SessionModel(user_id=test_user.id, session_id="integration-test-session")
    db_session.add(session)
    await db_session.commit()

    user_data = {
        "username": test_user.username,
        "user_id": test_user.id,
        "role": test_user.role,
        "session_id": session.session_id,
        "password_must_change": test_user.password_must_change,
    }

    # Initially passes
    result = await invoke_validator(db_session, user_data)
    assert result["session_id"] == session.session_id

    # Disable user to simulate admin action
    test_user.is_active = False
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await invoke_validator(db_session, user_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "User account has been disabled"


@pytest.mark.asyncio
async def test_session_deletion_invalidates_token(
    db_session: AsyncSession, test_user: User
):
    """Remote logout (session deletion) should make subsequent requests fail."""
    session = SessionModel(user_id=test_user.id, session_id="remote-logout-test")
    db_session.add(session)
    await db_session.commit()

    user_data = {
        "username": test_user.username,
        "user_id": test_user.id,
        "role": test_user.role,
        "session_id": session.session_id,
        "password_must_change": test_user.password_must_change,
    }

    # First call succeeds
    await invoke_validator(db_session, user_data)

    # Delete the session to simulate remote logout
    await db_session.delete(session)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await invoke_validator(db_session, user_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Session has been terminated"
