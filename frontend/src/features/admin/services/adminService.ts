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
 * Generate a cryptographically secure random password
 * Uses window.crypto.getRandomValues() for secure randomness
 */
export function generateRandomPassword(length: number = 12): string {
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const numbers = '0123456789';
  const special = '!@#$%^&*';
  const allChars = uppercase + lowercase + numbers + special;

  /**
   * Get a cryptographically secure random integer between 0 and max-1
   */
  const getSecureRandomInt = (max: number): number => {
    const randomBuffer = new Uint32Array(1);
    crypto.getRandomValues(randomBuffer);
    return randomBuffer[0] % max;
  };

  /**
   * Get a random character from a character set
   */
  const getRandomChar = (charset: string): string => {
    return charset[getSecureRandomInt(charset.length)];
  };

  // Ensure at least one of each required character type
  const password: string[] = [
    getRandomChar(uppercase),
    getRandomChar(lowercase),
    getRandomChar(numbers),
  ];

  // Fill the rest randomly from all characters
  for (let i = password.length; i < length; i++) {
    password.push(getRandomChar(allChars));
  }

  // Shuffle the password array using Fisher-Yates algorithm with crypto.getRandomValues
  for (let i = password.length - 1; i > 0; i--) {
    const j = getSecureRandomInt(i + 1);
    [password[i], password[j]] = [password[j], password[i]];
  }

  return password.join('');
}
