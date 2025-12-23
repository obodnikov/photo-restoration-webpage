# Technical Debts & Future Improvements

This document tracks non-blocking improvements, enhancements, and nice-to-have features that can be implemented in future iterations.

---

## Frontend - Profile Feature

### Testing Improvements (Medium Priority)

#### 1. **Additional Error Handling Tests for useProfile Hook** ✅ **COMPLETE**
**Context:** Phase 2.4 - User Profile Page
**Status:** ✅ **IMPLEMENTED** - Comprehensive error state testing added
**Implementation Date:** 2025-12-23
**Effort:** ~2 hours

**Completed Test Coverage:**
- ✅ Test that `mutationError` is cleared on successful password change
- ✅ Test that `mutationError` is cleared on successful session deletion
- ✅ Test that `mutationError` is set correctly on password change failure
- ✅ Test that `mutationError` is set correctly on session deletion failure
- ✅ Test that errors don't cross-contaminate between operations
- ✅ Test that error states are cleared independently
- ✅ Fixed existing tests to use correct error state properties (`profileError`, `sessionsError`, `mutationError`)

**Implementation Details:**
- Added "Error State Management" test suite with 4 comprehensive test cases
- Fixed existing test failures by updating error property references
- Tests verify proper error isolation between profile, sessions, and mutation operations
- All tests pass and provide confidence in error state management

**File:** `frontend/src/features/profile/__tests__/useProfile.test.ts`

---

#### 2. **SessionsList Error Prop Tests** ✅ **COMPLETE**
**Context:** Phase 2.4 - Senior Developer Review Improvements
**Status:** ✅ **IMPLEMENTED** - Comprehensive error prop testing added
**Implementation Date:** 2025-12-23
**Effort:** ~45 minutes

**Completed Test Coverage:**
- ✅ Test that error message is displayed when `error` prop is provided
- ✅ Test that empty state is NOT shown when `error` prop is provided
- ✅ Test that sessions list is NOT rendered when `error` prop is provided (error takes precedence)
- ✅ Test that error state still shows heading but not session count/full description
- ✅ Test that normal rendering works when error is null/undefined
- ✅ Test that empty state shows when no error and no sessions

**Implementation Details:**
- Added "Error Handling" test suite with 4 comprehensive test cases
- Tests verify proper error display and state management
- Tests ensure error prop prevents misleading empty state messages
- All tests pass and document critical UX behavior

**File:** `frontend/src/features/profile/__tests__/SessionsList.test.tsx`

---

#### 3. **ProfilePage Error Handling Tests** ✅ **COMPLETE**
**Context:** Phase 2.4 - Separated Error States
**Status:** ✅ **ALREADY IMPLEMENTED** - Comprehensive error handling tests existed
**Implementation Date:** Pre-existing (verified 2025-12-23)
**Effort:** Already covered in existing test suite

**Existing Test Coverage:**
- ✅ Test that `profileError` displays full-page error when profile fails to load
- ✅ Test that `mutationError` displays as banner when password change fails
- ✅ Test that `sessionsError` is passed to SessionsList component
- ✅ Test that errors are displayed in correct contexts
- ✅ Test that page renders correctly with various error combinations
- ✅ Test multiple simultaneous errors (profileError + mutationError + sessionsError)

**Implementation Details:**
- Existing ProfilePage.test.tsx already had comprehensive error handling tests
- Tests cover all error display scenarios and integration points
- Verified all test cases were already implemented and passing

**File:** `frontend/src/features/profile/__tests__/ProfilePage.test.tsx`

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

### 7. **Test Failures in Existing Test Suite** ✅ **COMPLETE**
**Context:** Profile feature test suite
**Status:** ✅ **FIXED** - All test failures resolved
**Implementation Date:** 2025-12-23
**Effort:** ~1.5 hours

**Fixed Test Issues:**
- ✅ **Hook initial state timing issues** - Fixed useProfile tests to not check loading states initially
- ✅ **Error property references** - Updated all tests to use correct error state properties (`profileError`, `sessionsError`, `mutationError`)
- ✅ **Modal query issues** - Fixed SessionsList error prop tests to handle modal cleanup properly
- ✅ **Date formatting conflicts** - Resolved by proper test isolation

**Root Causes Addressed:**
1. ✅ **useEffect timing** - Fixed initial state tests to not expect synchronous loading states
2. ✅ **Error state confusion** - Updated all error property references to match actual hook implementation
3. ✅ **Test isolation** - Ensured tests don't interfere with each other (modal cleanup, state resets)

**Files Fixed:**
- `frontend/src/features/profile/__tests__/useProfile.test.ts` - Fixed error properties and initial state expectations
- `frontend/src/features/profile/__tests__/SessionsList.test.tsx` - Fixed error prop test expectations

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
**Status:** ✅ **COMPLETE** (Production-ready, tests recommended)
**Implementation Date:** 2024-12-22
**Approach Used:** Approach A (Client-side filtering)

**Completed Features:**
- ✅ UI text updated to clarify cross-session behavior
- ✅ Backend already returns cross-session history via `/restore/history` endpoint
- ✅ Frontend already uses correct endpoint
- ✅ Session filter dropdown implemented with two options:
  - "All Sessions" (default) - Shows all user images
  - "Current Session Only" - Filters to images from current session
- ✅ Client-side filtering based on current session start time
- ✅ Bulk fetching with pagination loop (handles 10,000+ items)
- ✅ Comprehensive error handling with retry mechanism
- ✅ In-memory pagination for filtered results
- ✅ Automatic page reset when filter changes
- ✅ Page clamping to valid ranges
- ✅ Styled following sqowe brand guidelines
- ✅ Responsive design for mobile/tablet
- ✅ TypeScript compilation successful
- ✅ All code review issues addressed

**Implementation Details:**
- Filter dropdown added to HistoryPage header
- Filtering logic in useHistory hook using session start time from auth storage
- Compares image creation timestamps with current session login time
- Bulk fetching loop fetches all items in batches of 1000
- Robust termination based on batch size (not response.total)
- Error handling with 3-retry mechanism and 1s delays
- In-memory pagination for "Current Session Only" mode (no re-fetching)
- No backend changes required

**Files Modified:**
- `frontend/src/features/history/pages/HistoryPage.tsx` - Added filter UI
- `frontend/src/features/history/hooks/useHistory.ts` - Added filtering logic, bulk fetching, error handling
- `frontend/src/styles/components/history.css` - Added filter styles

**Recommended Addition (Not Blocking):**
- Unit tests for useHistory hook covering:
  - Bulk fetching loop with various batch sizes
  - Error handling and retry mechanism
  - In-memory pagination logic
  - Filter state changes and page resets
  - Edge cases (empty results, partial failures, safety limits)
- See **Item #15** below for test coverage plan

**Note:** Since backend HistoryItemResponse doesn't include session_id per item, the filter uses timestamp comparison with current session start time. For full session-by-session filtering (including past sessions), see **Enhancement Item #14** below.

---

### 14. **Enhanced Session Filter with Historical Session Selection** (Future Enhancement)
**Context:** Extension of Phase 2.4 Step 2
**Status:** Not implemented
**Effort:** 2-3 hours (requires backend changes)
**Priority:** LOW

**Current Implementation:**
- Filter has two options: "All Sessions" and "Current Session Only"
- Works by comparing timestamps with current session start time

**Proposed Enhancement:**
Add ability to filter by any historical session:
- Dropdown shows: "All Sessions" | "Current Session" | individual past sessions
- Requires backend to add `session_id` to `HistoryItemResponse` schema
- OR implement server-side filtering with `?session_id=xxx` query parameter

**Implementation Approach (Backend changes required):**
1. Add `session_id: int` field to `HistoryItemResponse` schema
2. Update `/restore/history` endpoint to include session_id in response
3. Frontend: Fetch user's session list from `/users/me/sessions`
4. Frontend: Show all sessions in dropdown
5. Frontend: Filter items by matching session_id

**Files to Modify:**
- `backend/app/api/v1/schemas/restoration.py` - Add session_id to HistoryItemResponse
- `backend/app/api/v1/routes/restoration.py` - Include session_id in history response
- `frontend/src/features/history/hooks/useHistory.ts` - Fetch sessions list, filter by session_id
- `frontend/src/features/history/pages/HistoryPage.tsx` - Update dropdown options dynamically

**Alternative Approach (Server-side filtering):**
- Add `?session_id=xxx` query parameter to `/restore/history` endpoint
- Backend filters before pagination
- Better performance for users with many images
- Accurate pagination counts per session

---

### 15. **Test Coverage for History Session Filter** ✅ **COMPLETE**
**Context:** Phase 2.4 Step 2 follow-up
**Status:** ✅ **IMPLEMENTED** - Comprehensive test suite created
**Implementation Date:** 2025-12-23
**Effort:** ~3 hours

**Completed Test Coverage:**

**Test File:** `frontend/src/features/history/__tests__/useHistory.test.ts`

**Test Scenarios Implemented:**
1. **Bulk Fetching Logic** ✅
   - ✅ Test fetching single batch (< 1000 items)
   - ✅ Test fetching multiple batches (> 1000 items)
   - ✅ Test termination when batch < limit
   - ✅ Test safety limit (10,000 items)

2. **Error Handling and Retries** ✅
   - ✅ Test single fetch failure with successful retry
   - ✅ Test consecutive failures (3 errors → stop)
   - ✅ Test error message display
   - ✅ Test graceful degradation (show partial data)

3. **In-Memory Pagination** ✅
   - ✅ Test pagination of filtered results
   - ✅ Test page changes without re-fetching
   - ✅ Test page clamping to valid ranges

4. **Filter State Management** ✅
   - ✅ Test switching from "All" to "Current Session Only"
   - ✅ Test page reset when filter changes
   - ✅ Test filter with no session start time (error case)
   - ✅ Test filter with invalid dates

5. **Edge Cases** ✅
   - ✅ Empty history
   - ✅ No items match current session filter
   - ✅ Invalid session start time in localStorage
   - ✅ Network failures during bulk fetch
   - ✅ Items with missing/invalid created_at dates

**Testing Approach Used:**
- ✅ `@testing-library/react-hooks` for hook testing
- ✅ Mock `fetchHistory` to simulate various responses
- ✅ Mock `localStorage` for session start time tests
- ✅ Test state updates and side effects
- ✅ 15 comprehensive test cases covering all scenarios

**Benefits Achieved:**
- ✅ Prevent regressions when refactoring
- ✅ Document expected behavior
- ✅ Catch edge cases in CI/CD pipeline
- ✅ Increase confidence for production deployment

---

### 10. **Step 3: Admin Panel**
**Context:** Phase 2.4 roadmap
**Status:** ✅ **COMPLETE** (Production-ready, tests recommended)
**Implementation Date:** 2025-12-22
**Effort:** ~3 hours

**Completed Features:**
- ✅ `/admin/users` route with AdminRoute wrapper (role-based access control)
- ✅ User list with pagination (20 users per page)
- ✅ Filters: Role (All/Admin/User) and Status (All/Active/Inactive)
- ✅ Create user dialog with password generation button
- ✅ Edit user dialog (email, full_name, role, is_active)
- ✅ Delete user confirmation modal with cascade warning
- ✅ Reset password dialog with password generation
- ✅ Role assignment dropdown in create/edit dialogs
- ✅ Activate/deactivate user toggle in edit dialog
- ✅ Admin navigation link (only visible to admins)
- ✅ Responsive design for mobile/tablet
- ✅ sqowe brand styling throughout
- ✅ TypeScript compilation successful
- ✅ Prevents admin from deleting self

**Implementation Details:**
- AdminRoute component checks user.role === 'admin' and redirects non-admins
- User interface updated to include role field
- JWT token decoder extracts role from access token
- All CRUD operations implemented with proper error handling
- Password generation creates secure 12-character passwords
- Table highlights current user with "(You)" badge
- Separate buttons for Edit/Reset Password/Delete actions
- Client-side pagination for large user lists

**Files Created:**
- `frontend/src/features/admin/types.ts`
- `frontend/src/features/admin/services/adminService.ts`
- `frontend/src/features/admin/hooks/useAdminUsers.ts`
- `frontend/src/features/admin/components/UserList.tsx`
- `frontend/src/features/admin/components/CreateUserDialog.tsx`
- `frontend/src/features/admin/components/EditUserDialog.tsx`
- `frontend/src/features/admin/components/DeleteUserDialog.tsx`
- `frontend/src/features/admin/components/ResetPasswordDialog.tsx`
- `frontend/src/features/admin/pages/AdminUsersPage.tsx`
- `frontend/src/components/AdminRoute.tsx`
- `frontend/src/styles/components/admin.css`

**Files Modified:**
- `frontend/src/features/auth/types.ts` - Added role to User interface
- `frontend/src/features/auth/hooks/useAuth.ts` - Added JWT token decoder
- `frontend/src/components/Button.tsx` - Added danger variant
- `frontend/src/components/Layout.tsx` - Added Admin nav link (admin-only)
- `frontend/src/app/App.tsx` - Added /admin/users route

**Backend Status:** ✅ Complete (all admin endpoints working)

**Code Review Fixes Applied (2025-12-22):**
- ✅ **[HIGH]** Fixed insecure password generation - Replaced Math.random() with crypto.getRandomValues()
- ✅ **[MEDIUM]** Fixed pagination bug after deletion - Now handles invalid page states correctly
- ✅ **[LOW]** Fixed sensitive data leak - Form state cleared on dialog close
- ✅ **Type Safety** - Replaced `any` types with proper interfaces (CreateUserRequest, UpdateUserRequest, ResetPasswordRequest)

**Recommended Additions (Non-Blocking):**
- Unit tests for admin components (See Item #17 below)
- Server-side search for large user bases (See Item #18 below)

---

### 17. **Test Coverage for Admin Panel** (Recommended, Not Blocking)
**Context:** Phase 2.4 Step 3 follow-up
**Status:** Not implemented
**Effort:** 3-4 hours
**Priority:** MEDIUM

**Current State:**
- Admin panel is functionally complete and production-ready
- Build successful with no TypeScript errors
- Comprehensive error handling in place
- No automated tests for admin features

**Recommended Test Coverage:**

**Test File:** `frontend/src/features/admin/__tests__/useAdminUsers.test.ts`

**Test Scenarios:**
1. **User List Fetching**
   - Test fetching users with pagination
   - Test applying role filter
   - Test applying status filter
   - Test error handling

2. **CRUD Operations**
   - Test creating user successfully
   - Test creating user with duplicate username/email
   - Test updating user
   - Test deleting user
   - Test reset password

3. **Pagination**
   - Test page changes
   - Test filter changes reset page to 1
   - Test total pages calculation

**Component Tests:**
- `UserList.test.tsx` - Table rendering, filters, pagination
- `CreateUserDialog.test.tsx` - Form validation, password generation
- `EditUserDialog.test.tsx` - Form updates, change detection
- `DeleteUserDialog.test.tsx` - Confirmation flow
- `ResetPasswordDialog.test.tsx` - Password generation, form submission

**Benefits:**
- Prevent regressions when refactoring
- Document expected behavior
- Catch edge cases in CI/CD pipeline
- Increase confidence for production deployment

**Not Blocking Because:**
- Feature is functionally complete and tested manually
- Build successful with no errors
- Comprehensive error handling already in place
- Can be added incrementally as part of test coverage improvements

---

### 18. **Server-Side Search for Admin Panel** (Future Enhancement)
**Context:** Phase 2.4 Step 3 enhancement
**Status:** Not implemented
**Effort:** 1-2 hours (requires backend changes)
**Priority:** LOW

**Current Implementation:**
- No search functionality (per user decision during implementation)
- Admins can use browser search (Ctrl+F) on current page
- Filters available: Role and Status

**Proposed Enhancement:**
Add server-side search capability for large user bases:
- Search by username, email, or full name
- Backend adds `?search=query` parameter to GET /admin/users
- Backend SQL: `WHERE username LIKE '%query%' OR email LIKE '%query%' OR full_name LIKE '%query%'`
- Frontend adds search input field above filters
- Debounced search to reduce API calls

**Implementation Approach:**
1. Backend: Add `search` query parameter to `/admin/users` endpoint
2. Backend: Update SQL query to include LIKE clauses
3. Frontend: Add search input to UserList component
4. Frontend: Debounce search input (500ms delay)
5. Frontend: Reset pagination when search changes

**Files to Modify:**
- `backend/app/api/v1/routes/admin.py` - Add search parameter
- `frontend/src/features/admin/components/UserList.tsx` - Add search UI
- `frontend/src/features/admin/hooks/useAdminUsers.ts` - Add search state
- `frontend/src/features/admin/services/adminService.ts` - Add search to getUsers

**When to Implement:**
- When user base grows beyond 100-200 users
- When admins request search functionality
- When pagination becomes cumbersome

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

**Total Items:** 18
**High Priority:** 0 (All Phase 2.4 tasks complete!)
**Medium Priority:** 3 (Session metadata, test coverage for admin panel)
**Low Priority:** 11 (UX enhancements, documentation, optimization, enhanced session filter, server-side search)

**✅ Phase 2.4 Complete - All 3 Steps Finished:**
- ✅ Step 1: User Profile Page (Complete, production-ready)
- ✅ Step 2: Updated History Component (Complete, production-ready, tests recommended)
- ✅ Step 3: Admin Panel (Complete, production-ready, tests recommended)

**✅ Test Coverage Improvements Complete:**
- ✅ Item #1: Additional Error Handling Tests for useProfile Hook (2 hours)
- ✅ Item #2: SessionsList Error Prop Tests (45 minutes)
- ✅ Item #3: ProfilePage Error Handling Tests (Already existed)
- ✅ Item #7: Test Failures in Existing Test Suite (1.5 hours)
- ✅ Item #15: Test Coverage for History Session Filter (3 hours)

**Recommended Additions (Non-Blocking):**
- Test coverage for admin panel (MEDIUM priority, 3-4 hours) - See Item #17
- Server-side search for admin panel (LOW priority, 1-2 hours) - See Item #18

**Estimated Total Effort for Remaining Items:** 25-31 hours

---

## Notes

- All items in this document are **non-blocking** for production deployment
- High priority items are part of the current phase roadmap
- Medium/low priority items can be addressed in future iterations
- This document should be reviewed and updated quarterly
- Completed items should be moved to a "Completed Technical Debts" section with completion date

---

**Document Created:** 2024-12-22
**Last Updated:** 2025-12-23
**Phase:** 2.4 - Enhanced Authentication Features ✅ COMPLETE
**Test Coverage Improvements:** ✅ COMPLETE (5/5 critical items implemented)
**Maintainer:** Development Team

## Frontend - Force Password Change Feature

### 19. **Test Coverage for ForcePasswordChangePage Component**
**Context:** Phase 2.4 - Forced Password Change Implementation
**Status:** Feature complete, tests recommended
**Effort:** ~2 hours
**Priority:** LOW

**Missing Test Coverage:**
- Form rendering and field presence
- Password validation rules (length, uppercase, lowercase, digit)
- Password mismatch validation
- Same-as-current password validation
- Successful submission flow and redirect to login
- API error handling
- Loading state management
- Logout button functionality

**Rationale:**
The ForcePasswordChangePage is a security-critical component that forces users to change passwords on first login. Comprehensive tests would ensure robustness.

**File:** `frontend/src/features/auth/__tests__/ForcePasswordChangePage.test.tsx` (to be created)

---

### 20. **Test Coverage for RequirePasswordChangeRoute Component**
**Context:** Phase 2.4 - Forced Password Change Implementation
**Status:** Feature complete, tests recommended
**Effort:** ~30 minutes
**Priority:** LOW

**Missing Test Coverage:**
- Authenticated user with password_must_change=true can access
- Authenticated user with password_must_change=false redirects to home
- Unauthenticated user redirects to login
- Component renders children when conditions are met

**Rationale:**
Route guard logic should be tested to prevent regressions in access control.

**File:** `frontend/src/features/auth/__tests__/RequirePasswordChangeRoute.test.tsx` (to be created)

---

### 21. **Test Coverage for Updated useAuth Hook**
**Context:** Phase 2.4 - Forced Password Change Implementation
**Status:** Feature complete, tests recommended
**Effort:** ~1 hour
**Priority:** LOW

**Missing Test Coverage:**
- JWT token decoding with password_must_change field
- JWT token decoding without password_must_change field (defaults to false)
- Warning log when password_must_change is missing
- Login redirect to /change-password when flag is true
- Login redirect to / when flag is false
- Token decode error handling

**Rationale:**
The updated decodeToken function includes critical security logic that should be thoroughly tested.

**File:** `frontend/src/features/auth/__tests__/useAuth.test.ts` (to be updated)

---
