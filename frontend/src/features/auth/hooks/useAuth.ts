/**
 * Authentication hook for React components.
 *
 * This hook provides authentication functionality:
 * - Login/logout actions
 * - Authentication state
 * - Loading and error states
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../../services/authStore';
import { login as loginApi } from '../services/authService';
import type { LoginCredentials } from '../types';

/**
 * Authentication hook
 */
export function useAuth() {
  const navigate = useNavigate();
  const { isAuthenticated, user, setAuth, clearAuth } = useAuthStore();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Decode JWT token payload
   */
  const decodeToken = (token: string): { sub: string; role: 'admin' | 'user' } => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Failed to decode token:', error);
      // Fallback to default if decode fails
      return { sub: '', role: 'user' };
    }
  };

  /**
   * Login with username and password
   */
  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await loginApi(credentials);

      // Decode token to extract user information
      const payload = decodeToken(response.access_token);

      // Store auth state
      setAuth(response.access_token, response.expires_in, {
        username: payload.sub,
        role: payload.role,
      });

      // Navigate to home page
      navigate('/');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout
   */
  const logout = () => {
    clearAuth();
    navigate('/login');
  };

  return {
    // State
    isAuthenticated,
    user,
    isLoading,
    error,

    // Actions
    login,
    logout,
  };
}
