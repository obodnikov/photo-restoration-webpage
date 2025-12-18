# DEBUG Logging Implementation

**Phase:** 1.9 - Testing & Quality Assurance
**Date:** December 18, 2024
**Status:** ✅ COMPLETE

## Overview

Comprehensive DEBUG logging has been implemented throughout the backend application. Logging is controlled by the `DEBUG` environment variable and provides detailed visibility into application operations for troubleshooting and monitoring.

## Configuration

### Enable DEBUG Logging

Set the `DEBUG` environment variable in your `.env` file or Docker environment:

```bash
# In .env
DEBUG=true
```

### Log Levels

The application uses Python's standard logging levels:

- **DEBUG**: Detailed diagnostic information (only when DEBUG=true)
- **INFO**: General informational messages (always shown)
- **WARNING**: Warning messages for unexpected but non-critical issues
- **ERROR**: Error messages for failures

### Log Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example:
```
2024-12-18 10:30:45,123 - app.main - INFO - Starting Photo Restoration API v1.8.2
2024-12-18 10:30:45,456 - app.api.v1.routes.auth - DEBUG - Login attempt for user: admin
```

## Logging Coverage

### 1. Application Startup ([app/main.py](../backend/app/main.py))

**INFO level:**
- Application name and version
- Environment (production/development/staging)
- Debug mode status
- Configuration source (JSON config vs .env)
- HuggingFace API configuration status
- Available models count
- Database initialization
- Cleanup scheduler status

**DEBUG level (when DEBUG=true):**
- Config directory paths
- Upload/processed directory paths
- Database URL
- CORS origins
- Complete models configuration (all model details)

Example output:
```
INFO - Starting Photo Restoration API v1.8.2
INFO - Environment: production
INFO - Debug mode: True
INFO - Configuration source: JSON config files
INFO - HuggingFace API configured: True
INFO - Available models: 4
DEBUG - === DEBUG MODE ENABLED ===
DEBUG - Config directory: /data
DEBUG - Upload directory: /data/uploads
DEBUG - Processed directory: /data/processed
DEBUG - Database URL: sqlite+aiosqlite:///data/photo_restoration.db
DEBUG - CORS origins: ['https://yourdomain.com']
DEBUG - Models configuration:
DEBUG -   - swin2sr-2x: Swin2SR 2x Upscale (huggingface)
DEBUG -   - swin2sr-4x: Swin2SR 4x Upscale (huggingface)
DEBUG -   - qwen-edit: Qwen Image Enhance (huggingface)
DEBUG -   - replicate-restore: Replicate Photo Restore (replicate)
```

### 2. Authentication ([app/api/v1/routes/auth.py](../backend/app/api/v1/routes/auth.py))

**INFO level:**
- Login attempts (username only, password never logged)
- Successful logins with token expiration
- Session creation
- "Remember Me" usage

**WARNING level:**
- Failed login attempts

**DEBUG level:**
- Token validation
- User info requests

Example:
```
INFO - Login attempt for user: admin
INFO - Created session abc123... for user admin
INFO - User admin logged in successfully (expires in 1440 minutes)
WARNING - Failed login attempt for user: baduser - Invalid credentials
DEBUG - Token validated for user: admin
```

### 3. Image Restoration ([app/api/v1/routes/restoration.py](../backend/app/api/v1/routes/restoration.py))

**INFO level:**
- Processing start (model ID, provider, session ID)

**DEBUG level:**
- Restore request details (user, session, model, filename)
- Concurrent upload limit checks
- File validation steps
- File read operations with byte counts
- Image preprocessing details
- Model provider selection

**WARNING level:**
- Invalid image formats
- Image size errors
- Validation failures

**ERROR level:**
- File read failures
- Preprocessing failures

Example:
```
DEBUG - Restore request - User: admin, Session: abc123..., Model: swin2sr-2x, File: old_photo.jpg
DEBUG - Checking concurrent upload limit for session abc123...
DEBUG - Concurrent upload check passed for session abc123...
DEBUG - Validating upload file: old_photo.jpg (image/jpeg)
DEBUG - File validation passed for: old_photo.jpg
DEBUG - Reading file bytes: old_photo.jpg
DEBUG - Read 125834 bytes from old_photo.jpg
DEBUG - Preprocessing image for model
DEBUG - Preprocessed image: 125834 bytes
INFO - Processing image with model swin2sr-2x (provider: huggingface) for session abc123...
```

### 4. HuggingFace Inference ([app/services/hf_inference.py](../backend/app/services/hf_inference.py))

**INFO level:**
- Processing start (model path, category)
- Input image details (format, size, mode)
- Processing method selection (image_to_image, prompts)
- Successful processing completion

**ERROR level:**
- API errors with full exception details

Example:
```
INFO - Processing image with model: caidas/swin2SR-classical-sr-x2-64, category: upscale
INFO - Input image: JPEG, (1024, 768), RGB
INFO - Using image_to_image for upscaling
INFO - Successfully processed image with caidas/swin2SR-classical-sr-x2-64
```

### 5. Replicate Inference ([app/services/replicate_inference.py](../backend/app/services/replicate_inference.py))

**INFO level:**
- Processing start (model path, category)
- Input image details
- Replicate call parameters
- Output type returned
- URL download or data URI decode operations

Example:
```
INFO - Processing image with Replicate model: flux-kontext-apps/restore-image, category: restore
INFO - Input image: JPEG, (1024, 768), RGB
INFO - Calling Replicate model flux-kontext-apps/restore-image with parameters: ['input_image']
INFO - Replicate model returned output type: <class 'str'>
INFO - Downloaded output image from URL: 245678 bytes
```

### 6. Session Manager ([app/services/session_manager.py](../backend/app/services/session_manager.py))

**Logging added:**
- Session creation logging
- Session retrieval logging
- Image storage operations
- Cleanup operations

**Note:** Logging infrastructure added (logger configured), detailed DEBUG logging to be added in Phase 2+.

### 7. Configuration Loading ([app/core/config.py](../backend/app/core/config.py))

**INFO level:**
- Configuration source selection
- Model count from configuration

**WARNING level:**
- Deprecated .env-only usage
- Missing configuration files
- Fallback to defaults

**DEBUG level:**
- JSON config file loading details
- Environment variable overrides
- Deep merge operations
- Complete configuration after loading

Example:
```
WARNING - Default config not found: /app/config/default.json
WARNING - Using .env-only configuration (DEPRECATED)
WARNING - Please migrate to JSON config: python scripts/migrate_env_to_config.py
INFO - Loaded configuration from JSON config files
INFO - Configuration contains 4 models
DEBUG - Loading JSON config from: /app/config/default.json
DEBUG - Loading environment-specific config: /app/config/production.json
DEBUG - Applying environment variable overrides
DEBUG - Final configuration: {...}
```

## Benefits

### 1. **Troubleshooting**
- Trace complete request flow from upload to processing
- Identify bottlenecks and failures quickly
- Understand configuration loading issues

### 2. **Monitoring**
- Track authentication patterns
- Monitor model usage
- Identify performance issues

### 3. **Security**
- Audit login attempts
- Track failed authentication
- Monitor session usage
- **Passwords are NEVER logged**

### 4. **Development**
- Detailed debugging information
- Configuration validation
- Model behavior understanding

## Usage Examples

### Example 1: Debug Configuration Issues

**Problem:** Frontend only showing 1 model instead of 4

**Solution with DEBUG logging:**
```bash
# Enable DEBUG mode
export DEBUG=true

# Restart backend
docker restart retro-backend

# Check logs
docker logs retro-backend 2>&1 | grep -E "(Configuration source|Available models|Models configuration)"
```

**Output reveals:**
```
INFO - Configuration source: .env only (DEPRECATED)
INFO - Available models: 1
```

**Fix:** Copy default.json to config directory, restart

**Verification:**
```
INFO - Configuration source: JSON config files
INFO - Available models: 4
DEBUG - Models configuration:
DEBUG -   - swin2sr-2x: Swin2SR 2x Upscale (huggingface)
DEBUG -   - swin2sr-4x: Swin2SR 4x Upscale (huggingface)
DEBUG -   - qwen-edit: Qwen Image Enhance (huggingface)
DEBUG -   - replicate-restore: Replicate Photo Restore (replicate)
```

### Example 2: Debug Image Processing Failure

**Problem:** Image upload returns 400 error

**With DEBUG logging:**
```
DEBUG - Restore request - User: admin, Session: abc123, Model: swin2sr-2x, File: photo.bmp
DEBUG - Validating upload file: photo.bmp (image/bmp)
WARNING - Invalid image format: photo.bmp - Only JPEG and PNG formats are supported
```

**Root cause identified:** BMP format not supported

### Example 3: Monitor Authentication

```bash
# Watch auth logs
docker logs -f retro-backend 2>&1 | grep -E "(Login attempt|Failed login|logged in)"
```

**Output:**
```
INFO - Login attempt for user: admin
INFO - User admin logged in successfully (expires in 1440 minutes)
INFO - Login attempt for user: hacker
WARNING - Failed login attempt for user: hacker - Invalid credentials
```

## Performance Considerations

### DEBUG Mode Impact

**Enabled (DEBUG=true):**
- More detailed logs = more I/O operations
- Slightly higher memory usage for log buffers
- Minimal CPU impact
- **Recommended:** Use in development/staging only

**Disabled (DEBUG=false):**
- Only INFO/WARNING/ERROR logs
- Minimal performance impact
- **Recommended:** Use in production (enable temporarily for troubleshooting)

### Log Rotation

For production deployments, configure log rotation to prevent disk space issues:

**Docker logging driver:**
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Systemd logging:**
```bash
journalctl --vacuum-size=100M
journalctl --vacuum-time=7d
```

## Security Notes

### What is NEVER Logged

✅ **Safe:**
- Usernames (for audit trail)
- Session IDs (for request tracking)
- File names
- Model IDs
- Image sizes and formats
- API endpoints called

❌ **NEVER Logged:**
- Passwords (always excluded)
- API keys (redacted if shown)
- Complete JWT tokens (only mentioned as "token validated")
- Sensitive personal data
- Full image contents

### Security Best Practices

1. **Sanitize logs before sharing**: Remove session IDs and usernames when sharing logs publicly
2. **Use DEBUG=false in production**: Only enable for troubleshooting
3. **Rotate logs regularly**: Prevent log files from growing indefinitely
4. **Monitor failed login attempts**: Watch WARNING logs for authentication failures
5. **Secure log files**: Restrict access to log files (root/admin only)

## Testing DEBUG Logging

### Test DEBUG Mode Locally

```bash
cd backend
source venv/bin/activate

# Set DEBUG=true
export DEBUG=true

# Run application
uvicorn app.main:app --reload

# Watch logs in another terminal
tail -f *.log

# Test with curl
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### Test in Docker

```bash
# Build with DEBUG enabled
docker build -t backend:debug \
  --build-arg DEBUG=true \
  backend/

# Run and watch logs
docker run -it --rm \
  --env-file backend/.env \
  -e DEBUG=true \
  backend:debug
```

## Future Enhancements (Phase 2+)

- [ ] Structured JSON logging for machine parsing
- [ ] Correlation IDs for request tracing
- [ ] Performance metrics logging (timing, memory)
- [ ] Aggregated logging with ELK stack support
- [ ] Real-time log streaming dashboard
- [ ] Automatic error alerting (email/Slack)
- [ ] Log sampling for high-traffic scenarios

## Related Documentation

- [Configuration Documentation](./configuration.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [Phase 1.8.2 Summary](./PHASE_1.8.2_SUMMARY.md)
- [ROADMAP - Phase 1.9](../ROADMAP.md#19-testing--quality-assurance)

---

**Document Version:** 1.0
**Last Updated:** December 18, 2024
**Phase:** 1.9 - Testing & Quality Assurance ✅
