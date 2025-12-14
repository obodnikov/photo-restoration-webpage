/**
 * Authentication state management with Zustand.
 *
 * This store manages:
 * - Authentication state (token, user, expiration)
 * - Token persistence in localStorage
 * - Auto-logout on token expiration
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthState, User } from '../features/auth/types';

const TOKEN_STORAGE_KEY = 'photo_restoration_token';
const TOKEN_EXPIRY_KEY = 'photo_restoration_token_expiry';
const USER_STORAGE_KEY = 'photo_restoration_user';

interface AuthStore extends AuthState {
  // Actions
  setAuth: (token: string, expiresIn: number, user: User) => void;
  clearAuth: () => void;
  checkTokenExpiry: () => boolean;
  isTokenExpired: () => boolean;
}

/**
 * Authentication store
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      user: null,
      token: null,
      expiresAt: null,

      // Set authentication state
      setAuth: (token: string, expiresIn: number, user: User) => {
        const expiresAt = Date.now() + expiresIn * 1000;

        set({
          isAuthenticated: true,
          token,
          user,
          expiresAt,
        });

        // Store in localStorage
        localStorage.setItem(TOKEN_STORAGE_KEY, token);
        localStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt.toString());
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
      },

      // Clear authentication state (logout)
      clearAuth: () => {
        set({
          isAuthenticated: false,
          token: null,
          user: null,
          expiresAt: null,
        });

        // Clear from localStorage
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(TOKEN_EXPIRY_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      },

      // Check if token is expired and auto-logout if necessary
      checkTokenExpiry: () => {
        const state = get();

        if (!state.token || !state.expiresAt) {
          return false;
        }

        const isExpired = Date.now() >= state.expiresAt;

        if (isExpired) {
          console.log('Token expired, logging out...');
          state.clearAuth();
          return true;
        }

        return false;
      },

      // Check if token is expired (without auto-logout)
      isTokenExpired: () => {
        const state = get();

        if (!state.expiresAt) {
          return true;
        }

        return Date.now() >= state.expiresAt;
      },
    }),
    {
      name: 'auth-storage',
      // Only persist specific fields
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        expiresAt: state.expiresAt,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

/**
 * Initialize auth store from localStorage on app start
 */
export function initializeAuthStore() {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);
  const userStr = localStorage.getItem(USER_STORAGE_KEY);

  if (!token || !expiryStr || !userStr) {
    useAuthStore.getState().clearAuth();
    return;
  }

  const expiresAt = parseInt(expiryStr, 10);
  const user = JSON.parse(userStr);

  // Check if token is expired
  if (Date.now() >= expiresAt) {
    console.log('Stored token is expired, clearing auth...');
    useAuthStore.getState().clearAuth();
    return;
  }

  // Restore auth state
  const expiresIn = Math.floor((expiresAt - Date.now()) / 1000);
  useAuthStore.getState().setAuth(token, expiresIn, user);

  console.log('Auth state restored from localStorage');
}

/**
 * Setup periodic token expiry check
 * Checks every minute if the token has expired
 */
export function setupTokenExpiryCheck() {
  setInterval(() => {
    useAuthStore.getState().checkTokenExpiry();
  }, 60 * 1000); // Check every minute
}
