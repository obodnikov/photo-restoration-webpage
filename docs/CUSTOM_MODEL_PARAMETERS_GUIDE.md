# Custom Model Parameters UI - User Guide

**Version:** 1.9.0+
**Last Updated:** 2025-12-30
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#1-overview)
2. [What You Can Do](#2-what-you-can-do)
3. [Quick Start](#3-quick-start)
4. [Migration Guide](#4-migration-guide)
5. [Configuration Reference](#5-configuration-reference)
6. [UI Control Types](#6-ui-control-types)
7. [Auto-Detection](#7-auto-detection)
8. [Configuration Examples](#8-configuration-examples)
9. [Troubleshooting](#9-troubleshooting)
10. [API Reference](#10-api-reference)

---

## 1. Overview

### What is Custom Model Parameters UI?

The Custom Model Parameters UI feature allows users to customize AI model behavior directly from the web interface. Instead of using fixed model settings, users can adjust parameters like image quality, output format, upscale factor, and more before processing their photos.

### Why Use This Feature?

**Before:** All users got the same model output with fixed settings
```
[Upload Image] → [Select Model] → [Process] → Fixed output
```

**After:** Users can customize model behavior to their needs
```
[Upload Image] → [Select Model] → [Adjust Parameters] → [Process] → Customized output
```

**Benefits:**
- **Flexibility** - Adjust quality, format, enhancement level per image
- **Control** - Fine-tune AI behavior for specific photo types
- **Transparency** - See and understand available model options
- **No Code** - Configure models through web UI, no backend changes needed

### Who Should Use This Guide?

This guide is for:
- **System administrators** deploying the application
- **Production users** upgrading from versions prior to 1.9.0
- **Power users** who want to customize AI model behavior

---

## 2. What You Can Do

### For End Users (Web Interface)

When a model has configurable parameters, users will see interactive controls on the restoration page:

```
┌────────────────────────────────────────────┐
│ ✓ Google Photo Upscaler        UPSCALE    │
├────────────────────────────────────────────┤
│ Upscale images 2x or 4x times              │
│                                            │
│ ▾ Parameters (2)                           │
│   ┌──────────────────────────────────┐    │
│   │ Upscale Factor                   │    │
│   │ ◉ x2    ○ x4                     │    │
│   │                                  │    │
│   │ Output Quality                   │    │
│   │ [━━━━━━●━━━] 80                 │    │
│   │ Low      Medium         High     │    │
│   └──────────────────────────────────┘    │
└────────────────────────────────────────────┘
```

**Available Controls:**
- **Text Input** - Free text entry (prompts, custom values)
- **Number Input** - Numeric values with validation
- **Slider** - Range selection with visual feedback
- **Dropdown** - Select from 4+ options
- **Radio Buttons** - Choose from 2-3 options
- **Toggle Switch** - Enable/disable features
- **Checkbox** - Boolean options

### For Administrators (Configuration)

Configure model parameters in JSON configuration files:

**Automated Approach:**
- Auto-hide internal parameters (seed, webhook, etc.)
- Auto-detect UI controls from parameter types
- Zero configuration for basic use cases

**Custom Approach:**
- Override auto-detection with custom UI controls
- Add custom labels, help text, slider marks
- Control parameter display order

---

## 3. Quick Start

### For New Installations

**Step 1:** Configure your models in `backend/config/default.json` or environment-specific files

**Step 2:** For Replicate models, ensure parameters have `ui_hidden` flags:

```json
{
  "replicate_schema": {
    "input": {
      "parameters": [
        {
          "name": "output_format",
          "type": "enum",
          "values": ["jpg", "png"],
          "default": "png",
          "description": "Output image format",
          "ui_hidden": false
        },
        {
          "name": "seed",
          "type": "integer",
          "description": "Random seed",
          "ui_hidden": true
        }
      ]
    }
  }
}
```

**Step 3:** (Optional) Add custom UI controls in `custom.ui_controls`

**Step 4:** Restart the application and test in the web interface

### For Existing Installations (Upgrade from <1.9.0)

**⚠️ IMPORTANT:** If upgrading from versions prior to 1.9.0, you **MUST** run the migration script.

See [Section 4: Migration Guide](#4-migration-guide) for detailed instructions.

---

## 4. Migration Guide

### Overview

If you have an existing deployment with Replicate models, you need to add `ui_hidden` flags to all model parameters. The migration script automates this process.

### When Do You Need to Migrate?

Run the migration if:
- ✅ Upgrading from version < 1.9.0
- ✅ You have Replicate models configured
- ✅ Your models have parameters without `ui_hidden` flags

Skip migration if:
- ❌ Fresh installation (no existing config)
- ❌ Only using HuggingFace models (no Replicate)
- ❌ Already migrated (all parameters have `ui_hidden`)

### Migration Warning Indicators

If migration is needed, you'll see:

**1. Backend Startup Warning**
```
⚠️  WARNING: Models need migration for Custom Model Parameters UI
    Models requiring migration:
    - replicate-restore (3 parameters need ui_hidden flags)

    Run migration script:
    python backend/scripts/migrate_ui_parameters.py --config backend/config/production.json
```

**2. Frontend Banner (Yellow Warning)**
```
┌────────────────────────────────────────────────────────────┐
│ ⚠️  Model Configuration Update Required                    │
│                                                            │
│ Some models need migration for the Custom Parameters UI.  │
│ Run: python backend/scripts/migrate_ui_parameters.py      │
│                                                            │
│ [View Documentation]  [Dismiss]                           │
└────────────────────────────────────────────────────────────┘
```

**3. API Endpoint**
```bash
# Check migration status
curl http://localhost:8000/api/v1/models/migration/status

# Response:
{
  "needs_migration": true,
  "models_needing_migration": [
    {
      "id": "replicate-restore",
      "name": "FLUX Kontext Photo Restore",
      "parameters_missing_ui_hidden": ["seed", "output_format", "safety_tolerance"]
    }
  ]
}
```

### Migration Script Options

The migration script provides two modes:

#### Option A: Automated Migration (Recommended for Quick Setup)

Automatically assigns `ui_hidden` based on parameter names:

```bash
# Navigate to project root
cd /path/to/photo-restoration-webpage

# Run automated migration
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/production.json

# Dry-run mode (preview changes without modifying files)
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/production.json \
  --dry-run
```

**What it does:**
- ✅ Auto-hides common internal parameters (seed, webhook, safety_tolerance, etc.)
- ✅ Auto-shows user-facing parameters (output_format, quality, upscale_factor, etc.)
- ✅ Uses auto-detection for UI controls (no custom config)
- ✅ Creates `backend/config/local.json` with migrated models
- ✅ Creates backup of original file

**Auto-hidden parameters:**
- `seed`, `random_seed`
- `safety_tolerance`
- `webhook`, `webhook_url`, `callback_url`
- `api_key`, `token`

#### Option B: Interactive Migration (Recommended for Production)

Asks questions to configure custom UI controls:

```bash
# Run interactive migration
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/production.json \
  --interactive
```

**Interactive prompts:**
```
============================================================
Parameter: output_format
Type: enum
Default: png
Description: Output image format

  Show in UI? [Y/n]: y

  Auto-detected control type: radio

  UI control type (auto/text/textarea/number/slider/dropdown/radio/toggle/checkbox) [radio]:
  Label [Output Format]: Image Format
  Help text [Output image format...]: Choose output file format
  Available options: jpg, png
  Custom order (comma-separated, blank=default):
  Display order (blank=auto): 1
```

**What it does:**
- ✅ All features of automated migration
- ✅ Lets you configure custom labels, help text
- ✅ Lets you add slider marks for ranges
- ✅ Lets you control display order
- ✅ Creates rich UI configurations in `custom.ui_controls`

### Migration Script Arguments

```bash
python backend/scripts/migrate_ui_parameters.py [OPTIONS]

Options:
  --config PATH       Config file to migrate (default: backend/config/production.json)
  --interactive       Ask questions to configure custom UI controls
  --no-backup         Skip creating backup file (not recommended)
  --output PATH       Output file path (default: creates backend/config/local.json)
  --dry-run           Show what would change without modifying files
```

### Step-by-Step Migration

**Step 1: Backup Your Configuration**

The script creates automatic backups, but you can create manual backup:

```bash
cp backend/config/production.json backend/config/production.json.backup
```

**Step 2: Choose Migration Mode**

**For quick migration (5 minutes):**
```bash
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/production.json
```

**For custom UI configuration (15 minutes):**
```bash
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/production.json \
  --interactive
```

**Step 3: Review Migration Summary**

The script shows a summary before saving:

```
=============================================================
MIGRATION SUMMARY
=============================================================
  - replicate-restore: Added ui_hidden to 'seed'
  - replicate-restore: Added ui_hidden to 'output_format'
  - replicate-restore: Added ui_hidden to 'safety_tolerance'
  - replicate-restore: Added custom UI controls

Total models migrated: 1/1

💾 Save changes to backend/config/local.json? [Y/n]:
```

**Step 4: Restart Application**

```bash
# If using Docker Compose
docker-compose restart backend

# If using local development
# Stop the backend and restart with:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Step 5: Verify Migration**

**Check startup logs:**
```bash
docker logs retro-backend 2>&1 | grep "Custom Model Parameters UI"

# Should show:
# ✅ Custom Model Parameters UI ready (3 models with parameters)
```

**Test in web interface:**
1. Open restoration page
2. Select a Replicate model
3. Verify parameter controls appear
4. Verify hidden parameters are not shown
5. Change parameter values
6. Process test image
7. Verify parameters applied

**Check API endpoint:**
```bash
curl http://localhost:8000/api/v1/models/migration/status

# Should show:
# {"needs_migration": false}
```

### Migration Output Files

The migration creates or modifies:

**`backend/config/local.json`** (created by default)
- Contains migrated model configurations
- Merged with environment config at startup
- Gitignored (safe for production secrets)
- Only `models` array is used from this file

**`backend/config/production.json.backup_YYYYMMDD_HHMMSS`** (backup)
- Timestamped backup of original file
- Preserved file metadata
- Use for rollback if needed

**Example local.json structure:**
```json
{
  "models": [
    {
      "id": "replicate-restore",
      "name": "FLUX Kontext Photo Restore",
      "replicate_schema": {
        "input": {
          "parameters": [
            {
              "name": "seed",
              "type": "integer",
              "ui_hidden": true
            },
            {
              "name": "output_format",
              "type": "enum",
              "values": ["jpg", "png"],
              "ui_hidden": false
            }
          ]
        }
      },
      "custom": {
        "ui_controls": {
          "output_format": {
            "type": "radio",
            "label": "Image Format",
            "help": "Choose output file format",
            "order": 1
          }
        }
      }
    }
  ]
}
```

### Rollback Migration

If you need to rollback:

**Option 1: Delete local.json**
```bash
# Remove migrated config
rm backend/config/local.json

# Restart application
docker-compose restart backend
```

**Option 2: Restore from backup**
```bash
# Find backup file
ls -la backend/config/*.backup_*

# Restore from backup
cp backend/config/production.json.backup_YYYYMMDD_HHMMSS \
   backend/config/production.json

# Restart application
docker-compose restart backend
```

---

## 5. Configuration Reference

### Configuration File Hierarchy

Model configurations are loaded in priority order:

```
1. backend/config/default.json        (REQUIRED - base config)
2. backend/config/{APP_ENV}.json      (Environment-specific: production.json, development.json)
3. backend/config/local.json          (Optional - custom overrides, models only)
4. Environment variables (.env)       (Highest priority - secrets only)
```

**Important Notes:**
- `default.json` MUST exist (contains base models and settings)
- `local.json` is **ONLY for model configurations** - all other fields are ignored
- For non-model overrides, use environment-specific files or `.env`

### Model Configuration Structure

A complete Replicate model configuration:

```json
{
  "id": "model-unique-id",
  "name": "Display Name",
  "model": "provider/model-name",
  "provider": "replicate",
  "category": "upscale|restore|enhance",
  "description": "User-facing description",
  "enabled": true,
  "tags": ["tag1", "tag2"],
  "version": "1.0",

  "replicate_schema": {
    "input": {
      "image": {
        "param_name": "image",
        "type": "uri",
        "format": "image",
        "required": true,
        "description": "Image to process"
      },
      "parameters": [
        {
          "name": "parameter_name",
          "type": "string|integer|float|boolean|enum",
          "required": false,
          "description": "Parameter description shown to users",
          "default": "default_value",
          "min": 1,
          "max": 100,
          "values": ["option1", "option2"],
          "ui_hidden": false
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
  },

  "custom": {
    "ui_controls": {
      "parameter_name": {
        "type": "text|textarea|number|slider|dropdown|radio|toggle|checkbox",
        "label": "Custom Label",
        "help": "Custom help text",
        "options": ["option1", "option2"],
        "order": 1,
        "step": 1,
        "marks": {
          "0": "Low",
          "50": "Medium",
          "100": "High"
        }
      }
    }
  },

  "parameters": {
    "default_param": "default_value"
  }
}
```

### Parameter Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ Yes | Parameter identifier (snake_case) |
| `type` | enum | ✅ Yes | Data type: `string`, `integer`, `float`, `boolean`, `enum` |
| `required` | boolean | No | Whether parameter is required (default: false) |
| `description` | string | No | User-facing description (shown as help text) |
| `default` | any | No | Default value if not provided |
| `min` | number | No | Minimum value (for `integer`/`float`) |
| `max` | number | No | Maximum value (for `integer`/`float`) |
| `values` | array | No | Allowed values (for `enum` type) |
| `ui_hidden` | boolean | ✅ Yes | Whether to hide from UI (true = hidden) |

### Custom UI Control Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | ✅ Yes | UI control type (see [Section 6](#6-ui-control-types)) |
| `label` | string | No | Override auto-generated label |
| `help` | string | No | Override parameter description |
| `options` | array | No | Options for `dropdown`/`radio` (overrides `values`) |
| `order` | number | No | Display order (lower = earlier, default: 999) |
| `step` | number | No | Step size for `number`/`slider` |
| `marks` | object | No | Slider marks: `{"value": "label"}` |

---

## 6. UI Control Types

### Overview

8 UI control types are available. If not specified in `custom.ui_controls`, the system auto-detects from parameter type.

### Text Input

**Best for:** Short strings, custom prompts, identifiers

**Auto-detected when:**
- Parameter type is `string`
- No better match found

**Configuration:**
```json
{
  "name": "prompt",
  "type": "string",
  "description": "Custom enhancement prompt",
  "ui_hidden": false
}
```

**Custom UI control:**
```json
{
  "prompt": {
    "type": "text",
    "label": "Enhancement Prompt",
    "help": "Describe desired enhancement"
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ Enhancement Prompt              │
│ ┌─────────────────────────────┐ │
│ │ make colors vibrant         │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### Number Input

**Best for:** Numeric values without predefined range

**Auto-detected when:**
- Parameter type is `integer` or `float`
- No `min` and `max` defined

**Configuration:**
```json
{
  "name": "iterations",
  "type": "integer",
  "description": "Number of enhancement iterations",
  "ui_hidden": false
}
```

**Custom UI control:**
```json
{
  "iterations": {
    "type": "number",
    "label": "Iterations",
    "step": 1
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ Iterations                      │
│ ┌──────┐                        │
│ │  5   │  [−]  [+]              │
│ └──────┘                        │
└─────────────────────────────────┘
```

### Slider Input

**Best for:** Numeric ranges with visual feedback

**Auto-detected when:**
- Parameter type is `integer` or `float`
- Both `min` AND `max` are defined

**Configuration:**
```json
{
  "name": "compression_quality",
  "type": "integer",
  "min": 1,
  "max": 100,
  "default": 80,
  "description": "Compression quality for output (1-100)",
  "ui_hidden": false
}
```

**Custom UI control (with marks):**
```json
{
  "compression_quality": {
    "type": "slider",
    "label": "Output Quality",
    "help": "Higher quality = larger file size",
    "step": 5,
    "marks": {
      "1": "Low",
      "50": "Medium",
      "100": "High"
    },
    "order": 2
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ Output Quality ⓘ                │
│ [━━━━━━━━●━━] 80               │
│ Low    Medium         High      │
└─────────────────────────────────┘
```

### Dropdown Input

**Best for:** Selecting from 4+ options

**Auto-detected when:**
- Parameter type is `enum`
- 4 or more values in `values` array

**Configuration:**
```json
{
  "name": "model_variant",
  "type": "enum",
  "values": ["fast", "balanced", "quality", "ultra"],
  "default": "balanced",
  "description": "Model quality variant",
  "ui_hidden": false
}
```

**Custom UI control:**
```json
{
  "model_variant": {
    "type": "dropdown",
    "label": "Quality Preset",
    "options": ["fast", "balanced", "quality", "ultra"]
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ Quality Preset                  │
│ ┌─────────────────────────────┐ │
│ │ balanced              ▼     │ │
│ └─────────────────────────────┘ │
│   Options:                      │
│   - fast                        │
│   - balanced (selected)         │
│   - quality                     │
│   - ultra                       │
└─────────────────────────────────┘
```

### Radio Input

**Best for:** Selecting from 2-3 options

**Auto-detected when:**
- Parameter type is `enum`
- 2 or 3 values in `values` array

**Configuration:**
```json
{
  "name": "upscale_factor",
  "type": "string",
  "default": "x2",
  "description": "Factor by which to upscale the image",
  "ui_hidden": false
}
```

**Custom UI control:**
```json
{
  "upscale_factor": {
    "type": "radio",
    "options": ["x2", "x4"],
    "label": "Upscale Factor",
    "help": "Choose 2x or 4x upscaling",
    "order": 1
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ Upscale Factor ⓘ                │
│ ◉ x2    ○ x4                    │
└─────────────────────────────────┘
```

### Toggle Input

**Best for:** Boolean on/off switches

**Auto-detected when:**
- Parameter type is `boolean`

**Configuration:**
```json
{
  "name": "enable_enhancement",
  "type": "boolean",
  "default": true,
  "description": "Apply AI-based enhancement",
  "ui_hidden": false
}
```

**Custom UI control:**
```json
{
  "enable_enhancement": {
    "type": "toggle",
    "label": "AI Enhancement",
    "help": "Apply additional AI enhancement"
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ AI Enhancement ⓘ       [●──]   │
│                        ON       │
└─────────────────────────────────┘
```

### Checkbox Input

**Best for:** Boolean checkboxes (alternative to toggle)

**Auto-detected when:**
- Never (must be explicitly configured)

**Custom UI control:**
```json
{
  "accept_terms": {
    "type": "checkbox",
    "label": "I accept terms of use"
  }
}
```

**UI Result:**
```
┌─────────────────────────────────┐
│ ☑ I accept terms of use         │
└─────────────────────────────────┘
```

---

## 7. Auto-Detection

### How Auto-Detection Works

If a parameter has `ui_hidden: false` but no entry in `custom.ui_controls`, the system automatically selects an appropriate UI control type based on the parameter schema.

### Auto-Detection Rules

| Parameter Characteristics | Auto-Detected Control |
|---------------------------|----------------------|
| `type: "boolean"` | `toggle` |
| `type: "enum"` with 2-3 values | `radio` |
| `type: "enum"` with 4+ values | `dropdown` |
| `type: "integer"` or `"float"` with `min` AND `max` | `slider` |
| `type: "integer"` or `"float"` without range | `number` |
| `type: "string"` | `text` |

### Auto-Detection Examples

**Example 1: Boolean → Toggle**
```json
{
  "name": "enable_enhancement",
  "type": "boolean",
  "default": true,
  "description": "Apply AI-based enhancement",
  "ui_hidden": false
}
```
Result: Toggle switch (ON/OFF)

**Example 2: Enum (2 values) → Radio**
```json
{
  "name": "output_format",
  "type": "enum",
  "values": ["jpg", "png"],
  "default": "png",
  "description": "Output image format",
  "ui_hidden": false
}
```
Result: Radio buttons (○ JPG ◉ PNG)

**Example 3: Range → Slider**
```json
{
  "name": "compression_quality",
  "type": "integer",
  "min": 1,
  "max": 100,
  "default": 80,
  "description": "Compression quality for output (1-100)",
  "ui_hidden": false
}
```
Result: Slider (1 ━━━●━━ 100)

### Overriding Auto-Detection

To override auto-detection, add explicit configuration in `custom.ui_controls`:

```json
{
  "replicate_schema": {
    "input": {
      "parameters": [
        {
          "name": "compression_quality",
          "type": "integer",
          "min": 1,
          "max": 100,
          "ui_hidden": false
        }
      ]
    }
  },
  "custom": {
    "ui_controls": {
      "compression_quality": {
        "type": "slider",
        "label": "Output Quality",
        "marks": {
          "1": "Low",
          "50": "Medium",
          "100": "High"
        }
      }
    }
  }
}
```

Without `custom.ui_controls`, this would be a plain slider. With override, it gets custom label and marks.

---

## 8. Configuration Examples

### Example 1: Google Photo Upscaler (Custom UI Controls)

**Full configuration from `backend/config/local.json.example`:**

```json
{
  "id": "replicate-google-upscaler",
  "name": "Google Photo Upscaler",
  "model": "google/upscaler",
  "provider": "replicate",
  "category": "upscale",
  "description": "Upscale images 2x or 4x times",
  "enabled": true,
  "tags": ["replicate", "advanced", "upscale"],
  "version": "1.0",
  "replicate_schema": {
    "input": {
      "image": {
        "param_name": "image",
        "type": "uri",
        "format": "image",
        "required": true,
        "description": "Image to upscale"
      },
      "parameters": [
        {
          "name": "upscale_factor",
          "type": "string",
          "required": false,
          "description": "Factor by which to upscale the image",
          "default": "x2",
          "ui_hidden": false
        },
        {
          "name": "compression_quality",
          "type": "integer",
          "required": false,
          "description": "Compression quality for output (1-100)",
          "default": 80,
          "min": 1,
          "max": 100,
          "ui_hidden": false
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
      "estimated_time_seconds": null
    }
  },
  "custom": {
    "ui_controls": {
      "upscale_factor": {
        "type": "radio",
        "options": ["x2", "x4"],
        "label": "Upscale Factor",
        "help": "Choose 2x or 4x upscaling",
        "order": 1
      },
      "compression_quality": {
        "type": "slider",
        "label": "Output Quality",
        "help": "Higher quality = larger file size",
        "order": 2,
        "step": 5,
        "marks": {
          "1": "Low",
          "50": "Medium",
          "100": "High"
        }
      }
    }
  },
  "parameters": {
    "output_format": "png",
    "safety_tolerance": 2
  }
}
```

**UI Result:**
```
┌────────────────────────────────────┐
│ ✓ Google Photo Upscaler  UPSCALE  │
├────────────────────────────────────┤
│ Upscale images 2x or 4x times      │
│                                    │
│ [replicate] [advanced] [upscale]  │
│                                    │
│ ▾ Parameters (2)                   │
│   ┌──────────────────────────────┐ │
│   │ Upscale Factor ⓘ             │ │
│   │ ◉ x2    ○ x4                 │ │
│   │                              │ │
│   │ Output Quality ⓘ             │ │
│   │ [━━━━━━●━━━] 80             │ │
│   │ Low    Medium         High   │ │
│   └──────────────────────────────┘ │
└────────────────────────────────────┘
```

### Example 2: FLUX Kontext Photo Restore (Auto-Detection)

**Full configuration from `backend/config/local.json.example`:**

```json
{
  "id": "replicate-restore-auto",
  "name": "FLUX Kontext Photo Restore (Auto UI)",
  "model": "flux-kontext-apps/restore-image",
  "provider": "replicate",
  "category": "restore",
  "description": "Advanced photo restoration (demonstrates auto-detection)",
  "enabled": true,
  "tags": ["restore", "replicate", "advanced"],
  "version": "1.0",
  "replicate_schema": {
    "input": {
      "image": {
        "param_name": "input_image",
        "type": "uri",
        "format": "image",
        "required": true,
        "description": "Image to restore (jpeg, png, gif, webp)"
      },
      "parameters": [
        {
          "name": "seed",
          "type": "integer",
          "required": false,
          "description": "Random seed for reproducible generation",
          "ui_hidden": true
        },
        {
          "name": "output_format",
          "type": "enum",
          "values": ["jpg", "png"],
          "default": "png",
          "required": false,
          "description": "Output image format",
          "ui_hidden": false
        },
        {
          "name": "enable_enhancement",
          "type": "boolean",
          "default": true,
          "required": false,
          "description": "Apply AI-based enhancement",
          "ui_hidden": false
        },
        {
          "name": "safety_tolerance",
          "type": "integer",
          "min": 0,
          "max": 2,
          "default": 2,
          "required": false,
          "description": "Safety level (0=strict, 2=permissive)",
          "ui_hidden": true
        }
      ]
    },
    "output": {
      "type": "uri",
      "format": "image"
    },
    "custom": {
      "max_file_size_mb": 10,
      "supported_formats": ["jpg", "jpeg", "png", "webp", "gif"],
      "estimated_time_seconds": 30
    }
  },
  "custom": {},
  "parameters": {
    "output_format": "png",
    "safety_tolerance": 2
  }
}
```

**UI Result (auto-detected):**
```
┌─────────────────────────────────────────┐
│ ✓ FLUX Kontext Photo Restore   RESTORE │
├─────────────────────────────────────────┤
│ Advanced photo restoration using AI     │
│                                         │
│ [restore] [replicate] [advanced]       │
│                                         │
│ ▾ Parameters (2)                        │
│   ┌───────────────────────────────┐    │
│   │ Output Format                 │    │
│   │ ◉ PNG    ○ JPG                │    │  ← Auto: radio (2 options)
│   │                               │    │
│   │ Enable Enhancement   [●──]    │    │  ← Auto: toggle (boolean)
│   │                      ON       │    │
│   └───────────────────────────────┘    │
└─────────────────────────────────────────┘

Note: seed and safety_tolerance are hidden (ui_hidden: true)
```

---

## 9. Troubleshooting

### Common Issues

#### Issue 1: Parameters Not Showing in UI

**Symptoms:**
- Model appears in selector
- No parameter controls visible
- Expected parameters are not shown

**Possible Causes & Solutions:**

**Cause A: Parameters have `ui_hidden: true`**
```json
{
  "name": "output_format",
  "ui_hidden": true  // ← This hides the parameter
}
```
Solution: Set `ui_hidden: false`

**Cause B: Model has no parameters**
```json
{
  "replicate_schema": {
    "input": {
      "parameters": []  // ← Empty array
    }
  }
}
```
Solution: Add parameters to schema

**Cause C: Migration not run**
```
⚠️  Parameter 'output_format' missing ui_hidden flag
```
Solution: Run migration script (see [Section 4](#4-migration-guide))

**Cause D: Configuration not loaded**
```bash
# Check backend logs
docker logs retro-backend 2>&1 | grep "Configuration source"

# Should show:
# ✅ Configuration source: JSON config files

# If shows:
# ⚠️  Configuration source: .env only (DEPRECATED)
# Then default.json is missing
```
Solution: Ensure `backend/config/default.json` exists

#### Issue 2: Invalid JSON in Configuration

**Symptoms:**
- Backend fails to start
- Error: "Invalid JSON in config file"

**Common JSON Errors:**

**Missing comma:**
```json
{
  "name": "param1"
  "type": "string"  // ← Missing comma after "param1"
}
```

**Trailing comma:**
```json
{
  "values": ["jpg", "png",]  // ← Trailing comma not allowed
}
```

**Unquoted keys:**
```json
{
  name: "value"  // ← Keys must be quoted
}
```

**Solution:**
1. Validate JSON syntax: https://jsonlint.com/
2. Use a JSON-aware editor (VS Code, Sublime Text)
3. Check backend logs for specific error line

#### Issue 3: Migration Script Fails

**Symptoms:**
- Script crashes
- Backup not created
- Output file not generated

**Common Errors:**

**Error: Config file not found**
```
❌ Error: Config file not found: backend/config/production.json
```
Solution:
```bash
# Verify file exists
ls -la backend/config/

# Use correct path
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/default.json
```

**Error: Permission denied**
```
PermissionError: [Errno 13] Permission denied: 'backend/config/local.json'
```
Solution:
```bash
# Check permissions
ls -la backend/config/

# Fix permissions
chmod 644 backend/config/local.json
```

#### Issue 4: Frontend Shows Migration Warning

**Symptoms:**
- Yellow banner appears on homepage
- "Model Configuration Update Required" message

**Cause:**
Models have parameters without `ui_hidden` flags

**Solution:**
```bash
# Run migration
python backend/scripts/migrate_ui_parameters.py \
  --config backend/config/production.json

# Restart backend
docker-compose restart backend

# Refresh browser
# Warning should disappear
```

#### Issue 5: Slider Marks Not Appearing

**Symptoms:**
- Slider shows but no labels
- Marks configuration ignored

**Cause: Incorrect marks format**
```json
{
  "marks": {
    0: "Low",      // ← Keys must be strings
    50: "Medium",
    100: "High"
  }
}
```
Solution: Quote all keys
```json
{
  "marks": {
    "0": "Low",
    "50": "Medium",
    "100": "High"
  }
}
```

### Debugging Steps

**Step 1: Check Backend Logs**
```bash
# Docker Compose
docker-compose logs -f backend

# Look for:
# - Configuration loading errors
# - Parameter validation warnings
# - Migration status messages
```

**Step 2: Verify Configuration Loaded**
```bash
# Check models API endpoint
curl http://localhost:8000/api/v1/models | jq

# Verify models have:
# - "schema" object with parameters
# - "custom" object (may be empty)
# - Parameters with "ui_hidden" field
```

**Step 3: Check Migration Status**
```bash
# Check migration endpoint
curl http://localhost:8000/api/v1/models/migration/status | jq

# Expected response:
# {
#   "needs_migration": false
# }

# If true, run migration script
```

**Step 4: Validate Configuration Files**
```bash
# Validate JSON syntax
python backend/scripts/validate_config.py \
  --env production

# Should show:
# ✅ Configuration valid
```

### Getting Help

If issues persist:

1. **Check migration status:**
   ```bash
   curl http://localhost:8000/api/v1/models/migration/status
   ```

2. **Review example configurations:**
   - `backend/config/local.json.example`
   - `backend/config/default.json`

3. **Check implementation docs:**
   - `docs/chats/custom-model-parameters-ui-implementation-2025-12-28.md`
   - `docs/chats/custom-model-parameters-ui-migration-strategy-2025-12-29.md`

4. **Verify file structure:**
   ```bash
   tree backend/config/
   # Should include:
   # - default.json (required)
   # - production.json (or development.json)
   # - local.json (if migrated)
   ```

---

## 10. API Reference

### Models API

#### GET /api/v1/models

List all available models with parameter schemas.

**Response:**
```json
{
  "models": [
    {
      "id": "model-id",
      "name": "Model Name",
      "category": "upscale",
      "description": "Model description",
      "schema": {
        "parameters": [
          {
            "name": "parameter_name",
            "type": "string",
            "description": "Parameter description",
            "default": "default_value",
            "ui_hidden": false
          }
        ],
        "custom": {
          "max_file_size_mb": 10,
          "supported_formats": ["jpg", "png"]
        }
      },
      "custom": {
        "ui_controls": {
          "parameter_name": {
            "type": "text",
            "label": "Parameter Label",
            "help": "Help text"
          }
        }
      }
    }
  ]
}
```

### Restoration API

#### POST /api/v1/restore

Restore an image using selected model and parameters.

**Request:**
```http
POST /api/v1/restore
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}

file: [binary image data]
model_id: "replicate-restore"
parameters: {"output_format": "png", "enable_enhancement": true}
```

**FormData Fields:**
- `file` (file) - Image file to process
- `model_id` (string) - Model identifier
- `parameters` (string, optional) - JSON string with parameter values

**Response:**
```json
{
  "id": "image-uuid",
  "original_url": "/uploads/session_id/uuid_original.jpg",
  "processed_url": "/processed/session_id/uuid_processed.png",
  "model_id": "replicate-restore",
  "parameters": {
    "output_format": "png",
    "enable_enhancement": true
  },
  "created_at": "2025-12-30T10:00:00Z"
}
```

### Migration Status API

#### GET /api/v1/models/migration/status

Check if models need migration for Custom Model Parameters UI.

**Response (migration needed):**
```json
{
  "needs_migration": true,
  "models_needing_migration": [
    {
      "id": "replicate-restore",
      "name": "Photo Restore",
      "parameters_missing_ui_hidden": ["seed", "output_format", "safety_tolerance"]
    }
  ]
}
```

**Response (no migration needed):**
```json
{
  "needs_migration": false
}
```

---

## Appendix: Related Documentation

### Implementation Conversations

Located in `docs/chats/`:

1. **custom-model-parameters-ui-implementation-2025-12-28.md**
   - Complete technical specification
   - Backend and frontend implementation details
   - Testing checklist

2. **custom-model-parameters-ui-feature-implementation-planning-2025-12-29.md**
   - Phase 1 (Backend) implementation
   - Schema updates and validation
   - API endpoint modifications

3. **custom-model-parameters-ui-phase-2-frontend-implementation-2025-12-29.md**
   - Phase 2 (Frontend) implementation
   - React components and state management
   - UI control components

4. **custom-model-parameters-ui-migration-strategy-2025-12-29.md**
   - Migration script design
   - Interactive vs automated approaches
   - Safety and validation

### Configuration Files

Located in `backend/config/`:

- **default.json** - Base configuration (REQUIRED)
- **production.json.example** - Production template
- **local.json.example** - Local overrides with real examples
- **development.json.example** - Development template
- **staging.json.example** - Staging template

### Migration Script

Located at `backend/scripts/migrate_ui_parameters.py`

Run `python backend/scripts/migrate_ui_parameters.py --help` for usage.

### Architecture Documentation

- **ARCHITECTURE.md** - System architecture (Section 4.1: Frontend Custom Model Parameters UI)
- **README.md** - Main project documentation
- **ROADMAP.md** - Development roadmap and phases

---

**End of Guide**

For questions or issues, refer to:
- [Section 9: Troubleshooting](#9-troubleshooting)
- Implementation docs in `docs/chats/`
- Migration script help: `python backend/scripts/migrate_ui_parameters.py --help`
