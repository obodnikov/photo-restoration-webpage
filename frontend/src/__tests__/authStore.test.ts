/**
 * Tests for authentication store (Zustand)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore, initializeAuthStore, setupTokenExpiryCheck } from '../services/authStore';
import { mockUser, mockToken } from '../test-utils';

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.getState().clearAuth();
    localStorage.clear();
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  describe('setAuth', () => {
    it('should update state when setting auth', () => {
      const store = useAuthStore.getState();
      const expiresIn = 86400; // 24 hours

      store.setAuth(mockToken, expiresIn, mockUser);

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(mockToken);
      expect(state.user).toEqual(mockUser);
      expect(state.expiresAt).toBeGreaterThan(Date.now());
    });

    it('should store token in localStorage', () => {
      const store = useAuthStore.getState();
      const expiresIn = 86400;

      store.setAuth(mockToken, expiresIn, mockUser);

      expect(localStorage.getItem('photo_restoration_token')).toBe(mockToken);
      expect(localStorage.getItem('photo_restoration_user')).toBe(
        JSON.stringify(mockUser)
      );
      expect(localStorage.getItem('photo_restoration_token_expiry')).toBeTruthy();
    });

    it('should calculate correct expiration time', () => {
      const store = useAuthStore.getState();
      const expiresIn = 3600; // 1 hour
      const beforeTime = Date.now();

      store.setAuth(mockToken, expiresIn, mockUser);

      const state = useAuthStore.getState();
      const afterTime = Date.now();
      const expectedExpiry = beforeTime + expiresIn * 1000;

      expect(state.expiresAt).toBeGreaterThanOrEqual(expectedExpiry);
      expect(state.expiresAt).toBeLessThanOrEqual(afterTime + expiresIn * 1000);
    });
  });

  describe('clearAuth', () => {
    it('should clear auth state', () => {
      const store = useAuthStore.getState();

      // First set auth
      store.setAuth(mockToken, 86400, mockUser);

      // Get fresh state after setAuth
      let state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);

      // Then clear it
      store.clearAuth();

      // Get fresh state after clearAuth
      state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.expiresAt).toBe(null);
    });

    it('should remove token from localStorage', () => {
      const store = useAuthStore.getState();

      // Set auth first
      store.setAuth(mockToken, 86400, mockUser);
      expect(localStorage.getItem('photo_restoration_token')).toBeTruthy();

      // Clear auth
      store.clearAuth();

      expect(localStorage.getItem('photo_restoration_token')).toBe(null);
      expect(localStorage.getItem('photo_restoration_user')).toBe(null);
      expect(localStorage.getItem('photo_restoration_token_expiry')).toBe(null);
    });
  });

  describe('Token persistence', () => {
    it('should persist token across store resets', () => {
      // Set auth
      useAuthStore.getState().setAuth(mockToken, 86400, mockUser);

      // Simulate app reload by initializing from localStorage
      initializeAuthStore();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe(mockToken);
      expect(state.user).toEqual(mockUser);
    });

    it('should not restore expired token on init', () => {
      // Set auth with already expired token
      const expiresAt = Date.now() - 1000; // 1 second ago
      localStorage.setItem('photo_restoration_token', mockToken);
      localStorage.setItem('photo_restoration_token_expiry', expiresAt.toString());
      localStorage.setItem('photo_restoration_user', JSON.stringify(mockUser));

      // Try to initialize
      initializeAuthStore();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.token).toBe(null);
      expect(localStorage.getItem('photo_restoration_token')).toBe(null);
    });

    it('should clear auth if localStorage is incomplete', () => {
      // Set only token, missing expiry and user
      localStorage.setItem('photo_restoration_token', mockToken);

      initializeAuthStore();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(localStorage.getItem('photo_restoration_token')).toBe(null);
    });
  });

  describe('Remember Me functionality', () => {
    it('should set 24-hour expiration for regular login', () => {
      const store = useAuthStore.getState();
      const expiresIn = 86400; // 24 hours

      const beforeTime = Date.now();
      store.setAuth(mockToken, expiresIn, mockUser);
      const state = useAuthStore.getState();

      const expectedExpiry = beforeTime + 86400 * 1000;
      expect(state.expiresAt).toBeGreaterThanOrEqual(expectedExpiry - 100);
      expect(state.expiresAt).toBeLessThanOrEqual(expectedExpiry + 100);
    });

    it('should set 7-day expiration for Remember Me login', () => {
      const store = useAuthStore.getState();
      const expiresIn = 604800; // 7 days

      const beforeTime = Date.now();
      store.setAuth(mockToken, expiresIn, mockUser);
      const state = useAuthStore.getState();

      const expectedExpiry = beforeTime + 604800 * 1000;
      expect(state.expiresAt).toBeGreaterThanOrEqual(expectedExpiry - 100);
      expect(state.expiresAt).toBeLessThanOrEqual(expectedExpiry + 100);
    });
  });

  describe('checkTokenExpiry', () => {
    it('should return false for valid token', () => {
      const store = useAuthStore.getState();
      store.setAuth(mockToken, 86400, mockUser);

      const isExpired = store.checkTokenExpiry();

      expect(isExpired).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });

    it('should return true and clear auth for expired token', () => {
      const store = useAuthStore.getState();

      // Set token that expires immediately
      const expiresAt = Date.now() - 1000; // Already expired
      useAuthStore.setState({
        isAuthenticated: true,
        token: mockToken,
        user: mockUser,
        expiresAt,
      });

      const isExpired = store.checkTokenExpiry();

      expect(isExpired).toBe(true);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().token).toBe(null);
    });

    it('should return false when no token exists', () => {
      const store = useAuthStore.getState();
      store.clearAuth();

      const isExpired = store.checkTokenExpiry();

      expect(isExpired).toBe(false);
    });
  });

  describe('isTokenExpired', () => {
    it('should return false for valid token', () => {
      const store = useAuthStore.getState();
      store.setAuth(mockToken, 86400, mockUser);

      const isExpired = store.isTokenExpired();

      expect(isExpired).toBe(false);
    });

    it('should return true for expired token', () => {
      const expiresAt = Date.now() - 1000; // Already expired
      useAuthStore.setState({
        isAuthenticated: true,
        token: mockToken,
        user: mockUser,
        expiresAt,
      });

      const isExpired = useAuthStore.getState().isTokenExpired();

      expect(isExpired).toBe(true);
    });

    it('should return true when no expiration is set', () => {
      useAuthStore.setState({
        isAuthenticated: true,
        token: mockToken,
        user: mockUser,
        expiresAt: null,
      });

      const isExpired = useAuthStore.getState().isTokenExpired();

      expect(isExpired).toBe(true);
    });
  });

  describe('Auto-logout on token expiration', () => {
    it('should setup periodic token expiry check', () => {
      vi.useFakeTimers();
      const setIntervalSpy = vi.spyOn(global, 'setInterval');

      setupTokenExpiryCheck();

      expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 60000);

      vi.useRealTimers();
    });

    it('should auto-logout when token expires during periodic check', () => {
      vi.useFakeTimers();

      // Set token that will expire soon
      const store = useAuthStore.getState();
      store.setAuth(mockToken, 1, mockUser); // Expires in 1 second

      // Setup periodic check
      setupTokenExpiryCheck();

      // Fast-forward past expiration
      vi.advanceTimersByTime(2000); // 2 seconds

      // Trigger the periodic check
      vi.advanceTimersByTime(60000); // 1 minute (check interval)

      // Token should be cleared
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);

      vi.useRealTimers();
    });
  });
});
