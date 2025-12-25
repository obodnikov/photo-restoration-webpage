# Phase 2.4 API Documentation - Enhanced Authentication

**Version:** 1.0.0
**Date:** December 21, 2024
**Status:** Backend Complete, Frontend Pending

## Overview

Phase 2.4 adds comprehensive user management and enhanced authentication features to the Photo Restoration API. The system now supports database-backed users, role-based authorization, and cross-session history access.

---

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### JWT Token Payload

Tokens now include extended user information:

```json
{
  "sub": "username",
  "user_id": 1,
  "role": "admin",
  "session_id": "uuid-here",
  "password_must_change": false,
  "exp": 1703176800
}
```

---

## Admin Endpoints

**Authorization Required:** Admin role only

All admin endpoints are prefixed with `/api/v1/admin`

### Create User

Create a new user account (admin only).

**Endpoint:** `POST /api/v1/admin/users`

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "SecurePass123",
  "role": "user",
  "password_must_change": true
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-12-21T10:30:00",
  "last_login": null
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)

**Username Requirements:**
- Only letters, numbers, underscores, and hyphens
- Automatically normalized to lowercase

**Errors:**
- `400` - Username or email already exists
- `400` - Password doesn't meet requirements
- `403` - Not an admin user

---

### List Users

Get paginated list of all users with optional filtering.

**Endpoint:** `GET /api/v1/admin/users`

**Query Parameters:**
- `skip` (int, default: 0) - Number of users to skip
- `limit` (int, default: 100, max: 1000) - Max users to return
- `role` (string, optional) - Filter by role ("admin" or "user")
- `is_active` (boolean, optional) - Filter by active status

**Example:**
```http
GET /api/v1/admin/users?skip=0&limit=10&role=user&is_active=true
```

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": 2,
      "username": "johndoe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "user",
      "is_active": true,
      "created_at": "2024-12-21T10:30:00",
      "last_login": "2024-12-21T14:20:00"
    }
  ],
  "total": 15
}
```

---

### Get User Details

Get detailed information about a specific user.

**Endpoint:** `GET /api/v1/admin/users/{user_id}`

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-12-21T10:30:00",
  "last_login": "2024-12-21T14:20:00"
}
```

**Errors:**
- `404` - User not found

---

### Update User

Update user information.

**Endpoint:** `PUT /api/v1/admin/users/{user_id}`

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "John Smith",
  "role": "admin",
  "is_active": false
}
```

All fields are optional. Only provided fields will be updated.

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "johndoe",
  "email": "newemail@example.com",
  "full_name": "John Smith",
  "role": "admin",
  "is_active": false,
  "created_at": "2024-12-21T10:30:00",
  "last_login": "2024-12-21T14:20:00"
}
```

**Errors:**
- `400` - Email already exists
- `404` - User not found

---

### Delete User

Permanently delete a user and all associated data (sessions, images).

**Endpoint:** `DELETE /api/v1/admin/users/{user_id}`

**Response:** `204 No Content`

**Errors:**
- `400` - Cannot delete your own account
- `404` - User not found

**Warning:** This action is irreversible and will delete:
- User account
- All user sessions
- All processed images (CASCADE delete)

---

### Reset User Password

Reset a user's password (admin only).

**Endpoint:** `PUT /api/v1/admin/users/{user_id}/reset-password`

**Request Body:**
```json
{
  "new_password": "NewSecurePass123",
  "password_must_change": true
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-12-21T10:30:00",
  "last_login": "2024-12-21T14:20:00"
}
```

**Note:** Setting `password_must_change` to `true` forces the user to change their password on next login.

---

## User Profile Endpoints

**Authorization Required:** Any authenticated user

All user endpoints are prefixed with `/api/v1/users`

### Get Own Profile

Get current user's profile information.

**Endpoint:** `GET /api/v1/users/me`

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-12-21T10:30:00",
  "last_login": "2024-12-21T14:20:00"
}
```

---

### Change Own Password

Change the current user's password.

**Endpoint:** `PUT /api/v1/users/me/password`

**Request Body:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Errors:**
- `400` - Current password is incorrect
- `400` - New password must be different from current
- `400` - New password doesn't meet requirements

**Note:** This automatically clears the `password_must_change` flag.

---

### Get Active Sessions

List all active sessions for the current user.

**Endpoint:** `GET /api/v1/users/me/sessions`

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "id": 1,
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2024-12-21T10:00:00",
      "last_accessed": "2024-12-21T14:30:00",
      "image_count": 5
    },
    {
      "id": 2,
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2024-12-20T15:00:00",
      "last_accessed": "2024-12-20T16:00:00",
      "image_count": 3
    }
  ],
  "total": 2
}
```

---

### Delete Session (Remote Logout)

Delete a specific session (logout from a device).

**Endpoint:** `DELETE /api/v1/users/me/sessions/{session_id}`

**Response:** `204 No Content`

**Errors:**
- `403` - Session belongs to another user
- `404` - Session not found

**Use Case:** Remotely logout from other devices while keeping current session active.

---

## Updated Endpoints

### History (Cross-Session Access)

The history endpoint now returns ALL images for the current user across ALL sessions.

**Endpoint:** `GET /api/v1/restore/history`

**Query Parameters:**
- `limit` (int, default: 50) - Max images to return
- `offset` (int, default: 0) - Number of images to skip

**Behavior Changes:**
- **Before Phase 2.4:** Only images from current session
- **After Phase 2.4:** ALL images from user across ALL sessions

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "original_filename": "old_photo.jpg",
      "model_id": "swin2sr-2x",
      "original_url": "/uploads/path/to/original.jpg",
      "processed_url": "/processed/path/to/processed.jpg",
      "created_at": "2024-12-21T10:00:00",
      "model_parameters": "{\"scale\": 2}"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

**Security:** Users can ONLY see their own images, not images from other users.

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Username 'johndoe' already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required. You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "User with ID 5 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database error while retrieving image history"
}
```

---

## Migration from Phase 1.x

### Breaking Changes

1. **Database Schema:** User table added, Session table updated
2. **Environment Variables:** New variables required (AUTH_EMAIL, AUTH_FULL_NAME)
3. **Sessions:** Now linked to users (no more anonymous sessions)

### Migration Steps

1. **Backup Data (if needed):**
   ```bash
   cp backend/data/photo_restoration.db backend/data/photo_restoration.db.backup
   ```

2. **Update Environment Variables:**
   ```env
   # Add to backend/.env
   AUTH_EMAIL=admin@example.com
   AUTH_FULL_NAME=System Administrator
   ```

3. **Delete Old Database:**
   ```bash
   rm -f backend/data/photo_restoration.db*
   ```

4. **Start Backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
   Admin user will be auto-created from .env variables.

5. **Test Login:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "password": "changeme"
     }'
   ```

---

## Best Practices

### Password Management
- Always use strong passwords
- Set `password_must_change=true` for new users
- Regularly rotate admin passwords
- Use environment variables for admin credentials (never hardcode)

### Session Management
- Implement session cleanup for inactive sessions
- Monitor active sessions regularly
- Use remote logout for compromised sessions
- Consider shorter token expiration for sensitive operations

### User Management
- Use descriptive full names for users
- Regularly audit user list (active vs inactive)
- Disable users instead of deleting (preserves history)
- Document role assignments

### Security
- Admin credentials should be unique per environment
- Use HTTPS in production
- Implement rate limiting on auth endpoints
- Monitor failed login attempts
- Regular security audits of user permissions

---

## Testing Endpoints

### Using cURL

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}'
```

**Create User (as admin):**
```bash
TOKEN="your_jwt_token_here"
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "TestPass123",
    "role": "user"
  }'
```

**Get Profile:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Future Enhancements

Planned for future phases:

- [ ] Email-based password reset
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] Session expiration policies
- [ ] Audit logging for admin actions
- [ ] User groups/teams
- [ ] API key authentication
- [ ] IP whitelisting for admin access

---

## Support

For issues or questions:
- Report bugs: https://github.com/anthropics/claude-code/issues
- Documentation: /docs/
- ROADMAP: /ROADMAP.md
