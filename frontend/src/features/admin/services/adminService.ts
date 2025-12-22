/**
 * Admin API service for user management
 */

import * as api from '../../../services/apiClient';
import type {
  AdminUser,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
  UserListResponse,
  UserListFilters,
} from '../types';

/**
 * Get list of users with pagination and filters
 */
export async function getUsers(
  skip: number = 0,
  limit: number = 20,
  filters?: UserListFilters
): Promise<UserListResponse> {
  let url = `/admin/users?skip=${skip}&limit=${limit}`;

  if (filters?.role) {
    url += `&role=${filters.role}`;
  }

  if (filters?.is_active !== null && filters?.is_active !== undefined) {
    url += `&is_active=${filters.is_active}`;
  }

  return api.get<UserListResponse>(url);
}

/**
 * Get user by ID
 */
export async function getUser(userId: number): Promise<AdminUser> {
  return api.get<AdminUser>(`/admin/users/${userId}`);
}

/**
 * Create new user
 */
export async function createUser(userData: CreateUserRequest): Promise<AdminUser> {
  return api.post<AdminUser>('/admin/users', userData);
}

/**
 * Update user
 */
export async function updateUser(
  userId: number,
  userData: UpdateUserRequest
): Promise<AdminUser> {
  return api.put<AdminUser>(`/admin/users/${userId}`, userData);
}

/**
 * Delete user
 */
export async function deleteUser(userId: number): Promise<void> {
  return api.del<void>(`/admin/users/${userId}`);
}

/**
 * Reset user password
 */
export async function resetUserPassword(
  userId: number,
  passwordData: ResetPasswordRequest
): Promise<AdminUser> {
  return api.put<AdminUser>(
    `/admin/users/${userId}/reset-password`,
    passwordData
  );
}

/**
 * Generate a random secure password
 */
export function generateRandomPassword(length: number = 12): string {
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const numbers = '0123456789';
  const special = '!@#$%^&*';
  const allChars = uppercase + lowercase + numbers + special;

  let password = '';

  // Ensure at least one of each required character type
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];

  // Fill the rest randomly
  for (let i = password.length; i < length; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)];
  }

  // Shuffle the password
  return password
    .split('')
    .sort(() => Math.random() - 0.5)
    .join('');
}
