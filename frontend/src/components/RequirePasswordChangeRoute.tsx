/**
 * RequirePasswordChangeRoute - Route wrapper for forced password change page
 *
 * This component ensures that users with password_must_change flag
 * can only access the change-password page and no other routes.
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../services/authStore';

interface RequirePasswordChangeRouteProps {
  children: React.ReactNode;
}

/**
 * Route wrapper that only allows access to the change-password page
 * when password_must_change is true
 */
export const RequirePasswordChangeRoute: React.FC<RequirePasswordChangeRouteProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();

  // If not authenticated, redirect to login
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  // User must have password_must_change flag to access this route
  // If they don't have it, redirect to home (password already changed)
  if (!user.password_must_change) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
