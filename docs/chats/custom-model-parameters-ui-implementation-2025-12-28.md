# Custom Model Parameters UI - Implementation Plan

**Date:** 2025-12-28
**Status:** Ready for Implementation
**Feature:** Dynamic Model Parameter Controls on Restoration Page

---

## Requirements Summary

### User Request
Add ability to configure model parameters on the Home (Restoration) page before processing images. Parameters should be displayed as interactive UI controls (sliders, dropdowns, toggles) based on model configuration.

### Key Features
1. **Dynamic parameter UI** - Generate controls from model schema
2. **Custom UI configuration** - Use `custom.ui_controls` to override auto-detection
3. **Auto-detection fallback** - Smart defaults when no custom config provided
4. **Validation** - Respect min/max constraints from replicate_schema
5. **Hide internal parameters** - Respect `ui_hidden` flag
6. **Label override** - Support custom labels in ui_controls
7. **Pass to API** - Send user-configured parameters to restoration endpoint

---

## Architecture Decision: Use Root-Level `custom` Field

### Current Configuration Structure

Models in config files have two `custom` fields:

```json
{
  "id": "model-id",
  "replicate_schema": {
    "input": {
      "parameters": [...],
    },
    "custom": {                    // ← Schema-level (file constraints)
      "max_file_size_mb": 10,
      "supported_formats": ["jpg", "png"]
    }
  },
  "custom": {}                     // ← ROOT LEVEL (app-specific config)
}
```

### Decision ✅
**Use root-level `custom` field for UI configuration**

**Rationale:**
- ✅ Clean separation: `replicate_schema` = API contract, `custom` = UI presentation
- ✅ No duplication of parameter definitions
- ✅ Already exists in model structure
- ✅ Can be extended for other app-specific features
- ✅ Maps to parameters by name (no sync issues)

---

## Configuration Format

### Schema Structure

```json
{
  "id": "replicate-google-upscaler",
  "name": "Google Photo Upscaler",
  "replicate_schema": {
    "input": {
      "parameters": [
        {
          "name": "upscale_factor",
          "type": "string",
          "default": "x2",
          "description": "Factor by which to upscale the image",
          "ui_hidden": false
        },
        {
          "name": "compression_quality",
          "type": "integer",
          "min": 1,
          "max": 100,
          "default": 80,
          "description": "Compression quality for output (1-100)",
          "ui_hidden": false
        },
        {
          "name": "seed",
          "type": "integer",
          "description": "Random seed for reproducibility",
          "ui_hidden": true          // ← Hidden from UI
        }
      ]
    }
  },
  "custom": {
    "ui_controls": {
      "upscale_factor": {
        "type": "radio",             // UI control type
        "options": ["x2", "x4"],     // Options for dropdown/radio
        "label": "Upscale Factor",   // Override auto-generated label
        "help": "Choose upscaling multiplier",
        "order": 1                   // Display order
      },
      "compression_quality": {
        "type": "slider",
        "label": "Output Quality",
        "help": "Higher quality = larger file size",
        "order": 2,
        "step": 5,                   // Slider step size
        "marks": {                   // Slider marks
          "1": "Low",
          "50": "Medium",
          "100": "High"
        }
      }
    }
  }
}
```

### UI Control Types

| Type | Use Case | Example |
|------|----------|---------|
| `text` | String input | Custom prompt text |
| `textarea` | Multi-line string | Long descriptions |
| `number` | Numeric input | Integer/float without range |
| `slider` | Numeric input with range | Quality 1-100 |
| `dropdown` | Select from list (4+ options) | File format selection |
| `radio` | Select from list (2-3 options) | x2 vs x4 upscaling |
| `toggle` | Boolean switch | Enable/disable feature |
| `checkbox` | Boolean checkbox | Accept terms |

### Auto-Detection Logic

When `custom.ui_controls` is empty or missing:

| Parameter Type | Conditions | Auto-Detected Control |
|----------------|------------|----------------------|
| `boolean` | - | `toggle` |
| `enum` | 2-3 values | `radio` |
| `enum` | 4+ values | `dropdown` |
| `integer/float` | Has min & max | `slider` |
| `integer/float` | No range | `number` |
| `string` | - | `text` |

---

## Example Configurations

### Example 1: Google Upscaler (with custom UI)

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
┌──────────────────────────────────────────┐
│ ✓ Google Photo Upscaler        UPSCALE  │
├──────────────────────────────────────────┤
│ Upscale images 2x or 4x times            │
│                                          │
│ [replicate] [advanced] [upscale]        │
│                                          │
│ ▾ Parameters (2)                         │
│   ┌────────────────────────────────┐    │
│   │ Upscale Factor ⓘ               │    │
│   │ ◉ x2    ○ x4                   │    │
│   │                                │    │
│   │ Output Quality ⓘ               │    │
│   │ [━━━━━━●━━━] 80               │    │
│   │ Low      Medium         High   │    │
│   └────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

### Example 2: FLUX Kontext (auto-detect)

```json
{
  "id": "replicate-restore",
  "name": "FLUX Kontext Photo Restore",
  "model": "flux-kontext-apps/restore-image",
  "provider": "replicate",
  "category": "restore",
  "description": "Advanced photo restoration using Replicate AI",
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
          "ui_hidden": true          // ← Hidden
        },
        {
          "name": "output_format",
          "type": "enum",
          "values": ["jpg", "png"],
          "default": "png",
          "required": false,
          "description": "Output image format",
          "ui_hidden": false         // ← Visible
        },
        {
          "name": "safety_tolerance",
          "type": "integer",
          "min": 0,
          "max": 2,
          "default": 2,
          "required": false,
          "description": "Safety level (0=strict, 2=permissive)",
          "ui_hidden": true          // ← Hidden
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
  "custom": {},                      // ← Empty: use auto-detection
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
│ ▾ Parameters (1)                        │
│   ┌───────────────────────────────┐    │
│   │ Output Format                 │    │
│   │ ◉ PNG    ○ JPG                │    │ ← Auto: radio (2 options)
│   └───────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend Changes

#### 1.1 Update Backend Schema Types

**File:** `backend/app/core/config_schema.py`

Add new Pydantic models for UI configuration:

```python
class UIControlConfig(BaseModel):
    """UI control configuration for a parameter."""

    type: Literal[
        "text", "textarea", "number", "slider",
        "dropdown", "radio", "toggle", "checkbox"
    ] = Field(description="UI control type")

    label: str | None = Field(
        None,
        description="Display label (overrides auto-generated)"
    )
    help: str | None = Field(
        None,
        description="Help text tooltip"
    )
    options: list[str] | None = Field(
        None,
        description="Options for dropdown/radio"
    )
    order: int | None = Field(
        None,
        description="Display order"
    )
    step: int | float | None = Field(
        None,
        description="Step size for slider/number"
    )
    marks: dict[str, str] | None = Field(
        None,
        description="Slider marks {value: label}"
    )


class ModelConfig(BaseModel):
    """Individual model configuration."""

    # ... existing fields ...

    custom: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom application-specific configuration"
    )
```

**Changes:**
- Add `UIControlConfig` class
- Keep `custom` as flexible `dict[str, Any]` to allow any structure
- Backend will pass this through to frontend as-is

#### 1.2 Update API Response Schema

**File:** `backend/app/api/v1/schemas/model.py`

Add UI control types to API response:

```python
class UIControlConfigResponse(BaseModel):
    """UI control configuration for frontend."""

    type: Literal[
        "text", "textarea", "number", "slider",
        "dropdown", "radio", "toggle", "checkbox"
    ]
    label: str | None = None
    help: str | None = None
    options: list[str] | None = None
    order: int | None = None
    step: int | float | None = None
    marks: dict[str, str] | None = None


class ModelCustomConfigResponse(BaseModel):
    """Custom model configuration for frontend."""

    ui_controls: dict[str, UIControlConfigResponse] | None = None
    # Allow other custom fields
    model_config = {"extra": "allow"}


class ModelInfo(BaseModel):
    """Model information schema."""

    # ... existing fields ...

    custom: dict[str, Any] | None = Field(
        None,
        description="Custom application-specific configuration"
    )
```

**Changes:**
- Add typed response models for documentation
- Keep actual field as `dict[str, Any]` for flexibility
- Frontend can parse according to known structure

#### 1.3 Update Models API Endpoint

**File:** `backend/app/api/v1/routes/models.py`

Ensure `custom` field is included in response:

```python
@router.get("", response_model=ModelListResponse)
async def get_models(...) -> ModelListResponse:
    """Get list of available models."""

    # ... existing code ...

    models_list = []
    for model_config in settings.models:
        model_dict = {
            "id": model_config.id,
            "name": model_config.name,
            # ... other fields ...
            "custom": model_config.custom,  # ← Include custom field
        }

        # Add schema if replicate model
        if model_config.replicate_schema:
            # ... existing schema processing ...

        models_list.append(ModelInfo(**model_dict))
```

**Changes:**
- Include `custom` field in model response
- No processing needed - pass through as-is

#### 1.4 Update Restoration API Endpoint

**File:** `backend/app/api/v1/routes/restoration.py`

Already supports `parameters` field, verify it works:

```python
@router.post("", response_model=schemas.RestoreResponse)
async def restore_image(
    file: UploadFile,
    model_id: str = Form(...),
    parameters: str | None = Form(None),  # ← JSON string with user params
    ...
):
    """Restore an image using selected model."""

    # Parse user parameters
    user_params = {}
    if parameters:
        try:
            user_params = json.loads(parameters)
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid parameters JSON")

    # ... pass user_params to inference service ...
```

**Changes:**
- Verify existing endpoint accepts parameters
- No changes needed if already implemented

---

### Phase 2: Frontend Changes

#### 2.1 Update Frontend Types

**File:** `frontend/src/features/restoration/types.ts`

```typescript
export type UIControlType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'slider'
  | 'dropdown'
  | 'radio'
  | 'toggle'
  | 'checkbox';

export interface UIControlConfig {
  type: UIControlType;
  label?: string;
  help?: string;
  options?: string[];
  order?: number;
  step?: number;
  marks?: Record<string, string>;
}

export interface ParameterSchema {
  name: string;
  type: 'string' | 'integer' | 'float' | 'boolean' | 'enum';
  required: boolean;
  description: string;
  default?: any;
  min?: number;
  max?: number;
  values?: string[];
  ui_hidden?: boolean;
  ui_group?: string;
}

export interface ModelSchema {
  parameters: ParameterSchema[];
  custom?: {
    max_file_size_mb: number;
    supported_formats: string[];
    estimated_time_seconds?: number;
  };
}

export interface ModelCustomConfig {
  ui_controls?: Record<string, UIControlConfig>;
  [key: string]: any;  // Allow other custom fields
}

export interface ModelInfo {
  id: string;
  name: string;
  model: string;
  category: string;
  description: string;
  parameters?: Record<string, unknown>;
  tags?: string[];
  version?: string;
  schema?: ModelSchema;
  custom?: ModelCustomConfig;  // ← NEW
}

export interface ModelParameterValues {
  [paramName: string]: any;
}
```

#### 2.2 Create Parameter Input Components

**File Structure:**
```
frontend/src/features/restoration/components/
├── ModelSelector.tsx              (MODIFY - integrate params)
├── ModelCard.tsx                  (NEW - extract card logic)
├── ModelParameterControls.tsx     (NEW - parameter form container)
└── parameter-inputs/              (NEW - folder)
    ├── TextInput.tsx              (NEW)
    ├── NumberInput.tsx            (NEW)
    ├── SliderInput.tsx            (NEW)
    ├── DropdownInput.tsx          (NEW)
    ├── RadioInput.tsx             (NEW)
    ├── ToggleInput.tsx            (NEW)
    ├── CheckboxInput.tsx          (NEW)
    └── ParameterInput.tsx         (NEW - wrapper/factory)
```

**File:** `frontend/src/features/restoration/components/parameter-inputs/ParameterInput.tsx`

```typescript
/**
 * Factory component that renders the appropriate input based on UI config
 */
import React from 'react';
import type { ParameterSchema, UIControlConfig } from '../../types';
import { TextInput } from './TextInput';
import { NumberInput } from './NumberInput';
import { SliderInput } from './SliderInput';
import { DropdownInput } from './DropdownInput';
import { RadioInput } from './RadioInput';
import { ToggleInput } from './ToggleInput';

export interface ParameterInputProps {
  param: ParameterSchema;
  uiConfig: UIControlConfig;
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export const ParameterInput: React.FC<ParameterInputProps> = ({
  param,
  uiConfig,
  value,
  onChange,
  disabled = false,
}) => {
  const label = uiConfig.label || formatLabel(param.name);
  const help = uiConfig.help || param.description;

  switch (uiConfig.type) {
    case 'text':
    case 'textarea':
      return (
        <TextInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
          multiline={uiConfig.type === 'textarea'}
        />
      );

    case 'number':
      return (
        <NumberInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
          min={param.min}
          max={param.max}
          step={uiConfig.step}
        />
      );

    case 'slider':
      return (
        <SliderInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
          min={param.min || 0}
          max={param.max || 100}
          step={uiConfig.step}
          marks={uiConfig.marks}
        />
      );

    case 'dropdown':
      return (
        <DropdownInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
          options={uiConfig.options || param.values || []}
        />
      );

    case 'radio':
      return (
        <RadioInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
          options={uiConfig.options || param.values || []}
        />
      );

    case 'toggle':
    case 'checkbox':
      return (
        <ToggleInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
          variant={uiConfig.type}
        />
      );

    default:
      return (
        <TextInput
          label={label}
          help={help}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      );
  }
};

function formatLabel(paramName: string): string {
  // "output_format" → "Output Format"
  return paramName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
```

**File:** `frontend/src/features/restoration/components/ModelParameterControls.tsx`

```typescript
/**
 * Container for all parameter inputs for a model
 */
import React from 'react';
import type { ModelInfo, ModelParameterValues } from '../types';
import { ParameterInput } from './parameter-inputs/ParameterInput';
import { getParameterUIConfig } from '../utils/parameterUtils';

export interface ModelParameterControlsProps {
  model: ModelInfo;
  values: ModelParameterValues;
  onChange: (values: ModelParameterValues) => void;
  disabled?: boolean;
}

export const ModelParameterControls: React.FC<ModelParameterControlsProps> = ({
  model,
  values,
  onChange,
  disabled = false,
}) => {
  if (!model.schema?.parameters) {
    return null;
  }

  // Filter visible parameters
  const visibleParams = model.schema.parameters
    .filter(p => !p.ui_hidden)
    .map(p => ({
      param: p,
      uiConfig: getParameterUIConfig(p.name, p, model),
    }))
    .filter(({ uiConfig }) => uiConfig !== null)
    .sort((a, b) => {
      const orderA = a.uiConfig?.order ?? 999;
      const orderB = b.uiConfig?.order ?? 999;
      return orderA - orderB;
    });

  if (visibleParams.length === 0) {
    return null;
  }

  const handleChange = (paramName: string, value: any) => {
    onChange({
      ...values,
      [paramName]: value,
    });
  };

  return (
    <div className="model-parameter-controls">
      <div className="parameter-controls-header">
        <h4>Parameters ({visibleParams.length})</h4>
      </div>
      <div className="parameter-controls-list">
        {visibleParams.map(({ param, uiConfig }) => (
          <div key={param.name} className="parameter-control-item">
            <ParameterInput
              param={param}
              uiConfig={uiConfig!}
              value={values[param.name] ?? param.default}
              onChange={(value) => handleChange(param.name, value)}
              disabled={disabled}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
```

**File:** `frontend/src/features/restoration/utils/parameterUtils.ts`

```typescript
/**
 * Utilities for parameter UI configuration
 */
import type { ParameterSchema, ModelInfo, UIControlConfig } from '../types';

export function getParameterUIConfig(
  paramName: string,
  param: ParameterSchema,
  model: ModelInfo
): UIControlConfig | null {
  // Hidden parameters → return null
  if (param.ui_hidden) {
    return null;
  }

  // Check custom UI config (explicit override)
  if (model.custom?.ui_controls?.[paramName]) {
    return model.custom.ui_controls[paramName];
  }

  // Auto-detect from schema
  return autoDetectUIControl(param);
}

export function autoDetectUIControl(
  param: ParameterSchema
): UIControlConfig {
  // Boolean → toggle
  if (param.type === 'boolean') {
    return { type: 'toggle' };
  }

  // Enum → radio (2-3 options) or dropdown (4+)
  if (param.type === 'enum' && param.values) {
    const type = param.values.length <= 3 ? 'radio' : 'dropdown';
    return { type, options: param.values };
  }

  // Numeric with range → slider
  if ((param.type === 'integer' || param.type === 'float') &&
      param.min != null && param.max != null) {
    return { type: 'slider' };
  }

  // Numeric without range → number input
  if (param.type === 'integer' || param.type === 'float') {
    return { type: 'number' };
  }

  // String → text input
  return { type: 'text' };
}

export function getDefaultParameterValues(
  model: ModelInfo
): Record<string, any> {
  if (!model.schema?.parameters) {
    return {};
  }

  const defaults: Record<string, any> = {};
  model.schema.parameters.forEach(param => {
    if (!param.ui_hidden && param.default !== undefined) {
      defaults[param.name] = param.default;
    }
  });

  return defaults;
}
```

#### 2.3 Update ModelSelector Component

**File:** `frontend/src/features/restoration/components/ModelSelector.tsx`

Modify to include parameter controls in model cards:

```typescript
// Add parameter controls to model cards
<button className="model-card" ...>
  {/* Existing card content */}

  {/* NEW: Show parameter controls when selected */}
  {selectedModel?.id === model.id && (
    <ModelParameterControls
      model={model}
      values={parameterValues}
      onChange={onParameterChange}
      disabled={disabled}
    />
  )}
</button>
```

#### 2.4 Update useImageRestore Hook

**File:** `frontend/src/features/restoration/hooks/useImageRestore.ts`

Add parameter state management:

```typescript
export const useImageRestore = () => {
  // ... existing state ...
  const [parameterValues, setParameterValues] =
    useState<ModelParameterValues>({});

  // Initialize parameters when model changes
  useEffect(() => {
    if (selectedModel) {
      const defaults = getDefaultParameterValues(selectedModel);
      setParameterValues(defaults);
    }
  }, [selectedModel]);

  // Pass parameters to API
  const uploadAndRestore = async () => {
    if (!selectedFile || !selectedModel) return;

    try {
      setIsProcessing(true);
      setError(null);

      const result = await restoreImage(
        selectedFile,
        selectedModel.id,
        parameterValues  // ← Pass user parameters
      );

      setOriginalImageUrl(result.original_url);
      setProcessedImageUrl(result.processed_url);
      setResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    // ... existing returns ...
    parameterValues,
    setParameterValues,
  };
};
```

#### 2.5 Update Restoration Service

**File:** `frontend/src/features/restoration/services/restorationService.ts`

Ensure parameters are sent to API:

```typescript
export async function restoreImage(
  file: File,
  modelId: string,
  parameters?: Record<string, any>
): Promise<RestoreResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model_id', modelId);

  if (parameters && Object.keys(parameters).length > 0) {
    formData.append('parameters', JSON.stringify(parameters));
  }

  const response = await fetch('/api/v1/restore', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Image restoration failed');
  }

  return response.json();
}
```

---

### Phase 3: Styling

#### 3.1 Parameter Controls CSS

**File:** `frontend/src/styles/components/restoration.css`

Add styles for parameter controls:

```css
/* Model Parameter Controls */
.model-parameter-controls {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border-subtle);
}

.parameter-controls-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.parameter-controls-header h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.parameter-controls-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.parameter-control-item {
  display: flex;
  flex-direction: column;
}

/* Parameter Input Base Styles */
.parameter-input {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.parameter-input-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.parameter-input-help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background-color: var(--color-surface-tertiary);
  color: var(--color-text-secondary);
  font-size: 0.6875rem;
  cursor: help;
}

/* Slider Input */
.slider-input {
  width: 100%;
  padding: 0.5rem 0;
}

.slider-input-track {
  position: relative;
  width: 100%;
  height: 0.375rem;
  background-color: var(--color-surface-tertiary);
  border-radius: 0.1875rem;
}

.slider-input-thumb {
  position: absolute;
  width: 1.25rem;
  height: 1.25rem;
  background-color: var(--color-accent);
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.slider-input-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  font-size: 0.6875rem;
  color: var(--color-text-tertiary);
}

/* Radio Input */
.radio-input {
  display: flex;
  gap: 1rem;
}

.radio-input-option {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
}

.radio-input-option input[type="radio"] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

.radio-input-option label {
  font-size: 0.8125rem;
  color: var(--color-text-primary);
  cursor: pointer;
}

/* Toggle Input */
.toggle-input {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toggle-switch {
  position: relative;
  width: 2.75rem;
  height: 1.5rem;
  background-color: var(--color-surface-tertiary);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-switch.active {
  background-color: var(--color-accent);
}

.toggle-switch-thumb {
  position: absolute;
  top: 0.1875rem;
  left: 0.1875rem;
  width: 1.125rem;
  height: 1.125rem;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-switch.active .toggle-switch-thumb {
  transform: translateX(1.25rem);
}
```

---

## Testing Checklist

### Backend Tests

- [ ] Verify `custom` field is included in `/api/v1/models` response
- [ ] Test auto-detection logic with various parameter types
- [ ] Verify parameters are accepted in `/api/v1/restore` endpoint
- [ ] Test validation of parameter values against schema constraints

### Frontend Tests

- [ ] Test parameter controls render correctly for each UI control type
- [ ] Test auto-detection when `custom.ui_controls` is empty
- [ ] Test custom UI config overrides auto-detection
- [ ] Test parameter values are initialized from defaults
- [ ] Test parameter changes update state correctly
- [ ] Test parameters are sent to API on restore
- [ ] Test `ui_hidden` parameters are not displayed
- [ ] Test label override works correctly
- [ ] Test validation respects min/max constraints
- [ ] Test parameter controls are disabled during processing

### Integration Tests

- [ ] Test Google Upscaler with custom UI config (radio + slider)
- [ ] Test FLUX Kontext with auto-detection (dropdown)
- [ ] Test model without parameters shows no controls
- [ ] Test model with all hidden parameters shows no controls
- [ ] Test changing parameter values and restoring image
- [ ] Test parameter values reset when changing models

---

## Migration Path

### For Existing Models

**No changes required** - existing models without `custom.ui_controls` will use auto-detection.

### To Add Custom UI

Add `custom.ui_controls` to model configuration in `local.json`:

```json
{
  "id": "existing-model-id",
  "custom": {
    "ui_controls": {
      "parameter_name": {
        "type": "slider",
        "label": "Custom Label",
        "order": 1
      }
    }
  }
}
```

---

## Future Enhancements

### Phase 2 (Optional)

1. **Parameter Grouping** - Add `group` field to organize parameters
2. **Conditional Parameters** - Show/hide parameters based on other values
3. **Advanced Validation** - Custom validation rules beyond min/max
4. **Presets** - Save/load parameter combinations
5. **Parameter History** - Remember last used values per model
6. **Visual Parameter Editor** - Admin UI to configure `ui_controls` visually

---

## Files to Create/Modify

### Backend Files

**Create:**
- None (schema updates only)

**Modify:**
1. `backend/app/core/config_schema.py` - Add `UIControlConfig` (optional, for docs)
2. `backend/app/api/v1/schemas/model.py` - Add UI control response types
3. `backend/app/api/v1/routes/models.py` - Ensure `custom` included in response
4. `backend/app/api/v1/routes/restoration.py` - Verify parameters accepted

### Frontend Files

**Create:**
1. `frontend/src/features/restoration/components/ModelCard.tsx`
2. `frontend/src/features/restoration/components/ModelParameterControls.tsx`
3. `frontend/src/features/restoration/components/parameter-inputs/ParameterInput.tsx`
4. `frontend/src/features/restoration/components/parameter-inputs/TextInput.tsx`
5. `frontend/src/features/restoration/components/parameter-inputs/NumberInput.tsx`
6. `frontend/src/features/restoration/components/parameter-inputs/SliderInput.tsx`
7. `frontend/src/features/restoration/components/parameter-inputs/DropdownInput.tsx`
8. `frontend/src/features/restoration/components/parameter-inputs/RadioInput.tsx`
9. `frontend/src/features/restoration/components/parameter-inputs/ToggleInput.tsx`
10. `frontend/src/features/restoration/utils/parameterUtils.ts`

**Modify:**
1. `frontend/src/features/restoration/types.ts` - Add UI control types
2. `frontend/src/features/restoration/components/ModelSelector.tsx` - Integrate parameters
3. `frontend/src/features/restoration/hooks/useImageRestore.ts` - Add parameter state
4. `frontend/src/features/restoration/services/restorationService.ts` - Pass parameters to API
5. `frontend/src/styles/components/restoration.css` - Add parameter control styles

### Test Files

**Create:**
1. `frontend/src/features/restoration/components/__tests__/ModelParameterControls.test.tsx`
2. `frontend/src/features/restoration/components/parameter-inputs/__tests__/ParameterInput.test.tsx`
3. `frontend/src/features/restoration/utils/__tests__/parameterUtils.test.ts`

---

## Implementation Order

1. **Backend Schema** (10 min)
   - Update config_schema.py
   - Update model.py API schemas
   - Verify models endpoint includes custom field

2. **Frontend Types** (5 min)
   - Update types.ts with new interfaces

3. **Parameter Utilities** (15 min)
   - Create parameterUtils.ts
   - Implement auto-detection logic
   - Implement default value extraction

4. **Input Components** (60 min)
   - Create base ParameterInput wrapper
   - Create TextInput
   - Create NumberInput
   - Create SliderInput (most complex)
   - Create DropdownInput
   - Create RadioInput
   - Create ToggleInput

5. **Parameter Controls Container** (20 min)
   - Create ModelParameterControls
   - Integrate with ParameterInput
   - Add sorting by order

6. **ModelSelector Integration** (15 min)
   - Update ModelSelector to show parameters
   - Add collapsible behavior

7. **State Management** (15 min)
   - Update useImageRestore hook
   - Add parameter state
   - Initialize from defaults
   - Pass to API

8. **Styling** (30 min)
   - Add CSS for all control types
   - Test responsive behavior
   - Match sqowe design system

9. **Testing** (45 min)
   - Unit tests for utilities
   - Component tests
   - Integration tests

**Total Estimated Time:** ~3.5 hours

---

## Success Criteria

✅ Parameters visible on model cards when model has schema
✅ Hidden parameters (`ui_hidden: true`) not displayed
✅ Auto-detection works when `custom.ui_controls` is empty
✅ Custom UI config overrides auto-detection
✅ Label override works correctly
✅ All UI control types render correctly
✅ Parameter values initialized from defaults
✅ Parameter changes update state
✅ Parameters sent to API on restore
✅ Validation respects schema constraints
✅ Follows sqowe design system
✅ Mobile responsive
✅ Test coverage ≥ 80%

---

**Status:** Ready for Implementation
**Next Step:** Begin with Backend Schema updates
