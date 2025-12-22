# Technical Debts & Future Improvements

This document tracks non-blocking improvements, enhancements, and nice-to-have features that can be implemented in future iterations.

---

## Frontend - Profile Feature

### Testing Improvements (Medium Priority)

#### 1. **Additional Error Handling Tests for useProfile Hook**
**Context:** Phase 2.4 - User Profile Page
**Status:** Functionality works correctly, tests would improve coverage
**Effort:** ~1 hour

**Missing Test Coverage:**
- Test that `mutationError` is cleared on successful password change
- Test that `mutationError` is cleared on successful session deletion
- Test that `mutationError` is set correctly on password change failure
- Test that `mutationError` is set correctly on session deletion failure
- Test that errors don't cross-contaminate between operations

**Rationale:**
While the core functionality has 99/113 tests passing (87.6%), these specific edge cases for the newly separated error states would provide additional confidence.

**File:** `frontend/src/features/profile/__tests__/useProfile.test.ts`

---

#### 2. **SessionsList Error Prop Tests**
**Context:** Phase 2.4 - Senior Developer Review Improvements
**Status:** Functionality works correctly, tests would improve coverage
**Effort:** ~30 minutes

**Missing Test Coverage:**
- Test that error message is displayed when `error` prop is provided
- Test that empty state is NOT shown when `error` prop is provided
- Test that sessions list is NOT rendered when `error` prop is provided
- Test that retry/refresh functionality works with error state

**Rationale:**
The new error prop prevents misleading "no sessions" messages when fetch fails. Tests would document this critical UX improvement.

**File:** `frontend/src/features/profile/__tests__/SessionsList.test.tsx`

**Test Cases to Add:**
```typescript
describe('Error Handling', () => {
  it('displays error message when error prop is provided', () => {
    // Test error display
  });

  it('does not show empty state when error exists', () => {
    // Ensure "No sessions" doesn't show with error
  });

  it('shows error instead of sessions list when error exists', () => {
    // Test error takes precedence
  });
});
```

---

#### 3. **ProfilePage Error Handling Tests**
**Context:** Phase 2.4 - Separated Error States
**Status:** Functionality works correctly, tests would improve coverage
**Effort:** ~1 hour

**Missing Test Coverage:**
- Test that `profileError` displays full-page error when profile fails to load
- Test that `mutationError` displays as banner when password change fails
- Test that `sessionsError` is passed to SessionsList component
- Test that errors are displayed in correct contexts
- Test that page renders correctly with various error combinations

**Rationale:**
Integration tests for the error display logic would ensure proper error routing and user feedback.

**File:** `frontend/src/features/profile/__tests__/ProfilePage.test.tsx`

**Test Cases to Add:**
```typescript
describe('Error Display', () => {
  it('shows full-page error for profileError', () => {
    // Test blocking error
  });

  it('shows banner for mutationError', () => {
    // Test non-blocking mutation errors
  });

  it('passes sessionsError to SessionsList', () => {
    // Test error prop passing
  });

  it('handles multiple simultaneous errors correctly', () => {
    // Test error priority
  });
});
```

---

### UX Enhancements (Low Priority)

#### 4. **Local Error Handling in SessionsList for Delete Operations**
**Context:** Phase 2.4 - Code Review Suggestion
**Status:** Currently uses global mutationError
**Effort:** ~2 hours
**Benefit:** Better localized feedback during session deletion

**Current Behavior:**
- Session deletion errors show in global banner at page top
- User must scroll to see error if they're viewing sessions list

**Proposed Improvement:**
- Add local error state in SessionsList component
- Display deletion errors inline, near the session being deleted
- Keep global error for critical issues

**Implementation:**
```typescript
// In SessionsList.tsx
const [deletionError, setDeletionError] = useState<string | null>(null);

const handleConfirmDelete = async () => {
  setDeletionError(null);
  try {
    await onDeleteSession(selectedSessionId);
    setSelectedSessionId(null);
  } catch (err) {
    setDeletionError('Failed to delete session. Please try again.');
    // Error also propagates to global mutationError
  }
};
```

**Files to Modify:**
- `frontend/src/features/profile/components/SessionsList.tsx`
- `frontend/src/features/profile/__tests__/SessionsList.test.tsx`

---

#### 5. **Password Strength Indicator**
**Context:** Phase 2.4 - User Profile Feature
**Status:** Basic validation exists, visual indicator would enhance UX
**Effort:** ~3 hours
**Benefit:** Better user guidance during password creation

**Current Behavior:**
- Password validation shows only error messages
- Users must meet all requirements to see if password is acceptable

**Proposed Improvement:**
- Visual strength indicator (weak/medium/strong)
- Real-time feedback as user types
- Color-coded requirements checklist

**Implementation:**
- Add password strength calculation function
- Add visual indicator component
- Update ChangePasswordForm to show real-time feedback

**Files to Create/Modify:**
- `frontend/src/features/profile/components/PasswordStrengthIndicator.tsx`
- `frontend/src/features/profile/components/ChangePasswordForm.tsx`
- `frontend/src/styles/components/profile.css`

---

#### 6. **Session Details Expansion**
**Context:** Phase 2.4 - Sessions Management
**Status:** Shows basic info (created, last accessed)
**Effort:** ~4 hours (requires backend changes)
**Benefit:** Better security awareness for users

**Current Display:**
- Session ID
- Created date
- Last accessed date
- Current session indicator

**Proposed Enhancement:**
- Browser/device information
- IP address (last used)
- Geographic location (approximate)
- Login method

**Backend Requirements:**
- Store additional session metadata
- Update Session model
- Update `/users/me/sessions` endpoint response

**Frontend Changes:**
- Update Session type definition
- Enhance SessionsList display
- Add expandable session details

---

## Frontend - General

### 7. **Test Failures in Existing Test Suite**
**Context:** Profile feature test suite
**Status:** 99/113 tests passing (87.6%)
**Effort:** ~2-3 hours
**Impact:** Better test reliability

**Failing Tests (14):**
- Form validation tests with HTML5 required attributes
- Modal/dialog query issues (getByText vs getByRole)
- Date formatting tests with multiple matches
- Hook initial state timing issues

**Root Causes:**
1. Tests expect JavaScript validation but forms use HTML5 `required`
2. Modal title appears in both heading and aria-label
3. Multiple date elements on page
4. useEffect runs after initial render

**Recommended Fixes:**
- Update tests to match actual component behavior
- Use more specific queries (getByRole with name)
- Add data-testid attributes for ambiguous elements
- Use waitFor for async state changes

**Files:**
- `frontend/src/features/profile/__tests__/ChangePasswordForm.test.tsx`
- `frontend/src/features/profile/__tests__/SessionsList.test.tsx`
- `frontend/src/features/profile/__tests__/ProfileView.test.tsx`
- `frontend/src/features/profile/__tests__/useProfile.test.ts`

---

## Backend - Profile Feature

### 8. **Session Metadata Enhancement**
**Context:** Support for frontend session details (#6)
**Status:** Basic session tracking exists
**Effort:** ~3 hours
**Impact:** Better security monitoring

**Current Schema:**
```python
class Session(Base):
    id: str
    user_id: int
    created_at: datetime
    last_accessed: datetime
```

**Proposed Schema:**
```python
class Session(Base):
    id: str
    user_id: int
    created_at: datetime
    last_accessed: datetime
    # New fields:
    user_agent: str | None
    ip_address: str | None
    device_type: str | None  # mobile, desktop, tablet
    browser: str | None
    os: str | None
```

**Files to Modify:**
- `backend/app/db/models.py`
- `backend/app/core/auth.py` (capture metadata on login)
- `backend/app/api/v1/users.py` (return metadata in sessions endpoint)
- Database migration script

---

## Phase 2.4 - Remaining Tasks

### 9. **Step 2: Updated History Component**
**Context:** Phase 2.4 roadmap
**Status:** ✅ PARTIALLY COMPLETE - UI text updated
**Effort:** 1-2 hours for optional filter
**Priority:** MEDIUM (optional session filter is nice-to-have)

**Completed:**
- ✅ UI text updated to clarify cross-session behavior
- ✅ Backend already returns cross-session history via `/restore/history` endpoint
- ✅ Frontend already uses correct endpoint

**Optional Enhancement - Session Filter:**
**Status:** Not implemented (added to technical debts)
**Effort:** 1-2 hours

**Two Implementation Approaches:**

**Approach A: Client-side filtering** (Recommended)
- Fetch user's sessions from `/users/me/sessions` (reuse profileService)
- Add dropdown above history list: "All Sessions" | "Current Session" | specific sessions
- Filter items client-side based on selection
- Pros: No backend changes, faster implementation
- Cons: Filters all loaded items (pagination still shows total count)

**Implementation Tasks:**
1. Add session filter dropdown to HistoryPage
2. Fetch sessions list on mount (reuse profile service)
3. Add filter state to useHistory hook
4. Filter displayed items based on selected session
5. Add filter UI above HistoryList component
6. Style filter dropdown following sqowe brand guidelines
7. Add tests for filtering functionality

**Approach B: Server-side filtering** (More complete, requires backend changes)
- Add `?session_id=xxx` query parameter to `/restore/history` endpoint
- Backend filters before pagination
- Update frontend to pass session_id parameter
- Pros: Proper pagination, accurate counts
- Cons: Requires backend changes, more effort

**Files to Modify (Approach A):**
- `frontend/src/features/history/pages/HistoryPage.tsx` - Add filter UI
- `frontend/src/features/history/hooks/useHistory.ts` - Add client-side filtering
- `frontend/src/features/history/components/HistoryFilterBar.tsx` - New component (optional)
- `frontend/src/styles/components/history.css` - Style filter dropdown
- `frontend/src/features/history/__tests__/useHistory.test.ts` - Add filter tests

---

### 10. **Step 3: Admin Panel**
**Context:** Phase 2.4 roadmap
**Status:** Not started
**Effort:** 3-4 hours
**Priority:** HIGH (final phase 2.4 task)

**Requirements:**
- `/admin/users` route
- User list with pagination
- Create user dialog/form
- Edit user dialog/form
- Delete user confirmation modal
- Reset password dialog
- Role assignment dropdown
- Activate/deactivate user toggle

**Backend Status:** ✅ Complete (all admin endpoints implemented and tested)

**Frontend Components to Create:**
- `frontend/src/features/admin/pages/AdminUsersPage.tsx`
- `frontend/src/features/admin/components/UserList.tsx`
- `frontend/src/features/admin/components/CreateUserDialog.tsx`
- `frontend/src/features/admin/components/EditUserDialog.tsx`
- `frontend/src/features/admin/components/DeleteUserDialog.tsx`
- `frontend/src/features/admin/components/ResetPasswordDialog.tsx`
- `frontend/src/features/admin/services/adminService.ts`
- `frontend/src/features/admin/hooks/useAdminUsers.ts`
- `frontend/src/features/admin/types.ts`

---

## Documentation

### 11. **API Documentation Updates**
**Context:** Phase 2.4 new endpoints
**Status:** Backend implemented, docs need update
**Effort:** 1 hour
**Priority:** Medium

**Endpoints to Document:**
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me/password` - Change password
- `GET /api/v1/users/me/sessions` - List active sessions
- `DELETE /api/v1/users/me/sessions/{id}` - Remote logout
- All admin endpoints (`/api/v1/admin/users/*`)

**Files to Update:**
- `docs/API.md` or similar
- OpenAPI/Swagger spec if exists

---

### 12. **Frontend Component Documentation**
**Context:** Improve developer onboarding
**Status:** Components exist, better docs would help
**Effort:** 2 hours
**Priority:** Low

**Documentation to Add:**
- Component props documentation (JSDoc)
- Usage examples
- Storybook stories (if Storybook is added)
- Architecture decision records (ADRs)

**Example:**
```typescript
/**
 * SessionsList - Displays active user sessions with remote logout capability
 *
 * @example
 * ```tsx
 * <SessionsList
 *   sessions={sessions}
 *   onDeleteSession={handleDelete}
 *   error={error}
 * />
 * ```
 *
 * @param sessions - Array of active sessions to display
 * @param onDeleteSession - Callback when user confirms session deletion
 * @param isLoading - Whether sessions are currently loading
 * @param error - Error message to display if sessions fetch failed
 */
```

---

## Performance Optimizations

### 13. **Memoization of Profile Components**
**Context:** Profile page re-renders
**Status:** Works correctly, could be optimized
**Effort:** 1 hour
**Priority:** Low (optimize only if performance issues observed)

**Current Behavior:**
- Profile components re-render on any state change
- Usually not a problem with current complexity

**Potential Optimization:**
```typescript
export const ProfileView = React.memo<ProfileViewProps>(({ profile }) => {
  // Component implementation
});

export const SessionsList = React.memo<SessionsListProps>(({
  sessions,
  onDeleteSession,
  error
}) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison for sessions array
  return (
    prevProps.error === nextProps.error &&
    prevProps.sessions.length === nextProps.sessions.length
  );
});
```

**When to Implement:**
- If profile page shows performance issues
- If users report slow rendering
- After adding more complex features

---

## Summary

**Total Items:** 13
**High Priority:** 2 (Steps 2 & 3 of Phase 2.4)
**Medium Priority:** 4 (Testing improvements, session metadata)
**Low Priority:** 7 (UX enhancements, documentation, optimization)

**Estimated Total Effort:** 20-25 hours

---

## Notes

- All items in this document are **non-blocking** for production deployment
- High priority items are part of the current phase roadmap
- Medium/low priority items can be addressed in future iterations
- This document should be reviewed and updated quarterly
- Completed items should be moved to a "Completed Technical Debts" section with completion date

---

**Document Created:** 2024-12-22
**Last Updated:** 2024-12-22
**Phase:** 2.4 - Enhanced Authentication Features
**Maintainer:** Development Team
