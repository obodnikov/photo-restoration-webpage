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

        // Note: Zustand persist middleware handles localStorage automatically
        // No need to manually store - the persist middleware will sync this
      },

      // Clear authentication state (logout)
      clearAuth: () => {
        set({
          isAuthenticated: false,
          token: null,
          user: null,
          expiresAt: null,
        });

        // Note: Zustand persist middleware handles localStorage automatically
        // The persist middleware will clear the storage when state is set to null
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
 * Note: Zustand persist middleware automatically loads from localStorage,
 * but we still need to check if the loaded token is expired
 */
export function initializeAuthStore() {
  console.log('[authStore] Initializing auth store...');

  // Zustand persist middleware has already loaded the state
  const state = useAuthStore.getState();

  console.log('[authStore] Current state:', {
    isAuthenticated: state.isAuthenticated,
    hasToken: !!state.token,
    expiresAt: state.expiresAt,
    isExpired: state.isTokenExpired(),
  });

  // Check if loaded token is expired
  if (state.token && state.expiresAt && Date.now() >= state.expiresAt) {
    console.log('[authStore] Stored token is expired, clearing auth...');
    state.clearAuth();
    return;
  }

  if (state.token) {
    console.log('[authStore] Auth state loaded successfully from localStorage');
  } else {
    console.log('[authStore] No auth state in localStorage');
  }
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
