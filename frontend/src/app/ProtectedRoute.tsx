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
  const { isAuthenticated, checkTokenExpiry } = useAuthStore();

  // Check token expiry on every render
  useEffect(() => {
    checkTokenExpiry();
  }, [checkTokenExpiry]);

  if (!isAuthenticated) {
    // Redirect to login, but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
