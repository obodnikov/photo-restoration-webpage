/**
 * Admin feature types
 */

/**
 * User from admin API
 */
export interface AdminUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

/**
 * Create user request
 */
export interface CreateUserRequest {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role: 'admin' | 'user';
  password_must_change: boolean;
}

/**
 * Update user request
 */
export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  role?: 'admin' | 'user';
  is_active?: boolean;
}

/**
 * Reset password request
 */
export interface ResetPasswordRequest {
  new_password: string;
  password_must_change: boolean;
}

/**
 * User list response
 */
export interface UserListResponse {
  users: AdminUser[];
  total: number;
}

/**
 * User list filters
 */
export interface UserListFilters {
  role?: 'admin' | 'user' | null;
  is_active?: boolean | null;
}
