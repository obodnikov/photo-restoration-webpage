# Configuration Reference

Auto-generated configuration documentation. Last updated: 2025-12-18 09:14

## Table of Contents

- [Application](#application)
- [Server](#server)
- [Cors](#cors)
- [Security](#security)
- [Api Providers](#api_providers)
- [Models](#models)
- [Models Api](#models_api)
- [Database](#database)
- [File Storage](#file_storage)
- [Session](#session)
- [Processing](#processing)

## Overview

This document provides a complete reference for all configuration options in the Photo Restoration API.

Configuration is loaded from JSON files in the `config/` directory based on the `APP_ENV` environment variable.

**Loading Priority** (highest to lowest):
1. Environment variables (from `.env` file)
2. Environment-specific config (`config/{APP_ENV}.json`)
3. Default config (`config/default.json`)

## Configuration Sections

## Application

<a id="application"></a>

### `application.name`

Application name displayed in logs and API responses

- **Type:** `string`
- **Required:** No
- **Default:** `"Photo Restoration API"`
- **Environment Override:** `APPLICATION_NAME`

### `application.version`

Application version

- **Type:** `string`
- **Required:** No
- **Default:** `"1.8.2"`
- **Environment Override:** `APPLICATION_VERSION`

### `application.debug`

Enable debug mode (verbose logging, detailed errors)

- **Type:** `boolean`
- **Required:** No
- **Default:** `False`
- **Environment Override:** `APPLICATION_DEBUG`

### `application.log_level`

Logging level for the application

- **Type:** `string`
- **Required:** No
- **Default:** `"INFO"`
- **Choices:** "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
- **Environment Override:** `APPLICATION_LOG_LEVEL`

---

## Server

<a id="server"></a>

### `server.host`

Server host address

- **Type:** `string`
- **Required:** No
- **Default:** `"0.0.0.0"`
- **Environment Override:** `SERVER_HOST`

### `server.port`

Server port number

- **Type:** `integer`
- **Required:** No
- **Default:** `8000`
- **Minimum:** `1`
- **Maximum:** `65535`
- **Environment Override:** `SERVER_PORT`

### `server.workers`

Number of worker processes

- **Type:** `integer`
- **Required:** No
- **Default:** `1`
- **Minimum:** `1`
- **Maximum:** `16`
- **Environment Override:** `SERVER_WORKERS`

---

## Cors

<a id="cors"></a>

### `cors.origins`

Allowed CORS origins for cross-origin requests

- **Type:** `array`
- **Required:** No
- **Default:** `["http://localhost:3000", "http://localhost"]`
- **Environment Override:** `CORS_ORIGINS`

### `cors.allow_credentials`

Allow credentials in CORS requests

- **Type:** `boolean`
- **Required:** No
- **Default:** `True`
- **Environment Override:** `CORS_ALLOW_CREDENTIALS`

### `cors.allow_methods`

Allowed HTTP methods

- **Type:** `array`
- **Required:** No
- **Default:** `["GET", "POST", "PUT", "DELETE", "OPTIONS"]`
- **Environment Override:** `CORS_ALLOW_METHODS`

### `cors.allow_headers`

Allowed HTTP headers

- **Type:** `array`
- **Required:** No
- **Default:** `["*"]`
- **Environment Override:** `CORS_ALLOW_HEADERS`

---

## Security

<a id="security"></a>

### `security.algorithm`

JWT token signing algorithm

- **Type:** `string`
- **Required:** No
- **Default:** `"HS256"`
- **Environment Override:** `SECURITY_ALGORITHM`

### `security.access_token_expire_minutes`

Access token expiration time in minutes (default: 24 hours)

- **Type:** `integer`
- **Required:** No
- **Default:** `1440`
- **Minimum:** `1`
- **Environment Override:** `SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES`

### `security.remember_me_expire_days`

Remember me token expiration in days

- **Type:** `integer`
- **Required:** No
- **Default:** `7`
- **Minimum:** `1`
- **Environment Override:** `SECURITY_REMEMBER_ME_EXPIRE_DAYS`

---

## Api Providers

<a id="api_providers"></a>

### `api_providers.huggingface`

HuggingFace API provider configuration.

- **Type:** `object`
- **Required:** No
- **Environment Override:** `API_PROVIDERS_HUGGINGFACE`

### `api_providers.replicate`

Replicate API provider configuration.

- **Type:** `object`
- **Required:** No
- **Environment Override:** `API_PROVIDERS_REPLICATE`

---

## Models

<a id="models"></a>

---

## Models Api

<a id="models_api"></a>

### `models_api.require_auth`

Require authentication for model list/details endpoints

- **Type:** `boolean`
- **Required:** No
- **Default:** `False`
- **Environment Override:** `MODELS_API_REQUIRE_AUTH`

### `models_api.cache_ttl_seconds`

Cache TTL for models list in seconds (0 = no cache)

- **Type:** `integer`
- **Required:** No
- **Default:** `300`
- **Minimum:** `0`
- **Environment Override:** `MODELS_API_CACHE_TTL_SECONDS`

---

## Database

<a id="database"></a>

### `database.url`

Database connection URL (SQLAlchemy format)

- **Type:** `string`
- **Required:** No
- **Default:** `"sqlite+aiosqlite:///./data/photo_restoration.db"`
- **Environment Override:** `DATABASE_URL`

### `database.echo_sql`

Echo SQL queries to console (debug mode)

- **Type:** `boolean`
- **Required:** No
- **Default:** `False`
- **Environment Override:** `DATABASE_ECHO_SQL`

### `database.pool_size`

Database connection pool size

- **Type:** `integer`
- **Required:** No
- **Default:** `5`
- **Minimum:** `1`
- **Environment Override:** `DATABASE_POOL_SIZE`

### `database.max_overflow`

Maximum overflow connections

- **Type:** `integer`
- **Required:** No
- **Default:** `10`
- **Minimum:** `0`
- **Environment Override:** `DATABASE_MAX_OVERFLOW`

---

## File Storage

<a id="file_storage"></a>

### `file_storage.upload_dir`

Directory for uploaded images

- **Type:** `string`
- **Required:** No
- **Default:** `"./data/uploads"`
- **Environment Override:** `FILE_STORAGE_UPLOAD_DIR`

### `file_storage.processed_dir`

Directory for processed images

- **Type:** `string`
- **Required:** No
- **Default:** `"./data/processed"`
- **Environment Override:** `FILE_STORAGE_PROCESSED_DIR`

### `file_storage.max_upload_size_mb`

Maximum file upload size in MB

- **Type:** `integer`
- **Required:** No
- **Default:** `10`
- **Minimum:** `1`
- **Maximum:** `100`
- **Environment Override:** `FILE_STORAGE_MAX_UPLOAD_SIZE_MB`

### `file_storage.allowed_extensions`

Allowed file extensions

- **Type:** `array`
- **Required:** No
- **Default:** `[".jpg", ".jpeg", ".png"]`
- **Environment Override:** `FILE_STORAGE_ALLOWED_EXTENSIONS`

### `file_storage.image_quality`

JPEG quality for saved images (1-100)

- **Type:** `integer`
- **Required:** No
- **Default:** `95`
- **Minimum:** `1`
- **Maximum:** `100`
- **Environment Override:** `FILE_STORAGE_IMAGE_QUALITY`

---

## Session

<a id="session"></a>

### `session.cleanup_hours`

Delete sessions older than this many hours (inactivity threshold)

- **Type:** `integer`
- **Required:** No
- **Default:** `24`
- **Minimum:** `1`
- **Environment Override:** `SESSION_CLEANUP_HOURS`

### `session.cleanup_interval_hours`

How often to run cleanup task (in hours)

- **Type:** `integer`
- **Required:** No
- **Default:** `6`
- **Minimum:** `1`
- **Environment Override:** `SESSION_CLEANUP_INTERVAL_HOURS`

### `session.max_age_hours`

Maximum session age in hours (7 days default)

- **Type:** `integer`
- **Required:** No
- **Default:** `168`
- **Minimum:** `1`
- **Environment Override:** `SESSION_MAX_AGE_HOURS`

---

## Processing

<a id="processing"></a>

### `processing.max_concurrent_uploads_per_session`

Maximum concurrent uploads per session

- **Type:** `integer`
- **Required:** No
- **Default:** `3`
- **Minimum:** `1`
- **Environment Override:** `PROCESSING_MAX_CONCURRENT_UPLOADS_PER_SESSION`

### `processing.queue_size`

Maximum queue size for processing tasks

- **Type:** `integer`
- **Required:** No
- **Default:** `100`
- **Minimum:** `1`
- **Environment Override:** `PROCESSING_QUEUE_SIZE`

---

## Examples

### Minimal Configuration

```json
{
  "application": {
    "name": "Photo Restoration API"
  },
  "models": [
    {
      "id": "swin2sr-2x",
      "name": "Swin2SR 2x",
      "model": "caidas/swin2SR-classical-sr-x2-64",
      "provider": "huggingface",
      "category": "upscale",
      "description": "Fast 2x upscaling"
    }
  ]
}
```

### Production Configuration

See `config/production.json.example` for a complete production example.

### Development Configuration

See `config/development.json.example` for a development example with debug settings.

## Secrets

The following values should **never** be in config files. They must be in the `.env` file:

- `HF_API_KEY` - HuggingFace API key
- `REPLICATE_API_TOKEN` - Replicate API token
- `SECRET_KEY` - JWT secret key (minimum 32 characters)
- `AUTH_USERNAME` - Authentication username
- `AUTH_PASSWORD` - Authentication password

## Validation

Validate your configuration:

```bash
python scripts/validate_config.py --env production
```

## Replicate Model Schema Configuration

For Replicate models, you can define a detailed schema that enables parameter validation, frontend UI generation, and custom constraints.

### Schema Structure

```json
{
  "id": "replicate-restore",
  "model": "flux-kontext-apps/restore-image",
  "provider": "replicate",
  "replicate_schema": {
    "input": {
      "image": {
        "param_name": "input_image",
        "type": "uri",
        "format": "image",
        "required": true,
        "description": "Image to restore"
      },
      "parameters": [
        {
          "name": "output_format",
          "type": "enum",
          "values": ["jpg", "png"],
          "default": "png",
          "required": false,
          "description": "Output image format",
          "ui_hidden": false,
          "ui_group": "output"
        },
        {
          "name": "quality",
          "type": "integer",
          "min": 1,
          "max": 100,
          "default": 80,
          "required": false,
          "description": "Output quality",
          "ui_group": "quality"
        }
      ]
    },
    "output": {
      "type": "uri",
      "format": "image"
    },
    "custom": {
      "max_file_size_mb": 10,
      "supported_formats": ["jpg", "jpeg", "png", "webp"],
      "estimated_time_seconds": 30
    }
  }
}
```

### Schema Fields

#### `input.image`
- `param_name` (string): Replicate API parameter name for image input
- `type` (string): Always "uri" for Replicate
- `format` (string): "image"
- `required` (boolean): Always true
- `description` (string): Human-readable description

#### `input.parameters[]`
- `name` (string): Parameter name as expected by Replicate API
- `type` (enum): "string", "integer", "float", "boolean", "enum"
- `required` (boolean): Whether parameter is required
- `description` (string): Parameter description
- `default` (any): Default value if not provided
- `min` / `max` (number): For integer/float types
- `values` (array): For enum type - allowed values
- `ui_hidden` (boolean): Hide from frontend UI
- `ui_group` (string): Group parameters in UI (e.g., "output", "quality")

#### `output`
- `type` (enum): "uri", "base64", "json", "list"
- `format` (string): "image", "text", etc.

#### `custom` (Application-specific)
- `max_file_size_mb` (number): Maximum input file size
- `supported_formats` (array): Allowed input formats
- `estimated_time_seconds` (number): Estimated processing time

### Parameter Types

**string**: Text value
```json
{"name": "prompt", "type": "string", "default": "enhance image"}
```

**integer**: Whole number with optional min/max
```json
{"name": "steps", "type": "integer", "min": 1, "max": 100, "default": 50}
```

**float**: Decimal number with optional min/max
```json
{"name": "scale", "type": "float", "min": 0.1, "max": 2.0, "default": 1.0}
```

**boolean**: True/false value
```json
{"name": "enable_upscale", "type": "boolean", "default": true}
```

**enum**: One of predefined values
```json
{"name": "format", "type": "enum", "values": ["jpg", "png"], "default": "png"}
```

### Generating Schemas from Replicate API

Use the provided utility to fetch schemas automatically:

```bash
# Fetch schema for a model
python backend/scripts/fetch_replicate_schema.py flux-kontext-apps/restore-image

# Save to file
python backend/scripts/fetch_replicate_schema.py google/upscaler -o schema.json

# With API token
export REPLICATE_API_TOKEN=your_token
python backend/scripts/fetch_replicate_schema.py model-owner/model-name
```

The utility outputs a `replicate_schema` object that you can copy into your model configuration. You'll need to manually adjust:
- `ui_hidden` flags
- `ui_group` assignments
- `custom.max_file_size_mb`
- `custom.supported_formats`
- `custom.estimated_time_seconds`

### Frontend Integration

Models with schemas automatically expose parameters in the API response:

```json
GET /api/v1/models

{
  "models": [
    {
      "id": "replicate-restore",
      "name": "Replicate Photo Restore",
      "schema": {
        "parameters": [
          {
            "name": "output_format",
            "type": "enum",
            "values": ["jpg", "png"],
            "default": "png",
            "ui_group": "output"
          }
        ],
        "custom": {
          "max_file_size_mb": 10,
          "supported_formats": ["jpg", "jpeg", "png"],
          "estimated_time_seconds": 30
        }
      }
    }
  ]
}
```

Parameters marked with `ui_hidden: true` are not included in the API response.

### Using Parameters in Restoration Requests

Pass parameters as JSON string in the `parameters` field:

```bash
curl -X POST http://localhost:8000/api/v1/restore \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@photo.jpg" \
  -F "model_id=replicate-restore" \
  -F 'parameters={"output_format": "jpg", "quality": 95}'
```

Parameters are validated against the schema:
- Type checking (integer, string, boolean, enum)
- Range validation (min/max)
- Enum value validation
- Required parameter checking
- Defaults applied for missing optional parameters

Invalid parameters trigger warnings (logged) and fallback to defaults.

## Migration

Migrate from `.env` to JSON config:

```bash
python scripts/migrate_env_to_config.py --env-file .env --output config/production.json
```
