# Fix: Frontend Only Loading First Model

**Date:** December 17, 2025
**Issue:** Frontend displaying only 1 model instead of all 4 models from production.json
**Status:** ✅ FIXED

## Problem

The backend API endpoint `/api/v1/models` was returning only 1 model despite having 4 models configured in `backend/config/production.json`.

## Root Cause

Two issues were identified:

### Issue 1: Models API Using Old String-Based Config
**File:** [backend/app/api/v1/routes/models.py](../backend/app/api/v1/routes/models.py)

The models API was using `settings.models_config` (old environment variable string) instead of `settings.get_models()` (new method that loads from JSON config files).

**Fix:**
```python
# Before:
def _parse_models_config(models_config: str) -> list[ModelInfo]:
    models_data = json.loads(models_config)
    return [ModelInfo(**model) for model in models_data]

def get_cached_models(settings: Settings) -> list[ModelInfo]:
    return _parse_models_config(settings.models_config)

# After:
def get_cached_models(settings: Settings) -> list[ModelInfo]:
    models_data = settings.get_models()
    return [ModelInfo(**model) for model in models_data]
```

### Issue 2: Config Flags Being Reset by Pydantic
**File:** [backend/app/core/config.py](../backend/app/core/config.py:215-217)

The `_using_json_config` and `_config_data` flags were set BEFORE calling `super().__init__()`, causing Pydantic to reset them to class-level defaults during initialization.

**Fix:**
```python
# Before:
def __init__(self, **kwargs: Any):
    # ... load config ...
    self._using_json_config = True
    self._config_data = config_data
    super().__init__(**kwargs)

# After:
def __init__(self, **kwargs: Any):
    # ... load config ...
    using_json = True
    config_data_dict = config_data
    super().__init__(**kwargs)

    # Set flags AFTER Pydantic initialization
    self._using_json_config = using_json
    self._config_data = config_data_dict
```

## Changes Made

### 1. Updated Models API Route
**File:** [backend/app/api/v1/routes/models.py](../backend/app/api/v1/routes/models.py:16-27)
- Removed `_parse_models_config()` function
- Updated `get_cached_models()` to use `settings.get_models()`

### 2. Fixed Config Initialization
**File:** [backend/app/core/config.py](../backend/app/core/config.py:178-217)
- Store config flags in local variables before `super().__init__()`
- Set instance attributes AFTER Pydantic initialization

### 3. Added Configuration Logging
**File:** [backend/app/core/config.py](../backend/app/core/config.py:219-244)

Added comprehensive logging to track configuration loading:

**Standard Logging (INFO level):**
```
✓ Configuration loaded from JSON files (APP_ENV=production)
  - Models: 4 configured
  - CORS origins: 4 configured
  - Database: sqlite+aiosqlite:///data/photo_restoration.db
```

**Debug Logging (when DEBUG=true):**
```
=== Configuration Details (DEBUG mode) ===
  App: Photo Restoration API v0.1.2
  Server: 0.0.0.0:8000
  Debug: True
  CORS origins: ['http://localhost:8000', ...]
  Models (4):
    - swin2sr-2x: Swin2SR 2x Upscale (huggingface)
    - swin2sr-4x: Swin2SR 4x Upscale (huggingface)
    - qwen-edit: Qwen Image Enhance (huggingface)
    - replicate-restore: Replicate Photo Restore (replicate)
  Upload dir: /data/uploads
  Processed dir: /data/processed
  Max upload size: 29.0MB
==================================================
```

### 4. Enhanced Startup Logging
**File:** [backend/app/main.py](../backend/app/main.py:23-28)

Added configuration source to startup logs:
```
Starting Photo Restoration API v1.8.2
Environment: production
Debug mode: False
Configuration source: JSON config files
HuggingFace API configured: True
Available models: 4
```

### 5. Updated Tests
**File:** [backend/tests/api/v1/test_models.py](../backend/tests/api/v1/test_models.py:65-70)
- Removed cache clearing from fixtures (no longer needed)
- Renamed test to `test_settings_override_refreshes_models`

## Testing

### Unit Tests
```bash
cd backend
source venv/bin/activate
python -m pytest tests/api/v1/test_models.py -v
```

**Result:** 17/17 tests passing ✅

### Manual Verification
```bash
# Test config loading
python -c "from app.core.config import Settings; s = Settings(app_env='production'); print(f'Models: {len(s.get_models())}')"
# Output: Models: 4

# Test API endpoint (after rebuild)
curl http://172.19.0.20:8000/api/v1/models | python3 -m json.tool
# Expected: {"models": [...], "total": 4}
```

## Deployment

### For Docker Deployment

The fix requires rebuilding the Docker image since the code has changed:

```bash
cd ~/src/photo-restoration-webpage

# Build new image
docker build -t obodnikov/photo-restoration-backend:0.1.8.3 backend/

# Stop current container
docker stop retro-backend
docker rm retro-backend

# Start with new image
docker run -d \
  --name retro-backend \
  --ip=172.19.0.20 \
  --network retro \
  -v /opt/retro/data:/data \
  -v /opt/retro/config:/app/config \
  --env-file ./backend.env \
  --restart unless-stopped \
  obodnikov/photo-restoration-backend:0.1.8.3

# Verify (should show 4 models)
curl -s http://172.19.0.20:8000/api/v1/models | python3 -m json.tool | grep total
```

### Check Logs

After deployment, verify the configuration loaded correctly:

```bash
# View container logs
docker logs retro-backend

# Expected output:
# ✓ Configuration loaded from JSON files (APP_ENV=production)
#   - Models: 4 configured
#   - CORS origins: 4 configured
#   ...
# Starting Photo Restoration API v1.8.2
# Environment: production
# Configuration source: JSON config files
# Available models: 4
```

### Enable Debug Logging (Optional)

To see detailed configuration in logs, set `DEBUG=true` in `backend.env`:

```bash
echo "DEBUG=true" >> backend.env
docker restart retro-backend
docker logs retro-backend
```

You'll see:
```
=== Configuration Details (DEBUG mode) ===
  Models (4):
    - swin2sr-2x: Swin2SR 2x Upscale (huggingface)
    - swin2sr-4x: Swin2SR 4x Upscale (huggingface)
    - qwen-edit: Qwen Image Enhance (huggingface)
    - replicate-restore: Replicate Photo Restore (replicate)
  ...
```

## Verification Checklist

- [x] Config loading fixed (flags set after Pydantic init)
- [x] Models API updated to use `get_models()`
- [x] Configuration logging added
- [x] Startup logging enhanced
- [x] Tests updated and passing (17/17)
- [x] Manual testing verified (4 models loaded)
- [ ] Docker image rebuilt with fixes
- [ ] Backend redeployed on production server
- [ ] Frontend confirmed showing all 4 models

## Related Files

- [backend/app/core/config.py](../backend/app/core/config.py) - Config loading with logging
- [backend/app/api/v1/routes/models.py](../backend/app/api/v1/routes/models.py) - Models API
- [backend/app/main.py](../backend/app/main.py) - Startup logging
- [backend/tests/api/v1/test_models.py](../backend/tests/api/v1/test_models.py) - Tests
- [backend/config/production.json](../backend/config/production.json) - Production config (4 models)

## See Also

- [PHASE_1.8.2_SUMMARY.md](./PHASE_1.8.2_SUMMARY.md) - Configuration system implementation
- [PHASE_1.8.2_TEST_REPORT.md](./PHASE_1.8.2_TEST_REPORT.md) - Test results
