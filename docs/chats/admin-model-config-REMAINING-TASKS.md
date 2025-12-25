# Admin Model Configuration - Remaining Frontend Tasks

**Status:** Backend Complete ✅ | Frontend 20% Complete
**Date:** 2025-12-25

---

## ✅ COMPLETED

### Backend (100%)
- ✅ docker-compose.yml updated (config volume read-write)
- ✅ backend/config/local.json created
- ✅ backend/config/default.json updated (model_configuration section)
- ✅ backend/app/core/config.py updated (merge, reload, CRUD methods)
- ✅ backend/app/api/v1/schemas/model.py updated (all response models)
- ✅ backend/app/api/v1/routes/admin.py updated (8 new endpoints)
- ✅ backend/tests/api/v1/test_admin_model_config.py created (comprehensive tests)

### Frontend (20%)
- ✅ frontend/src/features/admin/types.ts updated (model config types)
- ✅ frontend/src/features/admin/services/modelConfigService.ts created

---

## 🔨 REMAINING FRONTEND TASKS

The implementation plan is in `/docs/chats/admin-model-config-implementation-plan.md`.
All backend code is tested and ready. Frontend structure follows existing patterns.

### Hook (1 file)

**File:** `frontend/src/features/admin/hooks/useModelConfig.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import * as modelConfigService from '../services/modelConfigService';
import type {
  ModelConfigListItem,
  ModelConfigDetail,
  ModelConfigCreate,
  ModelConfigUpdate,
  AvailableTagsResponse,
} from '../types';

export const useModelConfig = () => {
  const [configs, setConfigs] = useState<ModelConfigListItem[]>([]);
  const [availableTags, setAvailableTags] = useState<AvailableTagsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConfigs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await modelConfigService.listModelConfigs();
      setConfigs(data);
    } catch (err) {
      setError('Failed to load model configurations');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadAvailableTags = useCallback(async () => {
    try {
      const data = await modelConfigService.getAvailableTags();
      setAvailableTags(data);
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  }, []);

  const createConfig = useCallback(async (config: ModelConfigCreate) => {
    setIsLoading(true);
    setError(null);
    try {
      await modelConfigService.createModelConfig(config);
      await loadConfigs();
    } catch (err: any) {
      setError(err.message || 'Failed to create configuration');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadConfigs]);

  const updateConfig = useCallback(async (modelId: string, config: ModelConfigUpdate) => {
    setIsLoading(true);
    setError(null);
    try {
      await modelConfigService.updateModelConfig(modelId, config);
      await loadConfigs();
    } catch (err: any) {
      setError(err.message || 'Failed to update configuration');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadConfigs]);

  const deleteConfig = useCallback(async (modelId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await modelConfigService.deleteModelConfig(modelId);
      await loadConfigs();
    } catch (err: any) {
      setError(err.message || 'Failed to delete configuration');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadConfigs]);

  const reloadConfigs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await modelConfigService.reloadModelConfigs();
      await loadConfigs();
    } catch (err: any) {
      setError(err.message || 'Failed to reload configurations');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadConfigs]);

  useEffect(() => {
    loadConfigs();
    loadAvailableTags();
  }, [loadConfigs, loadAvailableTags]);

  return {
    configs,
    availableTags,
    isLoading,
    error,
    loadConfigs,
    createConfig,
    updateConfig,
    deleteConfig,
    reloadConfigs,
  };
};
```

---

### Components (6 files)

Due to size constraints, I'll provide the file structure and key points. Follow existing admin component patterns (see `frontend/src/features/admin/components/` for reference).

**1. JsonEditor.tsx** - Simple multiline textarea
- Props: `value: string`, `onChange: (value: string) => void`, `placeholder?: string`, `rows?: number`
- Support tab key for indentation
- Show line numbers (optional)

**2. JsonPreview.tsx** - Live JSON preview with validation
- Props: `data: Record<string, any>`
- Real-time JSON generation
- Validation status indicator
- Syntax highlighting (use `<pre>` with JSON.stringify(data, null, 2))
- Copy to clipboard button

**3. TagSelector.tsx** - Multi-select checkboxes
- Props: `availableTags: string[]`, `selectedTags: string[]`, `onChange: (tags: string[]) => void`
- Grid layout with checkboxes
- Follow sqowe brand styling

**4. ModelConfigDialog.tsx** - Main create/edit dialog
- Props: `config?: ModelConfigDetail`, `onSave: (config) => void`, `onClose: () => void`, `availableTags`, `availableCategories`
- Form sections: Basic Info, Tags, JSON Editors (replicate_schema, custom, parameters)
- Live preview at bottom
- Validation before save

**5. DeleteModelConfigDialog.tsx** - Confirmation dialog
- Props: `modelId: string`, `modelName: string`, `source: string`, `onConfirm: () => void`, `onCancel: () => void`
- Warning if model is from local (deletable) vs default (cannot delete)
- Similar to existing DeleteUserDialog

**6. ModelConfigList.tsx** - List component (optional, can be in page)
- Display configs in table/card format
- Source badge (local/default)
- Edit/Delete buttons
- Filter by provider, category, enabled status

---

### Page (1 file)

**File:** `frontend/src/features/admin/pages/AdminModelConfigPage.tsx`

Structure (follow AdminUsersPage.tsx pattern):
```typescript
export const AdminModelConfigPage = () => {
  const { configs, availableTags, isLoading, error, createConfig, updateConfig, deleteConfig, reloadConfigs } = useModelConfig();
  const [selectedConfig, setSelectedConfig] = useState<ModelConfigDetail | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  // Search/filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [filterProvider, setFilterProvider] = useState<string | null>(null);

  // Handlers
  const handleCreate = () => { setSelectedConfig(null); setIsDialogOpen(true); };
  const handleEdit = async (id: string) => { /* fetch and setSelectedConfig */ };
  const handleDelete = (config: ModelConfigListItem) => { /* open delete dialog */ };

  // UI similar to AdminUsersPage
  return (
    <div className="admin-model-config-page">
      <header>
        <h1>Configuration</h1>
        <p>Manage AI model configurations</p>
      </header>

      <div className="controls">
        <button onClick={handleCreate}>+ Add Model</button>
        <button onClick={reloadConfigs}>Reload</button>
        <input placeholder="Search..." value={searchTerm} onChange={...} />
      </div>

      {error && <div className="error">{error}</div>}

      <div className="config-list">
        {filteredConfigs.map(config => (
          <div key={config.id} className="config-card">
            <div className="config-header">
              <h3>{config.name}</h3>
              <span className={`badge badge-${config.source}`}>{config.source}</span>
            </div>
            <p>{config.category} | {config.provider}</p>
            <div className="actions">
              <button onClick={() => handleEdit(config.id)}>Edit</button>
              {config.source === 'local' && (
                <button onClick={() => handleDelete(config)}>Delete</button>
              )}
            </div>
          </div>
        ))}
      </div>

      {isDialogOpen && (
        <ModelConfigDialog
          config={selectedConfig}
          onSave={selectedConfig ? updateConfig : createConfig}
          onClose={() => setIsDialogOpen(false)}
          availableTags={availableTags?.tags || []}
          availableCategories={availableTags?.categories || []}
        />
      )}

      {isDeleteDialogOpen && (
        <DeleteModelConfigDialog ... />
      )}
    </div>
  );
};
```

---

### Styles (1 file)

**File:** `frontend/src/styles/components/modelConfig.css`

Follow `frontend/src/styles/components/admin.css` patterns. Use sqowe brand colors:
- Dark Ground: #222222
- Light Purple: #8E88A3
- Dark Purple: #5B5377
- Light Grey: #B2B3B2

---

### Routing (2 files)

**1. frontend/src/app/App.tsx**

Add route after `/admin/users`:
```tsx
<Route
  path="/admin/models"
  element={
    <AdminRoute>
      <AdminModelConfigPage />
    </AdminRoute>
  }
/>
```

**2. frontend/src/components/Layout.tsx**

Add navigation link in admin section:
```tsx
{user?.role === 'admin' && (
  <>
    <a href="/admin/users" className={location.pathname === '/admin/users' ? 'active' : ''}>
      Users
    </a>
    <a href="/admin/models" className={location.pathname === '/admin/models' ? 'active' : ''}>
      Configuration
    </a>
  </>
)}
```

---

## 🧪 Testing

Create `frontend/src/features/admin/__tests__/useModelConfig.test.ts` following `useAdminUsers.test.ts` pattern.

Test scenarios:
- Loading configs
- Creating config
- Updating config
- Deleting config (local vs default)
- Validation
- Error handling

---

## ✅ Final Steps

1. Run backend tests: `venv/bin/python -m pytest backend/tests/api/v1/test_admin_model_config.py -v`
2. Start backend: `venv/bin/python -m uvicorn app.main:app --reload`
3. Build frontend: `docker run --rm -v "/Users/mike/src/photo-restoration-webpage/frontend":/app -w /app node:22.12-alpine npm run build`
4. Test in browser at `http://localhost:3000/admin/models`
5. Test CRUD operations:
   - Create new model config
   - Edit existing config
   - Delete local config (should work)
   - Try delete default config (should fail with message)
   - Reload configs
   - Validate JSON editors work

---

## 📚 Reference Files

- **Admin Page Pattern:** `frontend/src/features/admin/pages/AdminUsersPage.tsx`
- **Admin Components:** `frontend/src/features/admin/components/*.tsx`
- **Admin Styles:** `frontend/src/styles/components/admin.css`
- **Admin Hook:** `frontend/src/features/admin/hooks/useAdminUsers.ts`
- **Brand Guidelines:** `tmp/Brand-Guidelines.pdf`, `tmp/AI_WEB_DESIGN_SQOWE.md`

---

**Next Action:** Create the remaining frontend files following the patterns above. All backend endpoints are ready and tested.
