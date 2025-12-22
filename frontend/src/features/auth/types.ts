/**
 * Authentication-related TypeScript types and interfaces.
 */

/**
 * Login credentials for authentication
 */
export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe: boolean;
}

/**
 * Token response from login API
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * User information
 */
export interface User {
  username: string;
  role: 'admin' | 'user';
}

/**
 * Authentication state
 */
export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  expiresAt: number | null;
}

/**
 * Token validation response
 */
export interface TokenValidateResponse {
  valid: boolean;
  username?: string;
}
