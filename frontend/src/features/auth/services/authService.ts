/**
 * Authentication API service.
 *
 * This service handles all authentication-related API calls.
 */

import { config } from '../../../config/config';
import type { LoginCredentials, TokenResponse, TokenValidateResponse, User } from '../types';

/**
 * Login with username and password
 */
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await fetch(`${config.apiBaseUrl}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
      remember_me: credentials.rememberMe,
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Invalid credentials');
    }
    throw new Error('Login failed. Please try again.');
  }

  return response.json();
}

/**
 * Validate JWT token
 */
export async function validateToken(token: string): Promise<TokenValidateResponse> {
  const response = await fetch(`${config.apiBaseUrl}/auth/validate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return { valid: false };
  }

  return response.json();
}

/**
 * Get current user information
 */
export async function getCurrentUser(token: string): Promise<User> {
  const response = await fetch(`${config.apiBaseUrl}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get user information');
  }

  return response.json();
}
