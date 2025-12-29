# Model Config Dialog Focus Fix - 2025-12-29

## Problem

When typing in the "Edit Model Configuration" dialog, input fields lose focus on every keystroke. This makes it impossible to type more than one character at a time.

## Root Cause

The `ModelConfigDialog` component has a `useEffect` that depends on the `config` prop. When the parent component re-renders (which can happen on every keystroke due to state updates), it passes a new `config` object reference, even if the content is the same. This triggers the `useEffect` to run and reset the form state, causing focus loss.

## Original Code (Problematic)

```typescript
useEffect(() => {
  if (config) {
    setFormData({
      id: config.id,
      name: config.name,
      // ... other fields
    });
    // ... set other state
  }
  // ...
}, [config, availableCategories]); // ← config object reference in deps
```

**Problem:** Every time parent re-renders and creates a new `config` object (even with same data), this effect runs and resets the form.

## Solution

Use a ref to store the config and only initialize the form when:
1. The dialog opens
2. The config ID changes while dialog is open (user switches models)

This prevents re-initialization on every render while still handling config changes correctly.

```typescript
// Store config in a ref to avoid re-initialization when config object reference changes
const configRef = useRef<ModelConfigDetail | null | undefined>(undefined);
const lastIsOpenRef = useRef<boolean>(false);
const lastConfigIdRef = useRef<string | null>(null);

// Update config ref when config changes
if (config !== configRef.current) {
  configRef.current = config;
}

// Load config data when editing - only when dialog opens or config ID changes
useEffect(() => {
  const currentConfig = configRef.current;
  const currentConfigId = currentConfig?.id || null;
  const isDialogOpening = isOpen && !lastIsOpenRef.current;
  const isConfigChanged = isOpen && currentConfigId !== lastConfigIdRef.current;

  // Initialize form when:
  // 1. Dialog is opening (wasn't open before, now is open)
  // 2. OR config ID changed while dialog is already open (user switched models)
  if (isDialogOpening || isConfigChanged) {
    if (currentConfig) {
      setFormData({
        id: currentConfig.id,
        name: currentConfig.name,
        // ... other fields
      });
      // ... set other state
    }
  }

  // Update refs for next render
  lastIsOpenRef.current = isOpen;
  lastConfigIdRef.current = currentConfigId;
}, [isOpen, availableCategories]); // ← No config in deps!
```

## Key Changes

1. **Use `configRef`** to store the config without triggering re-renders
2. **Track `isOpen` state** to detect when dialog is opening
3. **Track `lastConfigIdRef`** to detect when config ID changes
4. **Initialize on dialog open OR config ID change**, not on every render
5. **Remove `config` from dependency array** to prevent unnecessary effect runs

## Benefits

- ✅ Input fields maintain focus while typing
- ✅ Form state persists during user interaction
- ✅ Form resets when dialog opens/closes
- ✅ Form updates when switching to a different model (config ID changes)
- ✅ No unnecessary re-renders on same config

## Same Issue in Other Dialogs

The same pattern exists in:
- `EditUserDialog` - has `useEffect` with `[user]` dependency
- Potentially other edit dialogs

These should be fixed with the same pattern if they exhibit focus loss issues.

## Testing

Created `ModelConfigDialog.focus.test.tsx` to verify:
- Focus is maintained when typing in text inputs
- Form state persists across renders
- Form only resets when dialog opens

## Related Previous Fix

This is similar to an issue that was previously fixed in the user admin dialogs. The solution uses refs to prevent unnecessary re-initialization of form state.
