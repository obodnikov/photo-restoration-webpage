# Flexible Replicate Schema Implementation

**Date**: 2025-12-18
**Status**: Completed

## Overview

Implemented a flexible schema-based configuration system for Replicate models that eliminates hardcoded assumptions and enables:
- Dynamic parameter validation
- Frontend UI generation
- Custom constraints per model
- Easy addition of new models

## Problem Statement

Previously, Replicate model integration was hardcoded:
- Fixed `input_param_name` for image input
- No parameter validation
- No schema awareness
- Each model required custom code changes

Each Replicate model has unique input/output schemas documented in their API (e.g., `https://replicate.com/flux-kontext-apps/restore-image/api/schema`).

## Solution

Implemented a comprehensive schema system with:

1. **Schema Definition Language** - JSON-based schema in config files
2. **Parameter Validation** - Type checking, constraints, defaults
3. **Frontend Integration** - Schema exposed via API for UI generation
4. **CLI Utility** - Auto-generate schemas from Replicate API

## Architecture

```
Config File (replicate_schema)
        ↓
Pydantic Models (validation)
        ↓
SchemaValidator (runtime validation)
        ↓
ReplicateInferenceService (API calls)
        ↓
Frontend (parameter UI)
```

## Implementation Details

### New Files Created

1. **`backend/app/core/replicate_schema.py`** (195 lines)
   - Pydantic models for schema definition
   - `ImageInputSchema`, `ParameterSchema`, `InputSchema`, `OutputSchema`, `CustomSchema`, `ReplicateModelSchema`
   - Support for string, integer, float, boolean, enum types
   - UI hints (`ui_hidden`, `ui_group`)

2. **`backend/app/services/schema_validator.py`** (259 lines)
   - Parameter validation service
   - Type checking with graceful fallback to defaults
   - Warning-based error handling (logs warnings, doesn't fail)
   - Image constraint validation

3. **`backend/scripts/fetch_replicate_schema.py`** (196 lines)
   - CLI utility to fetch schemas from Replicate API
   - Parses OpenAPI schema from Replicate
   - Outputs JSON ready for config files

4. **`backend/tests/test_replicate_schema.py`** (213 lines)
   - 12 tests for schema models
   - Validates Pydantic model behavior

5. **`backend/tests/test_schema_validator.py`** (247 lines)
   - 13 tests for validation logic
   - Covers type validation, constraints, warnings

### Modified Files

1. **`backend/app/services/replicate_inference.py`**
   - Added schema-based parameter validation
   - Dynamic image parameter name from schema
   - Backward compatible (falls back if no schema)

2. **`backend/app/api/v1/routes/restoration.py`**
   - Added `parameters` field to endpoint
   - Accepts JSON string with user parameters
   - Passes parameters to inference service

3. **`backend/app/api/v1/routes/models.py`**
   - Enhanced to return schema in model list
   - Filters out `ui_hidden` parameters for frontend
   - Converts internal schema to API response format

4. **`backend/app/api/v1/schemas/model.py`**
   - Added `ParameterSchemaResponse`, `CustomSchemaResponse`, `ModelSchemaResponse`
   - Added `schema` field to `ModelInfo`

5. **`backend/config/default.json`** & **`backend/config/production.json`**
   - Added full `replicate_schema` for `replicate-restore` model
   - Removed deprecated `input_param_name` field

6. **`docs/configuration.md`**
   - Added comprehensive schema documentation
   - Parameter type examples
   - Usage instructions
   - CLI utility guide

## Schema Structure

```json
{
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
          "ui_group": "output"
        },
        {
          "name": "quality",
          "type": "integer",
          "min": 1,
          "max": 100,
          "default": 80,
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
      "supported_formats": ["jpg", "jpeg", "png"],
      "estimated_time_seconds": 30
    }
  }
}
```

## Parameter Types Supported

| Type | Description | Constraints |
|------|-------------|-------------|
| `string` | Text value | - |
| `integer` | Whole number | `min`, `max` |
| `float` | Decimal number | `min`, `max` |
| `boolean` | True/false | - |
| `enum` | One of predefined values | `values` array |

## Validation Behavior

- **Required parameters**: Raises `ValueError` if missing
- **Type mismatches**: Logs warning, uses default
- **Out of range**: Logs warning, clamps to min/max
- **Invalid enum**: Logs warning, uses default
- **Unknown parameters**: Logs warning, ignores
- **Image constraints**: Raises `ValueError` for size/format violations

## API Changes

### GET /api/v1/models

Now returns schema for models:

```json
{
  "models": [
    {
      "id": "replicate-restore",
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

### POST /api/v1/restore

Now accepts parameters:

```bash
curl -X POST /api/v1/restore \
  -F "file=@photo.jpg" \
  -F "model_id=replicate-restore" \
  -F 'parameters={"output_format": "jpg"}'
```

## Usage Examples

### Adding a New Model

1. Fetch schema from Replicate:
```bash
python backend/scripts/fetch_replicate_schema.py google/upscaler > schema.json
```

2. Copy schema into config file and customize:
```json
{
  "id": "google-upscaler",
  "model": "google/upscaler",
  "provider": "replicate",
  "replicate_schema": { /* paste from schema.json */ }
}
```

3. Adjust UI hints:
   - Set `ui_hidden: true` for advanced parameters
   - Group related parameters with `ui_group`
   - Set `custom.max_file_size_mb` appropriately

### Using Parameters from Frontend

Frontend can read schema and build dynamic UI:

```typescript
// Fetch models with schema
const response = await fetch('/api/v1/models');
const { models } = await response.json();

// Find model
const model = models.find(m => m.id === 'replicate-restore');

// Build UI from schema.parameters
model.schema.parameters.forEach(param => {
  if (param.type === 'enum') {
    // Render dropdown
  } else if (param.type === 'integer') {
    // Render number input with min/max
  }
});

// Submit with parameters
const formData = new FormData();
formData.append('file', file);
formData.append('model_id', 'replicate-restore');
formData.append('parameters', JSON.stringify({
  output_format: 'jpg',
  quality: 95
}));
```

## Test Coverage

**25 tests total** (all passing):
- 12 schema model tests
- 13 validation logic tests

Coverage:
- ✅ Schema parsing and validation
- ✅ Parameter type checking
- ✅ Constraint enforcement (min/max, enum)
- ✅ Default value application
- ✅ Warning generation
- ✅ Image constraint validation
- ✅ Format normalization

## Benefits

1. **No Hardcoding** - Each model defines its own schema
2. **Easy to Add Models** - Use CLI tool + copy/paste
3. **Type Safety** - Pydantic validates schemas at startup
4. **Frontend-Ready** - Schema exposed via API
5. **Flexible** - Support 5-6 models easily, can scale to more
6. **Validated** - Comprehensive test coverage
7. **Documented** - Clear documentation with examples

## Future Enhancements

- Frontend parameter UI implementation (planned for next phase)
- Model versioning support
- Schema caching/optimization
- Additional parameter types (array, object)
- Parameter presets/templates
- Cost tracking per model

## Migration Notes

**No backward compatibility needed** - This is MVP phase.

Old field `input_param_name` has been replaced with `replicate_schema.input.image.param_name`.

Models without `replicate_schema` still work (fallback to legacy behavior), but should be migrated.

## Files Changed Summary

**New Files**: 5
**Modified Files**: 8
**Tests**: 25
**Lines of Code**: ~1,400

## Conclusion

Successfully implemented a flexible, schema-based Replicate provider system that:
- Eliminates hardcoded assumptions
- Enables easy addition of new models
- Provides parameter validation
- Prepares for frontend parameter UI
- Is fully tested and documented

The system is production-ready and can support 5-6 Replicate models with unique schemas.
