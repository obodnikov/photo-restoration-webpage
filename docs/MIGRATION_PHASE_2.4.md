# Migration Guide: Phase 2.4 Enhanced Authentication

**From:** Phase 1.x (Hardcoded Authentication)
**To:** Phase 2.4 (Database-Backed User Management)
**Date:** December 21, 2024

---

## ⚠️ Breaking Changes

Phase 2.4 introduces **breaking changes** that require manual migration steps. Please read this guide carefully before upgrading.

### What's Changed

1. **Database Schema**
   - New `users` table added
   - `sessions` table updated with `user_id` foreign key
   - Old anonymous sessions are no longer supported

2. **Authentication**
   - No more hardcoded credentials
   - All users must exist in database
   - JWT tokens now include `user_id` and `role`

3. **Environment Variables**
   - New required: `AUTH_EMAIL`, `AUTH_FULL_NAME`
   - `AUTH_USERNAME` and `AUTH_PASSWORD` now used for admin seeding only

4. **Sessions**
   - All sessions must be linked to a user
   - Old anonymous sessions will be orphaned

---

## Migration Strategy

### Option A: Clean Migration (Recommended)

**Best for:** Fresh installs, development, testing

**Steps:**
1. Backup any important data
2. Delete old database
3. Update environment variables
4. Restart application
5. Admin user auto-created
6. Create additional users

**Advantages:**
- ✅ Clean start
- ✅ No data conflicts
- ✅ Fastest migration
- ✅ Guaranteed to work

**Disadvantages:**
- ❌ Loses existing session history
- ❌ Loses processed images

---

### Option B: Manual Data Migration (Advanced)

**Best for:** Production with valuable data

**Steps:**
1. Export existing data
2. Update environment
3. Initialize new database
4. Import data with user mapping
5. Verify integrity

**Advantages:**
- ✅ Preserves data
- ✅ Maintains history

**Disadvantages:**
- ❌ More complex
- ❌ Requires custom scripts
- ❌ Time-consuming

**Note:** Option B requires custom migration scripts not included in this release.

---

## Clean Migration Steps (Option A)

### Step 1: Backup Current Data (Optional)

If you have images you want to keep:

```bash
# Backup database
cp backend/data/photo_restoration.db backend/data/photo_restoration.db.backup

# Backup uploaded images
cp -r backend/data/uploads backend/data/uploads.backup

# Backup processed images
cp -r backend/data/processed backend/data/processed.backup
```

**Note:** Even with backup, old sessions won't work in new system.

---

### Step 2: Update Environment Variables

Edit `backend/.env` and add new required variables:

```env
# Admin User Credentials (for database seeding - Phase 2.4)
# These are used to create the initial admin user in the database
# WARNING: Change these values from defaults in production!
AUTH_USERNAME=admin
AUTH_PASSWORD=YourSecurePassword123!
AUTH_EMAIL=admin@yourdomain.com
AUTH_FULL_NAME=Your Full Name
```

**Important Security Notes:**
- ❗ **Change AUTH_PASSWORD** from default
- ❗ Use a strong password (min 8 chars, uppercase, lowercase, digit)
- ❗ Use a real email address
- ❗ Keep `.env` file secure (never commit to git)

**Example:**
```env
AUTH_USERNAME=admin
AUTH_PASSWORD=MySecureAdminPass123!
AUTH_EMAIL=mike@sqowe.com
AUTH_FULL_NAME=Mike Anderson
```

---

### Step 3: Delete Old Database

**⚠️ WARNING:** This will delete all existing data!

```bash
cd /path/to/photo-restoration-webpage

# Delete SQLite database files
rm -f backend/data/photo_restoration.db
rm -f backend/data/photo_restoration.db-shm
rm -f backend/data/photo_restoration.db-wal

# Optionally, clean up images too
# rm -rf backend/data/uploads/*
# rm -rf backend/data/processed/*
```

**Verification:**
```bash
ls -la backend/data/
# Should see empty or minimal files
```

---

### Step 4: Start Backend

The backend will automatically:
1. Create new database with updated schema
2. Seed admin user from environment variables
3. Be ready to accept requests

```bash
cd backend

# If using virtual environment
source venv/bin/activate  # or: /opt/homebrew/bin/python3.13 -m venv venv

# Start backend
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Starting Photo Restoration API v1.8.2
INFO:     Environment: development
INFO:     Configuration source: JSON config files
INFO:     Starting database seeding...
INFO:     Created admin user: admin (admin@yourdomain.com) with ID 1
INFO:     Database seeding completed successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Success Indicators:**
- ✅ "Created admin user" message appears
- ✅ No errors during startup
- ✅ Server is running

---

### Step 5: Test Admin Login

Test that admin account works:

```bash
# Login request
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "YourSecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**If login fails:**
- Check password matches `.env` file
- Check username is lowercase
- Check backend logs for errors
- Verify database was created: `ls backend/data/`

---

### Step 6: Verify Database Schema

Check that tables were created correctly:

```bash
# Install sqlite3 if needed
# macOS: brew install sqlite3
# Linux: apt-get install sqlite3

# Connect to database
sqlite3 backend/data/photo_restoration.db

# Check tables
.tables
# Should show: processed_images  sessions  users

# Check admin user
SELECT * FROM users;
# Should show one row with admin user

# Exit
.exit
```

---

### Step 7: Create Additional Users (Once Frontend Available)

After frontend is implemented:

1. Login as admin at `/login`
2. Navigate to `/admin/users`
3. Click "Create User"
4. Fill in user details
5. Assign role (admin or user)
6. Click "Create"

**Or via API:**
```bash
# Get admin token first (from Step 5)
TOKEN="your_admin_token_here"

# Create new user
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "password": "UserPass123!",
    "role": "user",
    "password_must_change": true
  }'
```

---

## Docker Deployment

If using Docker:

### Step 1: Update docker-compose.yml

No changes needed! Environment variables are already configured.

### Step 2: Update .env File

```bash
# Edit backend/.env with new variables
nano backend/.env

# Or copy from example
cp backend/.env.example backend/.env
# Then edit with your values
```

### Step 3: Stop and Remove Containers

```bash
# Stop all containers
docker-compose down

# Remove volumes (deletes database!)
docker-compose down -v

# Or manually delete volume
docker volume rm photo-restoration-webpage_sqlite_data
```

### Step 4: Rebuild and Start

```bash
# Rebuild containers
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

**Expected in logs:**
```
backend_1  | INFO:     Created admin user: admin (admin@yourdomain.com) with ID 1
backend_1  | INFO:     Database seeding completed successfully
```

---

## Troubleshooting

### Issue: "Admin user already exists"

**Cause:** Database already has admin user (seeding ran before)

**Solution:** This is normal! Seeding is idempotent. If you want to reset:
```bash
rm backend/data/photo_restoration.db*
# Restart backend
```

---

### Issue: "Cannot create admin user: Missing required environment variables"

**Cause:** Missing AUTH_EMAIL or AUTH_FULL_NAME

**Solution:**
```bash
# Check .env file
cat backend/.env | grep AUTH_

# Should see:
# AUTH_USERNAME=admin
# AUTH_PASSWORD=...
# AUTH_EMAIL=...
# AUTH_FULL_NAME=...

# Add missing variables
echo "AUTH_EMAIL=admin@example.com" >> backend/.env
echo "AUTH_FULL_NAME=System Administrator" >> backend/.env

# Restart backend
```

---

### Issue: Login fails with "Invalid credentials"

**Cause:** Username/password mismatch

**Solutions:**
1. **Check password:** Verify it matches `.env` file exactly
2. **Check username:** Must be lowercase (normalized automatically)
3. **Check database:** Verify user exists in database
   ```bash
   sqlite3 backend/data/photo_restoration.db "SELECT username FROM users;"
   ```
4. **Reset password via database:**
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"])
   hashed = pwd_context.hash("NewPassword123!")
   # Then update in database:
   # UPDATE users SET hashed_password='...' WHERE username='admin';
   ```

---

### Issue: "Could not validate credentials" when accessing protected routes

**Cause:** Invalid or expired JWT token

**Solutions:**
1. **Get fresh token:** Login again
2. **Check token format:** Must be `Bearer <token>`
3. **Check expiration:** Tokens expire (24h default, 7 days with remember_me)

---

### Issue: Session cleanup removed my sessions

**Cause:** Sessions older than 24 hours are auto-cleaned

**Solution:** Sessions are cleaned up after 24 hours of inactivity (configurable)
```env
# In .env
SESSION_CLEANUP_HOURS=24  # Increase if needed
```

---

## Rollback (If Needed)

If migration fails and you need to rollback:

### Step 1: Restore Backup

```bash
# Stop backend
# Ctrl+C or docker-compose down

# Restore database backup
cp backend/data/photo_restoration.db.backup backend/data/photo_restoration.db

# Restore images (if backed up)
rm -rf backend/data/uploads
rm -rf backend/data/processed
cp -r backend/data/uploads.backup backend/data/uploads
cp -r backend/data/processed.backup backend/data/processed
```

### Step 2: Checkout Previous Version

```bash
# Find previous commit before Phase 2.4
git log --oneline

# Checkout that commit
git checkout <commit-hash>
```

### Step 3: Restart

```bash
# Restart backend with old code
cd backend
uvicorn app.main:app --reload
```

---

## Post-Migration Checklist

- [ ] Backend starts without errors
- [ ] Admin user created successfully
- [ ] Admin login works
- [ ] Can create new users (via API)
- [ ] New users can login
- [ ] Sessions are created properly
- [ ] History endpoint works
- [ ] Images can be uploaded and processed
- [ ] Database backup created
- [ ] `.env` file secured (not in git)
- [ ] Admin password changed from default
- [ ] Documentation updated

---

## Production Deployment Considerations

### Security

1. **Change Default Credentials:**
   ```env
   AUTH_USERNAME=unique_admin_username
   AUTH_PASSWORD=VeryStrongPassword123!@#
   AUTH_EMAIL=real-admin-email@company.com
   ```

2. **Secure SECRET_KEY:**
   ```bash
   # Generate secure key
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   # Add to .env
   SECRET_KEY=<generated-key>
   ```

3. **Use HTTPS:**
   - Configure nginx for SSL/TLS
   - Force HTTPS redirects
   - Use valid certificates (Let's Encrypt)

4. **Restrict Admin Access:**
   - Consider IP whitelisting for admin panel
   - Implement 2FA (future phase)
   - Monitor admin activity

### Performance

1. **Database Optimization:**
   - WAL mode enabled (default)
   - Regular VACUUM
   - Index optimization

2. **Session Cleanup:**
   - Configure appropriate cleanup interval
   - Monitor session growth

3. **Backups:**
   - Automated daily backups
   - Test restore procedures
   - Offsite backup storage

---

## Support

For help with migration:

1. **Check Logs:**
   ```bash
   # Backend logs
   docker-compose logs backend
   # Or direct run
   tail -f <uvicorn-log-file>
   ```

2. **Enable Debug Mode:**
   ```env
   DEBUG=true
   ```

3. **Report Issues:**
   - GitHub Issues: https://github.com/anthropics/claude-code/issues
   - Include: logs, error messages, steps to reproduce

4. **Documentation:**
   - API Documentation: `/docs/API_PHASE_2.4.md`
   - ROADMAP: `/ROADMAP.md`
   - Code Review: `/tmp/last-review-*.md`

---

## Next Steps

After successful migration:

1. **Test Thoroughly:**
   - Test all user workflows
   - Test admin workflows
   - Test error cases

2. **Implement Frontend:**
   - Admin panel (`/admin/users`)
   - User profile (`/profile`)
   - Updated history page

3. **Add Tests:**
   - Unit tests for new models
   - Integration tests for endpoints
   - End-to-end tests

4. **Monitor:**
   - Watch for errors
   - Monitor user creation
   - Track session activity

5. **Document:**
   - Update team documentation
   - Create user guides
   - Document processes

---

**Migration Date:** ________________

**Migrated By:** ________________

**Notes:** ________________
