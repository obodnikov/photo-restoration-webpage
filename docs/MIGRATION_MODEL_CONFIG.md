# Migration Guide: Admin Model Configuration Feature

## Overview

This guide provides step-by-step instructions for deploying the admin model configuration feature to an existing photo restoration application installation.

**Feature Summary:** Allows administrators to manage AI model configurations through a web UI with hot reload support, without requiring server restarts.

**Version:** Added in commit a189ce8

---

## Prerequisites

- Admin user account with role='admin' in the database
- SSH/shell access to the deployment server
- Docker and docker-compose installed (if using containerized deployment)
- Backup of existing configuration files

---

## Migration Steps

### 1. Configuration File Setup

#### 1.1 Create local.json (if not exists)

Create the local configuration file that will store user-created model configurations:

```bash
# Navigate to backend config directory
cd /path/to/photo-restoration-webpage/backend/config

# Create local.json with empty models array
cat > local.json << 'EOF'
{
  "models": []
}
EOF

# Set proper permissions
chmod 644 local.json
chown <app_user>:<app_group> local.json
```

#### 1.2 Verify default.json Structure

Ensure `backend/config/default.json` contains the model configuration section:

```json
{
  "models": [
    // ... existing default models
  ],
  "model_configuration": {
    "available_tags": [
      "restore",
      "upscale",
      "colorize",
      "denoise",
      "enhance",
      "face",
      "general"
    ],
    "available_categories": [
      "restoration",
      "upscale",
      "colorization",
      "denoising",
      "enhancement"
    ]
  }
}
```

**Action Required:** If `model_configuration` section is missing, add it to `default.json`.

#### 1.3 Verify environment.json (if exists)

If you use environment-specific configurations (production.json, staging.json, etc.), ensure they follow the same structure.

---

### 2. Infrastructure Changes

#### 2.1 Docker Volume Configuration (Docker Deployments)

**CRITICAL:** The config directory must be mounted as **read-write** (not read-only).

**Before:**
```yaml
services:
  backend:
    volumes:
      - ./backend/config:/app/config:ro  # READ-ONLY - will not work!
```

**After:**
```yaml
services:
  backend:
    volumes:
      - ./backend/config:/app/config  # READ-WRITE - required for hot reload
```

**Migration Steps:**

```bash
# 1. Stop the application
docker-compose down

# 2. Edit docker-compose.yml
# Remove :ro flag from config volume mount

# 3. Restart the application
docker-compose up -d

# 4. Verify volume permissions
docker-compose exec backend ls -la /app/config
# Should show rw permissions on local.json
```

#### 2.2 File System Permissions (Non-Docker Deployments)

Ensure the application user has write permissions to the config directory:

```bash
# Set ownership
chown -R <app_user>:<app_group> /path/to/backend/config

# Set permissions
chmod 755 /path/to/backend/config
chmod 644 /path/to/backend/config/*.json
```

---

### 3. Backend Deployment

#### 3.1 Update Code

```bash
# Pull latest code
cd /path/to/photo-restoration-webpage
git fetch origin
git checkout <target_branch>  # e.g., main, feat/model-config-page

# Verify commit includes model config feature
git log --oneline -n 10 | grep -i "model.*config"
```

#### 3.2 Verify Dependencies

No new Python dependencies were added. Standard requirements should work:

```bash
# If using venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# If using Docker
docker-compose build backend
```

#### 3.3 Database Migration

**No database migrations required.** This feature uses JSON file storage, not database tables.

#### 3.4 Restart Backend Service

```bash
# Docker deployment
docker-compose restart backend

# Systemd service
sudo systemctl restart photo-restoration-backend

# Manual process
# Kill existing process and restart
```

#### 3.5 Verify Backend Health

```bash
# Check logs for errors
docker-compose logs -f backend | grep -i error

# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test admin model config endpoint (requires admin token)
curl -H "Authorization: Bearer <admin_token>" \
     http://localhost:8000/api/v1/admin/models/config
```

---

### 4. Frontend Deployment

#### 4.1 Rebuild Frontend

```bash
# Navigate to frontend directory
cd /path/to/photo-restoration-webpage/frontend

# Install dependencies (if needed)
npm ci

# Build production bundle
npm run build

# Output will be in frontend/dist directory
```

#### 4.2 Deploy Frontend Build

**For Docker deployments:**
```bash
# Rebuild frontend container
docker-compose build frontend
docker-compose up -d frontend
```

**For static file server (nginx, apache, etc.):**
```bash
# Copy build artifacts to web server
rsync -av frontend/dist/ /var/www/photo-restoration/

# Reload web server
sudo systemctl reload nginx
```

---

### 5. Verification and Testing

#### 5.1 Admin Access Test

1. Login as admin user
2. Navigate to `/admin/models` in the web UI
3. Verify the model configuration page loads
4. Check that default models are listed

#### 5.2 CRUD Operations Test

**Create Test:**
```bash
# Create a test model config via API
curl -X POST http://localhost:8000/api/v1/admin/models/config \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-migration",
    "name": "Migration Test Model",
    "model": "test/model",
    "provider": "huggingface",
    "category": "upscale",
    "description": "Test model for migration verification",
    "enabled": true
  }'

# Verify it appears in local.json
cat backend/config/local.json | jq '.models[] | select(.id=="test-migration")'
```

**Update Test:**
```bash
# Update the test model
curl -X PUT http://localhost:8000/api/v1/admin/models/config/test-migration \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}'
```

**Delete Test:**
```bash
# Delete the test model
curl -X DELETE http://localhost:8000/api/v1/admin/models/config/test-migration \
  -H "Authorization: Bearer <admin_token>"

# Verify it's removed from local.json
cat backend/config/local.json | jq '.models[] | select(.id=="test-migration")'
# Should return empty
```

#### 5.3 Hot Reload Test

1. Create a model via API
2. Manually edit `backend/config/local.json` to change a field
3. Call reload endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/models/reload \
     -H "Authorization: Bearer <admin_token>"
   ```
4. Verify changes are reflected without restarting the backend

#### 5.4 Staging Environment Test (if applicable)

If you have a staging environment:

```bash
# Set APP_ENV to staging
export APP_ENV=staging

# Restart backend
docker-compose restart backend

# Verify no errors in logs (enum should support 'staging' now)
docker-compose logs backend | grep -i "staging"
```

---

### 6. Authorization Verification

Verify that non-admin users **cannot** access model configuration endpoints:

```bash
# Test with regular user token (should get 403 Forbidden)
curl -X GET http://localhost:8000/api/v1/admin/models/config \
  -H "Authorization: Bearer <user_token>"

# Expected response: 403 Forbidden
```

---

### 7. Rollback Procedure

If you need to rollback the feature:

#### 7.1 Restore Previous Code

```bash
# Checkout previous commit
cd /path/to/photo-restoration-webpage
git checkout <previous_commit>

# Rebuild and restart services
docker-compose build
docker-compose up -d
```

#### 7.2 Restore Read-Only Config (Optional)

If you want to restore read-only config volume:

```yaml
# Edit docker-compose.yml
services:
  backend:
    volumes:
      - ./backend/config:/app/config:ro  # Add :ro back
```

```bash
docker-compose down
docker-compose up -d
```

#### 7.3 Preserve Local Configurations

If you want to preserve user-created model configurations:

```bash
# Backup local.json before rollback
cp backend/config/local.json backend/config/local.json.backup

# After rollback, you can restore if needed
cp backend/config/local.json.backup backend/config/local.json
```

---

## Environment-Specific Considerations

### Production Environment

- **Backup First:** Always backup config files before migration
- **Monitoring:** Watch error logs during and after deployment
- **Gradual Rollout:** Consider deploying to staging first
- **Cache Invalidation:** Clear any frontend CDN caches after deployment

### Staging Environment

- **Test Thoroughly:** Test all CRUD operations and hot reload
- **Verify Enum:** Ensure APP_ENV=staging doesn't cause enum errors
- **Load Testing:** Test concurrent admin users modifying configs

### Development Environment

- **Hot Reload:** Verify file watching and hot reload works
- **Permissions:** Ensure development containers have proper file permissions

---

## Troubleshooting

### Issue: "Permission denied" when creating model config

**Cause:** Config directory or local.json is read-only

**Solution:**
```bash
# Check permissions
ls -la backend/config/

# Fix permissions
chmod 644 backend/config/local.json
chown <app_user>:<app_group> backend/config/local.json

# If Docker: verify volume is not mounted :ro
docker inspect <container> | grep -A 5 "Mounts"
```

### Issue: "Model configuration not found" after creation

**Cause:** Config not reloaded or file write failed

**Solution:**
```bash
# Check if model exists in local.json
cat backend/config/local.json | jq '.models'

# Manually reload config
curl -X POST http://localhost:8000/api/v1/admin/models/reload \
  -H "Authorization: Bearer <admin_token>"
```

### Issue: "ValueError: 'staging' is not a valid ModelConfigSource"

**Cause:** Old code version without STAGING enum value

**Solution:**
```bash
# Verify code is up to date
grep -n "STAGING" backend/app/api/v1/schemas/model.py
# Should find: STAGING = "staging"

# If missing, pull latest code and rebuild
git pull origin <branch>
docker-compose build backend
docker-compose restart backend
```

### Issue: Frontend shows "Module has no exported member 'apiClient'"

**Cause:** Old frontend code with incorrect import

**Solution:**
```bash
# Verify frontend code is updated
grep "import \* as api" frontend/src/features/admin/services/modelConfigService.ts
# Should use namespace import, not named import

# Rebuild frontend
cd frontend
npm run build
```

### Issue: Changes to local.json not reflected in API

**Cause:** Config not reloaded after manual file edit

**Solution:**
```bash
# Always call reload endpoint after manual edits
curl -X POST http://localhost:8000/api/v1/admin/models/reload \
  -H "Authorization: Bearer <admin_token>"
```

---

## Post-Migration Checklist

- [ ] Backend service running without errors
- [ ] Frontend accessible and admin page loads
- [ ] Admin user can list model configurations
- [ ] Admin user can create new model configuration
- [ ] New model appears in local.json
- [ ] Admin user can update model configuration
- [ ] Admin user can delete model configuration
- [ ] Non-admin users get 403 on admin endpoints
- [ ] Hot reload endpoint works
- [ ] Config directory has read-write permissions
- [ ] Staging environment works (if applicable)
- [ ] Logs show no enum or import errors
- [ ] Frontend TypeScript compiles without errors

---

## Support and Documentation

- **API Documentation:** `http://<your-domain>/docs` (OpenAPI/Swagger UI)
- **Technical Debts:** See `TECHNICAL_DEBTS.md` items #25-26 for future optimizations
- **Code Review:** See git history for detailed implementation decisions
- **Test Coverage:** `backend/tests/api/v1/test_admin_model_config.py` - 14 comprehensive tests

---

## Summary of Changes

### Files Added
- None (feature uses existing infrastructure)

### Files Modified
- `backend/app/api/v1/routes/admin.py` - Added 8 model config endpoints
- `backend/app/api/v1/schemas/model.py` - Added STAGING to enum, added schemas
- `backend/app/core/config.py` - Added hot reload support
- `frontend/src/features/admin/*` - Added model config UI components
- `docker-compose.yml` - Config volume must be read-write (not :ro)

### Configuration Files
- `backend/config/local.json` - Created for user configurations
- `backend/config/default.json` - Added model_configuration section

### Database Changes
- None required

### Dependencies
- No new Python packages
- No new npm packages

---

## Timeline Estimate

**Small Installation (single server):** 30-60 minutes

**Medium Installation (staging + production):** 2-3 hours

**Large Installation (multiple environments, load balancers):** 4-6 hours

---

## Contacts

For issues during migration:
- Check logs first: `docker-compose logs -f backend`
- Review this migration guide troubleshooting section
- Check git commit history for implementation details
- Run backend tests: `pytest backend/tests/api/v1/test_admin_model_config.py`
