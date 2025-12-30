/**
 * useAuth hook tests
 * Tests the authentication hook including JWT decoding and login flow
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { login as loginApi } from '../services/authService';
import { useAuthStore } from '../../../services/authStore';
import type { LoginCredentials } from '../types';

// Mock dependencies
vi.mock('../services/authService', () => ({
  login: vi.fn(),
}));

vi.mock('../../../services/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

/**
 * Helper function to create a test JWT token
 */
function createTestToken(payload: {
  sub: string;
  role?: 'admin' | 'user';
  password_must_change?: boolean;
}): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const headerBase64 = btoa(JSON.stringify(header));
  const payloadBase64 = btoa(JSON.stringify(payload));
  return `${headerBase64}.${payloadBase64}.fake-signature`;
}

// Wrapper for hooks that need router context
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('useAuth', () => {
  const mockSetAuth = vi.fn();
  const mockClearAuth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock for useAuthStore
    vi.mocked(useAuthStore).mockImplementation((selector: any) => {
      const state = {
        isAuthenticated: false,
        user: null,
        setAuth: mockSetAuth,
        clearAuth: mockClearAuth,
      };
      return selector ? selector(state) : state;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Token Decoding', () => {
    it('decodes token with password_must_change=true correctly', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: true,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(token, 3600, {
          username: 'testuser',
          role: 'user',
          password_must_change: true,
        });
      });
    });

    it('decodes token with password_must_change=false correctly', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: false,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(token, 3600, {
          username: 'testuser',
          role: 'user',
          password_must_change: false,
        });
      });
    });

    it('defaults password_must_change to false when field is missing', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        // password_must_change is omitted
      });

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(token, 3600, {
          username: 'testuser',
          role: 'user',
          password_must_change: false,
        });
      });

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('JWT token missing password_must_change field')
      );

      consoleWarnSpy.mockRestore();
    });

    it('handles malformed token gracefully', async () => {
      const malformedToken = 'not.a.valid.jwt.token';

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: malformedToken,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(malformedToken, 3600, {
          username: '',
          role: 'user',
          password_must_change: false,
        });
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to decode token:',
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    });

    it('extracts role field correctly for admin', async () => {
      const token = createTestToken({
        sub: 'adminuser',
        role: 'admin',
        password_must_change: false,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'adminuser',
        password: 'adminpass',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(token, 3600, {
          username: 'adminuser',
          role: 'admin',
          password_must_change: false,
        });
      });
    });

    it('extracts username from sub field correctly', async () => {
      const token = createTestToken({
        sub: 'john.doe',
        role: 'user',
        password_must_change: false,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'john.doe',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(
          token,
          3600,
          expect.objectContaining({
            username: 'john.doe',
          })
        );
      });
    });
  });

  describe('Login Flow', () => {
    it('navigates to /change-password when password_must_change is true', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: true,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/change-password');
      });
    });

    it('navigates to / when password_must_change is false', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: false,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('stores auth state correctly on successful login', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: false,
      });

      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 7200,
      });

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(mockSetAuth).toHaveBeenCalledWith(token, 7200, {
          username: 'testuser',
          role: 'user',
          password_must_change: false,
        });
      });
    });

    it('sets error state and re-throws on login failure', async () => {
      const errorMessage = 'Invalid credentials';
      vi.mocked(loginApi).mockRejectedValueOnce(new Error(errorMessage));

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'wrongpassword',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(result.current.login(credentials)).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe(errorMessage);
      });

      expect(mockSetAuth).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Logout', () => {
    it('clears auth state on logout', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      result.current.logout();

      expect(mockClearAuth).toHaveBeenCalled();
    });

    it('navigates to /login on logout', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      result.current.logout();

      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('Loading and Error States', () => {
    it('sets loading state during login', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: false,
      });

      vi.mocked(loginApi).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          access_token: token,
          token_type: 'bearer',
          expires_in: 3600,
        }), 100))
      );

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(false);

      result.current.login(credentials);

      // Should be loading immediately after calling login
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      // Should not be loading after login completes
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('clears error state on successful login', async () => {
      const token = createTestToken({
        sub: 'testuser',
        role: 'user',
        password_must_change: false,
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      // First, set an error by failing a login
      vi.mocked(loginApi).mockRejectedValueOnce(new Error('First error'));

      const credentials: LoginCredentials = {
        username: 'testuser',
        password: 'password123',
      };

      await expect(result.current.login(credentials)).rejects.toThrow();

      await waitFor(() => {
        expect(result.current.error).toBe('First error');
      });

      // Now login successfully
      vi.mocked(loginApi).mockResolvedValueOnce({
        access_token: token,
        token_type: 'bearer',
        expires_in: 3600,
      });

      await result.current.login(credentials);

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });
  });
});
