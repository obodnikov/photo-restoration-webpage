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
  // Rehydration state
  hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;

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
      hasHydrated: false,

      // Set hydration state
      setHasHydrated: (state: boolean) => {
        set({ hasHydrated: state });
      },

      // Set authentication state
      setAuth: (token: string, expiresIn: number, user: User) => {
        const expiresAt = Date.now() + expiresIn * 1000;

        console.log('[authStore] setAuth called:', {
          tokenLength: token.length,
          expiresIn,
          expiresAt,
          expiresAtDate: new Date(expiresAt).toISOString(),
          user,
        });

        set({
          isAuthenticated: true,
          token,
          user,
          expiresAt,
        });

        console.log('[authStore] State updated, checking localStorage...');
        // Give persist middleware a moment to save, then check
        setTimeout(() => {
          const stored = localStorage.getItem('auth-storage');
          console.log('[authStore] localStorage after setAuth:', stored);
        }, 100);

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
      // Handle rehydration from localStorage
      onRehydrateStorage: () => {
        console.log('[authStore] Starting rehydration from localStorage...');
        return (state, error) => {
          if (error) {
            console.error('[authStore] Rehydration error:', error);
          } else if (state) {
            console.log('[authStore] Rehydrated successfully:', {
              hasToken: !!state.token,
              isAuthenticated: state.isAuthenticated,
              expiresAt: state.expiresAt,
            });

            // Check if rehydrated token is expired
            if (state.token && state.expiresAt && Date.now() >= state.expiresAt) {
              console.log('[authStore] Rehydrated token is expired, clearing...');
              state.clearAuth();
            }

            // Mark that hydration is complete
            state.setHasHydrated(true);
          } else {
            console.log('[authStore] No stored state to rehydrate');
            // Still mark hydration as complete even if no state was found
            useAuthStore.getState().setHasHydrated(true);
          }
        };
      },
    }
  )
);

/**
 * Initialize auth store from localStorage on app start
 * Note: Zustand persist middleware automatically loads from localStorage
 * via the onRehydrateStorage callback above
 */
export function initializeAuthStore() {
  console.log('[authStore] Auth store initialization triggered');
  // The actual rehydration is handled by Zustand persist middleware
  // See onRehydrateStorage callback in the store definition above
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
