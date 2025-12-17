# Deployment Checklist - Photo Restoration API

## Pre-Deployment Checklist

### 1. Configuration Files

#### ✅ Required Files
- [ ] `backend/config/default.json` - **MUST EXIST** (committed to git)
- [ ] `backend/config/production.json` - Environment-specific config
- [ ] `backend/.env` - Secrets file

#### ✅ For Docker Volume Mounts
If using `-v /opt/retro/config:/app/config`, ensure BOTH files are in the mounted directory:

```bash
# Check files exist
ls -la /opt/retro/config/
# Expected output:
# - default.json (required!)
# - production.json (recommended)

# If default.json is missing:
sudo cp backend/config/default.json /opt/retro/config/

# If production.json is missing:
sudo cp backend/config/production.json.example /opt/retro/config/production.json
sudo nano /opt/retro/config/production.json  # Edit for your environment
```

### 2. Secrets Configuration

Edit `backend/.env` and set:
- [ ] `HF_API_KEY` - HuggingFace API key
- [ ] `REPLICATE_API_TOKEN` - Replicate API token (if using Replicate models)
- [ ] `SECRET_KEY` - JWT signing key (32+ characters, **NOT the default!**)
- [ ] `AUTH_USERNAME` - Admin username
- [ ] `AUTH_PASSWORD` - Admin password (**change from default!**)
- [ ] `APP_ENV=production` - Environment selection

### 3. Production Configuration

Edit `backend/config/production.json`:
- [ ] `cors.origins` - Set to your domain(s)
  ```json
  "origins": ["https://yourdomain.com", "https://www.yourdomain.com"]
  ```
- [ ] `models` - Configure your AI models (4 models by default)
- [ ] `database.url` - Database path (default: `/data/photo_restoration.db`)
- [ ] `file_storage.upload_dir` - Upload directory (default: `/data/uploads`)
- [ ] `file_storage.processed_dir` - Processed directory (default: `/data/processed`)
- [ ] `file_storage.max_upload_size_mb` - Max upload size

### 4. Validation

```bash
# Validate configuration
cd backend
python scripts/validate_config.py --env production

# Expected output:
# ✓ JSON syntax valid: config/production.json
# ✓ Schema validation passed
# ✓ All 4 models are valid (or your model count)
```

## Deployment Steps

### Option A: Docker Build & Deploy

```bash
cd ~/src/photo-restoration-webpage

# 1. Build new image
docker build -t obodnikov/photo-restoration-backend:0.1.8.3 backend/

# 2. Stop and remove old container
docker stop retro-backend
docker rm retro-backend

# 3. Start new container
docker run -d \
  --name retro-backend \
  --ip=172.19.0.20 \
  --network retro \
  -v /opt/retro/data:/data \
  -v /opt/retro/config:/app/config \
  --env-file ./backend.env \
  --restart unless-stopped \
  obodnikov/photo-restoration-backend:0.1.8.3

# 4. Verify startup
docker logs retro-backend
```

### Option B: Docker Compose Deploy

```bash
cd ~/src/photo-restoration-webpage

# 1. Build and start
docker-compose up --build -d

# 2. Verify startup
docker-compose logs backend
```

## Post-Deployment Verification

### 1. Check Startup Logs

```bash
docker logs retro-backend 2>&1 | head -20

# Expected output:
# ✓ Configuration loaded from JSON files (APP_ENV=production)
#   - Models: 4 configured
#   - CORS origins: X configured
#   - Database: /data/photo_restoration.db
# Starting Photo Restoration API v1.8.2
# Environment: production
# Debug mode: False
# Configuration source: JSON config files  <-- IMPORTANT!
# HuggingFace API configured: True
# Available models: 4  <-- Should match your config!
```

### 2. Test API Endpoints

```bash
# Test health endpoint
curl http://172.19.0.20:8000/health

# Expected output:
# {"status":"healthy","service":"Photo Restoration API","version":"1.8.2"}

# Test models endpoint
curl -s http://172.19.0.20:8000/api/v1/models | python3 -m json.tool | grep total

# Expected output:
# "total": 4  <-- Should match your configured models count
```

### 3. Check Frontend

```bash
# Open frontend in browser
# Navigate to: http://yourdomain.com

# Verify:
# - Login page loads
# - After login, model selector shows all 4 models (or your count)
# - Can upload and process images
```

## Troubleshooting

### Issue: Only 1 Model Showing

**Symptoms:**
- API returns `"total": 1`
- Logs show: `Configuration source: .env only (DEPRECATED)`
- Logs show: `Default config not found: /app/config/default.json`

**Cause:** `default.json` is missing from the config directory

**Fix:**
```bash
# Copy default.json to mounted directory
sudo cp backend/config/default.json /opt/retro/config/

# Restart container
docker restart retro-backend

# Verify
docker logs retro-backend 2>&1 | grep "Configuration source"
# Should show: "Configuration source: JSON config files"
```

### Issue: Wrong CORS Origins

**Symptoms:**
- Frontend can't connect to backend
- Browser console shows CORS errors

**Fix:**
```bash
# Edit production.json
sudo nano /opt/retro/config/production.json

# Update cors.origins to include your domain:
"cors": {
  "origins": [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
  ]
}

# Restart
docker restart retro-backend
```

### Issue: Models Not Loading

**Check:**
1. Is `default.json` present?
2. Does `production.json` have a `models` array?
3. Are all model entries valid?

```bash
# Validate
cd backend
python scripts/validate_config.py --env production

# Check specific model count
cat /opt/retro/config/production.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Models: {len(d.get('models', []))}\")"
```

### Enable Debug Logging

To see detailed configuration in logs:

```bash
# Add to backend.env
echo "DEBUG=true" >> backend.env

# OR edit production.json
sudo nano /opt/retro/config/production.json
# Set: "debug": true

# Restart
docker restart retro-backend

# View detailed logs
docker logs retro-backend 2>&1 | grep -A 20 "Configuration Details"
```

## Rollback Procedure

If deployment fails:

```bash
# Stop new container
docker stop retro-backend
docker rm retro-backend

# Start old version
docker run -d \
  --name retro-backend \
  --ip=172.19.0.20 \
  --network retro \
  -v /opt/retro/data:/data \
  -v /opt/retro/config:/app/config \
  --env-file ./backend.env \
  --restart unless-stopped \
  obodnikov/photo-restoration-backend:0.1.8.2  # Previous version
```

## Success Criteria

Deployment is successful when:

- [x] Startup logs show: `Configuration source: JSON config files`
- [x] Startup logs show: `Available models: X` (matches your config)
- [x] `/api/v1/models` returns correct model count
- [x] Frontend shows all configured models
- [x] Can successfully upload and process images
- [x] CORS works (no browser errors)
- [x] Authentication works (can login)

## Maintenance

### Update Models Configuration

```bash
# Edit production.json
sudo nano /opt/retro/config/production.json

# Add/edit models in the "models" array

# Validate
cd backend
python scripts/validate_config.py --env production

# Restart to apply changes
docker restart retro-backend
```

### View Current Configuration

```bash
# See what's loaded (requires DEBUG=true)
docker logs retro-backend 2>&1 | grep -A 30 "Configuration Details"

# Or check files directly
cat /opt/retro/config/production.json | python3 -m json.tool
```

## Related Documentation

- [README.md](../README.md) - Main documentation
- [backend/config/README.md](../backend/config/README.md) - Configuration details
- [PHASE_1.8.2_SUMMARY.md](./PHASE_1.8.2_SUMMARY.md) - Configuration system overview
- [FIX_MODELS_LOADING.md](./FIX_MODELS_LOADING.md) - Models loading fix details
