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
   * Login with username and password
   */
  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await loginApi(credentials);

      // Store auth state
      setAuth(response.access_token, response.expires_in, {
        username: credentials.username,
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
