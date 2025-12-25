/**
 * Protected route wrapper component.
 *
 * This component checks authentication before rendering child routes.
 * If user is not authenticated, redirects to login page.
 */

import { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../services/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  // Use selectors to prevent unnecessary re-renders
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const checkTokenExpiry = useAuthStore((state) => state.checkTokenExpiry);

  // Check token expiry on every render
  useEffect(() => {
    checkTokenExpiry();
  }, [checkTokenExpiry]);

  // Wait for Zustand persist to rehydrate before checking auth
  if (!hasHydrated) {
    console.log('[ProtectedRoute] Waiting for auth store to rehydrate...');
    return null; // or a loading spinner
  }

  console.log('[ProtectedRoute] Hydration complete, isAuthenticated:', isAuthenticated);

  if (!isAuthenticated) {
    console.log('[ProtectedRoute] Not authenticated, redirecting to login');
    // Redirect to login, but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user must change password
  // Note: /change-password route is NOT wrapped with ProtectedRoute, so this guard
  // prevents access to all OTHER protected routes until password is changed
  if (user?.password_must_change && location.pathname !== '/change-password') {
    console.log('[ProtectedRoute] User must change password, redirecting to /change-password');
    return <Navigate to="/change-password" replace />;
  }

  return <>{children}</>;
}
