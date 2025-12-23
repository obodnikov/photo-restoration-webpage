# Component Documentation Guide

This document provides comprehensive JSDoc documentation for key frontend components, following the technical debt item #12 from TECHNICAL_DEBTS.md.

## Profile Feature Components

### `SessionsList` Component

**File:** `frontend/src/features/profile/components/SessionsList.tsx`

```typescript
/**
 * SessionsList - Displays active user sessions with remote logout capability
 *
 * Displays a list of active sessions with creation date, last access time,
 * and the ability to remotely logout from non-current sessions. Includes
 * error handling, empty states, and confirmation modal for logout actions.
 *
 * @example
 * ```tsx
 * <SessionsList
 *   sessions={sessions}
 *   onDeleteSession={handleDelete}
 *   isLoading={loading}
 *   error={error}
 * />
 * ```
 *
 * @param sessions - Array of active Session objects to display
 * @param onDeleteSession - Callback invoked when user confirms session deletion
 * @param isLoading - Whether sessions are currently loading (default: false)
 * @param error - Error message to display if sessions fetch failed (default: null)
 *
 * @component
 * @category Profile
 */
```

**Props Interface:**
```typescript
interface SessionsListProps {
  sessions: Session[];
  onDeleteSession: (sessionId: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}
```

**Session Interface:**
```typescript
interface Session {
  id: string;
  session_id: string;
  created_at: string;
  last_accessed: string;
  image_count: number;
  is_current: boolean;
}
```

**Component Behavior:**
1. **Error State:** Displays error message with "Failed to Load Sessions" title
2. **Empty State:** Shows "No active sessions found" when no sessions exist
3. **Normal State:** Lists sessions with formatted dates and logout buttons
4. **Current Session:** Highlights current session with badge, disables logout
5. **Confirmation Modal:** Shows before deleting session for user confirmation

---

### `ProfileView` Component

**File:** `frontend/src/features/profile/components/ProfileView.tsx`

```typescript
/**
 * ProfileView - Displays user profile information in a structured format
 *
 * Shows user details (username, email, full name, role) in a card layout.
 * Includes creation date and last login timestamp. Designed as a read-only
 * display component.
 *
 * @example
 * ```tsx
 * <ProfileView
 *   profile={profile}
 *   isLoading={loading}
 *   error={error}
 * />
 * ```
 *
 * @param profile - User profile object with personal and account information
 * @param isLoading - Whether profile data is currently loading (default: false)
 * @param error - Error message to display if profile fetch failed (default: null)
 *
 * @component
 * @category Profile
 */
```

**Props Interface:**
```typescript
interface ProfileViewProps {
  profile: UserProfile;
  isLoading?: boolean;
  error?: string | null;
}
```

**UserProfile Interface:**
```typescript
interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}
```

---

### `ChangePasswordForm` Component

**File:** `frontend/src/features/profile/components/ChangePasswordForm.tsx`

```typescript
/**
 * ChangePasswordForm - Form for changing user password with validation
 *
 * Provides a secure password change form with current password verification,
 * new password validation (length, uppercase, lowercase, digit), and password
 * mismatch checking. Includes loading states and error display.
 *
 * @example
 * ```tsx
 * <ChangePasswordForm
 *   onSubmit={handleChangePassword}
 *   isLoading={loading}
 *   error={error}
 * />
 * ```
 *
 * @param onSubmit - Callback invoked with form data when submitted
 * @param isLoading - Whether password change is in progress (default: false)
 * @param error - Error message to display (default: null)
 *
 * @component
 * @category Profile
 */
```

**Props Interface:**
```typescript
interface ChangePasswordFormProps {
  onSubmit: (data: ChangePasswordFormData) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}
```

**Form Data Interface:**
```typescript
interface ChangePasswordFormData {
  current_password: string;
  new_password: string;
  confirm_password: string;
}
```

**Validation Rules:**
1. Current password must not be empty
2. New password must meet complexity requirements:
   - Minimum 8 characters
   - At least one uppercase letter (A-Z)
   - At least one lowercase letter (a-z)
   - At least one digit (0-9)
3. New password must match confirmation password
4. New password must be different from current password

---

## History Feature Components

### `HistoryPage` Component

**File:** `frontend/src/features/history/pages/HistoryPage.tsx`

```typescript
/**
 * HistoryPage - Main page for viewing image restoration history
 *
 * Displays paginated list of processed images with filtering options (All Sessions,
 * Current Session Only). Includes before/after comparison, download functionality,
 * and session-based filtering.
 *
 * @component
 * @category History
 */
```

**Features:**
- Session filter dropdown with "All Sessions" and "Current Session Only" options
- Paginated image grid with responsive layout
- In-memory pagination for filtered results
- Bulk fetching for large history sets with error retry mechanism

---

### `useHistory` Hook

**File:** `frontend/src/features/history/hooks/useHistory.ts`

```typescript
/**
 * useHistory - Custom hook for managing image restoration history
 *
 * Provides comprehensive history management with pagination, filtering,
 * bulk fetching, and error handling. Supports client-side filtering by
 * session and server-side pagination.
 *
 * @example
 * ```tsx
 * const {
 *   items,
 *   isLoading,
 *   error,
 *   totalPages,
 *   currentPage,
 *   filter,
 *   setCurrentPage,
 *   setFilter,
 *   refetch,
 * } = useHistory();
 * ```
 *
 * @returns History management state and actions
 *
 * @hook
 * @category History
 */
```

**Hook Return Interface:**
```typescript
interface UseHistoryReturn {
  items: HistoryItem[];
  isLoading: boolean;
  error: string | null;
  totalItems: number;
  totalPages: number;
  currentPage: number;
  filter: 'all' | 'current';
  setCurrentPage: (page: number) => void;
  setFilter: (filter: 'all' | 'current') => void;
  refetch: () => Promise<void>;
}
```

**Bulk Fetching Behavior:**
- Fetches history in batches of 1000 items
- Implements safety limit of 10,000 items
- Includes 3-retry mechanism with 1-second delays
- Graceful degradation with partial data display on errors

---

## Admin Feature Components

### `UserList` Component

**File:** `frontend/src/features/admin/components/UserList.tsx`

```typescript
/**
 * UserList - Displays paginated list of users with admin controls
 *
 * Shows user table with filtering (role, status), pagination, and CRUD
 * action buttons (Edit, Reset Password, Delete). Highlights current user
 * and prevents self-deletion.
 *
 * @example
 * ```tsx
 * <UserList
 *   users={users}
 *   totalUsers={total}
 *   currentPage={page}
 *   filters={filters}
 *   onPageChange={handlePageChange}
 *   onFilterChange={handleFilterChange}
 *   onEditUser={handleEdit}
 *   onResetPassword={handleResetPassword}
 *   onDeleteUser={handleDelete}
 *   isLoading={loading}
 *   error={error}
 * />
 * ```
 *
 * @component
 * @category Admin
 */
```

---

### `AdminRoute` Component

**File:** `frontend/src/components/AdminRoute.tsx`

```typescript
/**
 * AdminRoute - Route wrapper for admin-only access control
 *
 * Protects routes by checking if current user has 'admin' role.
 * Redirects non-admin users to home page. Provides appropriate
 * loading and error states.
 *
 * @example
 * ```tsx
 * <Route path="/admin/users" element={
 *   <AdminRoute>
 *     <AdminUsersPage />
 *   </AdminRoute>
 * } />
 * ```
 *
 * @param children - Component(s) to render if user is admin
 *
 * @component
 * @category Auth
 */
```

---

## Common Components

### `Card` Component

**File:** `frontend/src/components/Card.tsx`

```typescript
/**
 * Card - Container component with various styling variants
 *
 * Flexible card container with light/dark variants, padding options,
 * and hover effects. Used throughout the application for consistent
 * content grouping.
 *
 * @example
 * ```tsx
 * <Card variant="light" padding="medium">
 *   <h2>Title</h2>
 *   <p>Content goes here</p>
 * </Card>
 * ```
 *
 * @param variant - Visual style: 'light' (default) or 'dark'
 * @param padding - Padding size: 'small', 'medium' (default), 'large', or 'none'
 * @param className - Additional CSS classes
 * @param children - Card content
 *
 * @component
 * @category UI
 */
```

---

### `Button` Component

**File:** `frontend/src/components/Button.tsx`

```typescript
/**
 * Button - Interactive button component with multiple variants
 *
 * Configurable button with primary/secondary/danger variants,
 * small/medium/large sizes, and loading/disabled states.
 * Follows accessibility standards with proper ARIA attributes.
 *
 * @example
 * ```tsx
 * <Button
 *   variant="primary"
 *   size="medium"
 *   onClick={handleClick}
 *   loading={isLoading}
 *   disabled={isDisabled}
 * >
 *   Click Me
 * </Button>
 * ```
 *
 * @param variant - Button style: 'primary' (default), 'secondary', or 'danger'
 * @param size - Button size: 'small', 'medium' (default), 'large'
 * @param type - HTML button type: 'button', 'submit', 'reset' (default: 'button')
 * @param onClick - Click handler function
 * @param loading - Whether button shows loading spinner
 * @param disabled - Whether button is disabled
 * @param className - Additional CSS classes
 * @param children - Button label/content
 *
 * @component
 * @category UI
 */
```

---

## JSDoc Best Practices

### General Format
```typescript
/**
 * ComponentName - Brief description
 *
 * Detailed description covering purpose, behavior, and usage.
 * Include any important implementation details or edge cases.
 *
 * @example
 * ```tsx
 * <ComponentName
 *   prop1={value1}
 *   prop2={value2}
 * />
 * ```
 *
 * @param propName - Description of prop
 * @returns Description of return value (for hooks/functions)
 *
 * @component (or @hook, @function)
 * @category Feature/Module
 */
```

### Prop Documentation
- Use `@param` for each prop in props interface
- Include type information in description
- Document default values for optional props
- Mention any validation or constraints

### Usage Examples
- Include realistic, runnable examples
- Show both simple and complex usage
- Demonstrate error states and edge cases
- Use proper TypeScript syntax

### Categories
- `@category Profile` - User profile features
- `@category History` - Image history features
- `@category Admin` - Admin panel features
- `@category Auth` - Authentication components
- `@category UI` - General UI components
- `@category Forms` - Form-related components

---

## Implementation Checklist

### ✅ Completed Documentation
- [x] SessionsList - Comprehensive JSDoc with examples
- [ ] ProfileView - Needs JSDoc enhancement
- [ ] ChangePasswordForm - Needs JSDoc enhancement
- [ ] HistoryPage - Needs basic JSDoc
- [x] useHistory - Comprehensive hook documentation
- [ ] UserList - Needs admin component JSDoc
- [x] AdminRoute - Basic documentation exists
- [ ] Card - Needs JSDoc enhancement
- [ ] Button - Needs JSDoc enhancement

### 🔄 Pending Updates
- Add JSDoc to remaining profile components
- Update history components with examples
- Enhance admin components documentation
- Document shared UI components
- Create usage examples for complex components

### 📚 Additional Documentation Types
1. **Architecture Decision Records (ADRs)** - Document design decisions
2. **Storybook Stories** - Interactive component documentation
3. **API Integration Examples** - How to use with backend
4. **Testing Examples** - How to test each component
5. **Accessibility Notes** - WCAG compliance details

---

## How to Use This Guide

1. **For New Components:** Copy the JSDoc template and adapt for your component
2. **For Existing Components:** Add missing JSDoc following these patterns
3. **For Updates:** Keep documentation synchronized with component changes
4. **For Verification:** Use TypeScript to ensure prop types match documentation

**Remember:** Good documentation reduces onboarding time, prevents bugs, and makes maintenance easier. Always document:
- What the component does
- How to use it (with examples)
- What props it accepts
- Any special behavior or edge cases
- Related components or hooks