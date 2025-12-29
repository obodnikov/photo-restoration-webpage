# Model Card Styling Fix - 2025-12-29

## Problem Identified

During the Custom Model Parameters UI feature implementation (commit `ef0bcbc` on 2025-12-29), the `ModelSelector` component structure was changed but the corresponding CSS was not updated, causing model cards to appear with incorrect size and layout.

### Root Cause

The component was restructured from:
```jsx
<button className="model-card">...</button>
```

To:
```jsx
<div className="model-card-wrapper">
  <button className="model-card">...</button>
  <div className="model-parameters-section">
    <ModelParameterControls />
  </div>
</div>
```

However, the CSS file (`frontend/src/styles/components/restoration.css`) was never updated to include styles for:
1. `.model-card-wrapper` - the new wrapper div
2. `.model-parameters-section` - the parameters container

This caused the wrapper div to take up the full grid cell without proper constraints, making cards appear larger than intended.

## Solution Implemented

Added missing CSS styles to `frontend/src/styles/components/restoration.css`:

### 1. Model Card Wrapper Styles
```css
/* Model card wrapper - contains card button and parameters section */
.model-card-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0;
}
```

**Purpose:**
- Establishes a flex container that stacks the card button and parameters section vertically
- No gap between elements for clean visual integration
- Allows the card button to maintain its original size
- Parameters section expands only when a model is selected

### 2. Model Card Button Styles
```css
.model-card {
  background: white;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  cursor: pointer;
  transition: all var(--transition-base);
  text-align: left;
  width: 100%;  /* ADDED: Ensures card takes full wrapper width */
}
```

**Changes:**
- Added `width: 100%` to ensure the button takes the full width of its wrapper
- This prevents the card from shrinking and maintains consistent sizing

### 3. Parameters Section Styles
```css
/* Model parameters section - appears below selected card */
.model-parameters-section {
  width: 100%;
}
```

**Purpose:**
- Ensures parameters section takes full width of the wrapper
- Provides a clean integration point for `ModelParameterControls` component
- Only visible when a model is selected (controlled by React conditional rendering)

## Impact

### Before Fix
- Model cards appeared too large and stretched
- Wrapper div had no styling, causing layout issues
- Grid cells expanded unpredictably
- Visual inconsistency with original design

### After Fix
- Model cards maintain their original compact appearance
- Cards are properly constrained within their grid cells
- Parameters section integrates seamlessly below selected card
- Consistent with the original design shown in the screenshot

## Testing

All 12 ModelSelector tests passing:
```
✓ should show loading state initially
✓ should render models after loading
✓ should auto-select first model if none selected
✓ should not auto-select if model already selected
✓ should call onSelectModel when model card clicked
✓ should show selected model with selected class
✓ should display model tags
✓ should show error message on load failure
✓ should retry loading on error close
✓ should show empty state when no models available
✓ should disable model cards when disabled prop is true
✓ should render ModelParameterControls for selected model
```

## Files Modified

1. **frontend/src/styles/components/restoration.css**
   - Added `.model-card-wrapper` styles (lines 190-195)
   - Updated `.model-card` with `width: 100%` (line 205)
   - Added `.model-parameters-section` styles (lines 297-300)

## Related Issues

This fix addresses the visual regression introduced during the Custom Model Parameters UI feature implementation. The feature itself is working correctly; only the CSS styling was missing.

## Verification Steps

To verify the fix:
1. Start the frontend application
2. Navigate to the Home (Restoration) page
3. View the AI model selection cards
4. Verify cards appear in their original compact size
5. Select a model with parameters
6. Verify parameters section appears below the card without disrupting layout
7. Switch between models to ensure consistent behavior

## Architecture Notes

This change aligns with the feature's architecture decision to:
- Keep model cards as buttons for accessibility
- Wrap cards with parameters in a container for clean layout
- Use conditional rendering to show/hide parameters
- Maintain backward compatibility with models that have no parameters
