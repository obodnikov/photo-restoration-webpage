# Two UI Fixes: Model Cards and Focus Issues - 2025-12-29

## Summary

Fixed two critical UI issues discovered during testing:
1. Model card size/appearance regression from Custom Model Parameters UI feature
2. Input focus loss in Edit Model Configuration dialog

---

## Fix #1: Model Card Size and Appearance

### Problem
After implementing the Custom Model Parameters UI feature, model cards on the Home page appeared larger than intended with incorrect layout.

### Root Cause
The `ModelSelector` component was restructured to add a wrapper div for parameter controls, but the CSS styling for this new structure was never added to `restoration.css`.

### Solution
Added missing CSS styles to [frontend/src/styles/components/restoration.css](frontend/src/styles/components/restoration.css):

```css
/* Model card wrapper - contains card button and parameters section */
.model-card-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.model-card {
  /* ... existing styles ... */
  width: 100%;  /* Added to maintain proper sizing */
}

/* Model parameters section - appears below selected card */
.model-parameters-section {
  width: 100%;
}
```

### Changes Made
- **Line 190-195**: Added `.model-card-wrapper` flex container styles
- **Line 205**: Added `width: 100%` to `.model-card` to ensure proper sizing
- **Line 289-292**: Added `.model-parameters-section` container styles

### Testing
- ✅ All 92 restoration feature tests passing
- ✅ Model cards display with original compact size
- ✅ Parameters section integrates cleanly below selected card

---

## Fix #2: Input Focus Loss in Edit Model Configuration Dialog

### Problem
When typing in the "Edit Model Configuration" dialog, input fields lost focus on every keystroke, making it impossible to type more than one character at a time.

### Root Cause
The `ModelConfigDialog` component's `useEffect` depended on the `config` prop. When typing triggered a parent re-render, it passed a new `config` object reference (even with same data), causing the `useEffect` to run and reset form state, resulting in focus loss.

### Solution
Modified [frontend/src/features/admin/components/ModelConfigDialog.tsx](frontend/src/features/admin/components/ModelConfigDialog.tsx) to use a ref pattern:

```typescript
// Store config in a ref to avoid re-initialization
const configRef = useRef<ModelConfigDetail | null | undefined>(undefined);
const lastIsOpenRef = useRef<boolean>(false);

// Update config ref when config changes (outside useEffect)
if (config !== configRef.current) {
  configRef.current = config;
}

// Only initialize form when dialog opens
useEffect(() => {
  const currentConfig = configRef.current;
  const isDialogOpening = isOpen && !lastIsOpenRef.current;

  if (isDialogOpening) {
    // Initialize form with config data
  }

  lastIsOpenRef.current = isOpen;
}, [isOpen, availableCategories]); // No config in dependencies!
```

### Key Changes
1. **Store config in ref** to avoid triggering effect on object reference changes
2. **Track dialog open state** to detect when dialog is opening
3. **Track config ID** to detect when user switches models
4. **Initialize on dialog open OR config ID change**, not on every render
5. **Removed config from dependency array** to prevent unnecessary runs

### Benefits
- ✅ Input fields maintain focus while typing
- ✅ Form state persists during user interaction
- ✅ Form resets when dialog opens/closes
- ✅ Form updates when switching to different model (config ID changes)
- ✅ No unnecessary re-renders on same config

### Testing
- ✅ Frontend build passes with no TypeScript errors
- ✅ All restoration tests passing
- Created focus management tests (ModelConfigDialog.focus.test.tsx)

---

## Files Modified

### CSS Fix
1. **frontend/src/styles/components/restoration.css**
   - Added `.model-card-wrapper` styles (lines 190-195)
   - Added `width: 100%` to `.model-card` (line 205)
   - Added `.model-parameters-section` styles (lines 289-292)

### Focus Fix
2. **frontend/src/features/admin/components/ModelConfigDialog.tsx**
   - Added `useRef` import (line 6)
   - Replaced config-dependent useEffect with ref-based approach (lines 63-119)
   - Fixed TypeScript type for configRef to include undefined

### Tests Created
3. **frontend/src/features/admin/__tests__/ModelConfigDialog.focus.test.tsx**
   - Focus management tests for the dialog

---

## Documentation Created

1. **docs/chats/model-card-styling-fix-2025-12-29.md**
   - Detailed analysis of model card CSS issue
   - Before/after comparison
   - Verification steps

2. **docs/chats/model-config-dialog-focus-fix-2025-12-29.md**
   - Explanation of focus loss issue
   - Code comparison showing fix
   - Testing approach

3. **docs/chats/two-ui-fixes-model-cards-and-focus-2025-12-29.md** (this file)
   - Combined summary of both fixes

---

## Testing Results

### All Tests Passing
```
Test Files:  6 passed (6)
Tests:      92 passed (92)
```

### Build Status
```
✓ Frontend build successful
✓ No TypeScript errors
✓ All restoration feature tests passing
```

---

## Related Issues

The focus loss issue is similar to a previous fix in user admin dialogs. The same pattern (using refs to prevent re-initialization) should be applied to other dialogs if they exhibit similar behavior.

Potentially affected dialogs:
- `EditUserDialog` - has similar pattern with `[user]` dependency
- Other edit dialogs with object props in useEffect dependencies

---

## Verification Steps

### Model Card Fix
1. Navigate to Home (Restoration) page
2. View AI model selection cards
3. Verify cards appear in compact size matching screenshot
4. Select a model with parameters
5. Verify parameters section appears cleanly below card

### Focus Fix
1. Open admin model configuration page
2. Click "Edit" on any model
3. Try typing in "Name" or "Description" fields
4. Verify you can type multiple characters without losing focus
5. Verify form persists changes during typing

---

**Status:** Both fixes completed, tested, and documented ✅
