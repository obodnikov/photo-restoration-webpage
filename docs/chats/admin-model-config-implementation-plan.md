# Admin Model Configuration Page - Implementation Plan

**Date:** 2025-12-25
**Status:** Ready for Implementation
**Feature:** Admin Configuration Tab for Model Management

---

## Requirements Summary

### User Request
Add a new admin-only "Configuration" tab that allows administrators to manage AI model configurations through a web interface. Configurations should be stored in a `local.json` file with priority over default configurations.

### Key Features
1. **Admin-only access** - Visible only to users with admin role
2. **CRUD operations** for model configurations
3. **Form-based editing** for basic fields
4. **JSON editors** for complex objects (replicate_schema, custom, parameters)
5. **Live JSON preview** with validation and error display
6. **Tag selector** with predefined values
7. **Priority system** - local.json overrides production.json/default.json
8. **Hot reload** - Configuration changes apply without server restart

---

## All Questions Resolved ✅

### 1. Config File Location ✅
**Decision:** Store `local.json` in `backend/config/` directory
- **Confirmed:** Docker volume mounts `./backend/config:/app/config:ro` (currently read-only)
- **Action Required:** Change volume mount to read-write for local.json support
- **Location:** `/app/config/local.json` inside container = `backend/config/local.json` on host

### 2. Restart Required ✅
**Decision:** Implement hot reload
- Configuration changes apply without server restart
- Use file watcher or reload endpoint to refresh config in memory
- Settings class method to reload models from disk

### 3. Tag Values ✅
**Decision:** Create configurable tag array in default.json
- **Default values:** `["restore", "replicate", "advanced", "enhance", "upscale", "fast"]`
- **Location:** New section in `backend/config/default.json`
- **Technical Debt:** Add idea to make Category field configurable as well

### 4. Permissions ✅
**Decision:** Use existing admin role
- Regular admin users can manage model configurations
- No need for super-admin or additional permission levels
- Same role check as admin user management

### 5. Validation Level ✅
**Decision:** Warn and use defaults (as per existing flexible schema system)
- Frontend: Display validation errors but allow saving
- Backend: Pydantic validation with clear error messages
- Invalid configs are logged but don't crash the system

### 6. UI Complexity ✅
**Decision:** Keep JSON text areas for complex objects
- Simple approach: multiline textarea for replicate_schema, custom, parameters
- **Technical Debt:** Add idea for full schema editor with visual form builder

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Admin Configuration Page                │
│         (admin role required, new tab)               │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              Backend API Endpoints                   │
│  GET  /api/v1/admin/models/config                   │
│  GET  /api/v1/admin/models/config/{id}              │
│  POST /api/v1/admin/models/config                   │
│  PUT  /api/v1/admin/models/config/{id}              │
│  DELETE /api/v1/admin/models/config/{id}            │
│  GET  /api/v1/admin/models/tags                     │
│  POST /api/v1/admin/models/validate                 │
│  POST /api/v1/admin/models/reload                   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              Config Priority System                  │
│  1. local.json (highest priority)                   │
│  2. production.json                                  │
│  3. default.json (fallback)                         │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              Config File Structure                   │
│  backend/config/local.json                          │
│  backend/config/production.json                     │
│  backend/config/default.json                        │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Backend Changes

#### 1. Update docker-compose.yml
```yaml
# Change from read-only to read-write for local.json support
volumes:
  - ./backend/config:/app/config  # Remove :ro flag
```

#### 2. Create backend/config/local.json
```json
{
  "models": []
}
```

#### 3. Update backend/config/default.json
Add new section for configurable tags:
```json
{
  "model_configuration": {
    "available_tags": ["restore", "replicate", "advanced", "enhance", "upscale", "fast"],
    "available_categories": ["restore", "upscale", "enhance"]
  }
}
```

#### 4. Update backend/app/core/config.py
- Add `get_available_tags()` method
- Add `get_available_categories()` method
- Modify `get_models()` to merge configs with priority: local.json → production.json → default.json
- Add `reload_models()` method for hot reload
- Add `save_local_model_config(model_data)` method
- Add `delete_local_model_config(model_id)` method

#### 5. Create/Update backend/app/api/v1/routes/admin.py
Add new endpoints:
```python
@router.get("/models/config")
async def list_model_configs(...)
  # Return all models with source indicator (local/default)

@router.get("/models/config/{model_id}")
async def get_model_config(model_id: str, ...)
  # Get specific model config with full details

@router.post("/models/config")
async def create_model_config(...)
  # Create new model in local.json

@router.put("/models/config/{model_id}")
async def update_model_config(model_id: str, ...)
  # Update model in local.json

@router.delete("/models/config/{model_id}")
async def delete_model_config(model_id: str, ...)
  # Delete from local.json

@router.get("/models/tags")
async def get_available_tags(...)
  # Get predefined tag values from config

@router.post("/models/validate")
async def validate_model_config(...)
  # Validate model config JSON structure

@router.post("/models/reload")
async def reload_model_configs(...)
  # Hot reload all model configurations
```

#### 6. Update backend/app/api/v1/schemas/model.py
Add new Pydantic models:
```python
class ModelConfigSource(str, Enum):
    LOCAL = "local"
    PRODUCTION = "production"
    DEFAULT = "default"

class ModelConfigDetail(BaseModel):
    # Full model config including replicate_schema
    source: ModelConfigSource
    # All fields from model config

class ModelConfigListItem(BaseModel):
    id: str
    name: str
    provider: str
    category: str
    enabled: bool
    source: ModelConfigSource

class AvailableTagsResponse(BaseModel):
    tags: list[str]
    categories: list[str]
```

### Frontend Changes

#### 1. Create frontend/src/features/admin/pages/AdminModelConfigPage.tsx
Main configuration page with:
- List of model configs with source badges (local/default)
- Search and filter (by provider, category, enabled status)
- "Add Model" button
- Edit/Delete actions per model

#### 2. Create frontend/src/features/admin/components/ModelConfigDialog.tsx
Dialog for create/edit with:
- Basic info form (id, name, model, provider, category, description, version, enabled)
- Tag selector (multi-select checkboxes)
- JSON editors (replicate_schema, custom, parameters)
- Live JSON preview with validation
- Save/Cancel buttons

#### 3. Create frontend/src/features/admin/components/JsonEditor.tsx
Multiline textarea with:
- Syntax highlighting (optional, can use simple textarea initially)
- Line numbers (optional)
- Tab key support for indentation

#### 4. Create frontend/src/features/admin/components/JsonPreview.tsx
Live preview component with:
- Real-time JSON generation from form fields
- Validation status indicator (✓ Valid JSON / ✗ Error at line X)
- Syntax highlighting
- Copy to clipboard button

#### 5. Create frontend/src/features/admin/components/TagSelector.tsx
Multi-select component with:
- Checkboxes for each predefined tag
- Fetches available tags from backend
- Returns array of selected tags

#### 6. Create frontend/src/features/admin/components/DeleteModelConfigDialog.tsx
Confirmation dialog with:
- Warning message about deletion
- Indicator if model is from local.json (deletable) or default (cannot delete)
- Confirm/Cancel buttons

#### 7. Create frontend/src/features/admin/services/modelConfigService.ts
API client methods:
```typescript
export const modelConfigService = {
  async listConfigs(): Promise<ModelConfigListItem[]>
  async getConfig(modelId: string): Promise<ModelConfigDetail>
  async createConfig(config: ModelConfigCreate): Promise<void>
  async updateConfig(modelId: string, config: ModelConfigUpdate): Promise<void>
  async deleteConfig(modelId: string): Promise<void>
  async getAvailableTags(): Promise<AvailableTagsResponse>
  async validateConfig(config: any): Promise<ValidationResult>
  async reloadConfigs(): Promise<void>
}
```

#### 8. Create frontend/src/features/admin/hooks/useModelConfig.ts
Hook for managing config state:
```typescript
export const useModelConfig = () => {
  const [configs, setConfigs] = useState<ModelConfigListItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadConfigs = async () => {...}
  const createConfig = async (config) => {...}
  const updateConfig = async (id, config) => {...}
  const deleteConfig = async (id) => {...}
  const reloadConfigs = async () => {...}

  return { configs, isLoading, error, loadConfigs, ... }
}
```

#### 9. Update frontend/src/app/App.tsx
Add new route:
```tsx
<Route
  path="/admin/models"
  element={<AdminRoute><AdminModelConfigPage /></AdminRoute>}
/>
```

#### 10. Update frontend/src/components/Layout.tsx
Add "Configuration" link to admin section:
```tsx
{user?.role === 'admin' && (
  <>
    <a href="/admin/users">Users</a>
    <a href="/admin/models">Configuration</a>
  </>
)}
```

#### 11. Create frontend/src/styles/components/modelConfig.css
Styles based on sqowe brand guidelines:
- Dark Ground (#222222) for headers
- Light Purple (#8E88A3) for accents
- Dark Purple (#5B5377) for buttons
- Light Grey (#B2B3B2) for borders

---

## Technical Debts to Add

### 1. Full Schema Editor
**File:** TECHNICAL_DEBTS.md
**Section:** Admin - Model Configuration
**Description:**
Instead of JSON text areas for `replicate_schema`, `custom`, and `parameters` objects, create a visual form builder that:
- Dynamically generates form fields based on schema structure
- Provides type-specific inputs (enum → dropdown, integer → number input with min/max)
- Validates in real-time
- Offers better UX for non-technical users

**Effort:** 8-12 hours
**Priority:** LOW

### 2. Configurable Category Field
**File:** TECHNICAL_DEBTS.md
**Section:** Admin - Model Configuration
**Description:**
Make the `category` field configurable like tags:
- Store available categories in config file
- Allow admins to add/edit/delete categories
- Update UI to use dynamic category list
- Ensure backward compatibility with existing models

**Effort:** 2-3 hours
**Priority:** LOW

---

## File Changes Summary

### New Files (Backend: 1)
```
backend/config/local.json
```

### Modified Files (Backend: 3)
```
backend/config/default.json (add model_configuration section)
backend/app/core/config.py (add config merge, reload, CRUD methods)
backend/app/api/v1/routes/admin.py (add model config endpoints)
backend/app/api/v1/schemas/model.py (add new response models)
docker-compose.yml (change config volume from :ro to read-write)
```

### New Files (Frontend: 9)
```
frontend/src/features/admin/pages/AdminModelConfigPage.tsx
frontend/src/features/admin/components/ModelConfigDialog.tsx
frontend/src/features/admin/components/JsonEditor.tsx
frontend/src/features/admin/components/JsonPreview.tsx
frontend/src/features/admin/components/TagSelector.tsx
frontend/src/features/admin/components/DeleteModelConfigDialog.tsx
frontend/src/features/admin/services/modelConfigService.ts
frontend/src/features/admin/hooks/useModelConfig.ts
frontend/src/styles/components/modelConfig.css
```

### Modified Files (Frontend: 2)
```
frontend/src/app/App.tsx (add route)
frontend/src/components/Layout.tsx (add nav link)
```

---

## Implementation Checklist

### Pre-Implementation ✅
- [x] Verify config file location (backend/config/)
- [x] Confirm hot reload requirement
- [x] Define predefined tag values
- [x] Confirm permission model (existing admin role)
- [x] Decide UI complexity (JSON text areas)
- [x] Document all decisions

### Backend Implementation
- [ ] Update docker-compose.yml (remove :ro from config volume)
- [ ] Create backend/config/local.json
- [ ] Update backend/config/default.json (add model_configuration section)
- [ ] Update backend/app/core/config.py (priority merge, reload, CRUD)
- [ ] Update backend/app/api/v1/routes/admin.py (add 7 new endpoints)
- [ ] Update backend/app/api/v1/schemas/model.py (add response models)
- [ ] Test backend endpoints with Postman/curl
- [ ] Test hot reload functionality
- [ ] Test config priority system (local overrides production)

### Frontend Implementation
- [ ] Create AdminModelConfigPage.tsx
- [ ] Create ModelConfigDialog.tsx
- [ ] Create JsonEditor.tsx
- [ ] Create JsonPreview.tsx
- [ ] Create TagSelector.tsx
- [ ] Create DeleteModelConfigDialog.tsx
- [ ] Create modelConfigService.ts
- [ ] Create useModelConfig.ts
- [ ] Create modelConfig.css (following sqowe brand guidelines)
- [ ] Update App.tsx (add route)
- [ ] Update Layout.tsx (add nav link)
- [ ] Test UI with various config scenarios
- [ ] Test validation and error handling
- [ ] Test JSON preview updates in real-time

### Technical Debts
- [ ] Add "Full Schema Editor" to TECHNICAL_DEBTS.md
- [ ] Add "Configurable Category Field" to TECHNICAL_DEBTS.md

### Testing
- [ ] Test create new model config
- [ ] Test edit existing model config
- [ ] Test delete local model config
- [ ] Test cannot delete default model config
- [ ] Test validation errors display correctly
- [ ] Test live JSON preview
- [ ] Test tag selector
- [ ] Test hot reload after config change
- [ ] Test config priority (local overrides production)
- [ ] Test admin-only access (non-admin cannot see tab)

### Documentation
- [ ] Update README.md with configuration management section
- [ ] Add API documentation for new endpoints
- [ ] Add user guide for model configuration

---

## Success Criteria

✅ **All questions answered and decisions documented**
✅ **Implementation plan created with detailed file changes**
✅ **Technical debts documented**
✅ **Ready to begin implementation**

---

## Next Steps

**User:** Please review this implementation plan and confirm:
1. All requirements are correctly understood
2. All questions have been answered
3. Ready to proceed with implementation

**Developer:** Once confirmed, begin implementation following the checklist above.

---

**Document Created:** 2025-12-25
**Last Updated:** 2025-12-25
**Status:** ✅ Ready for Implementation
