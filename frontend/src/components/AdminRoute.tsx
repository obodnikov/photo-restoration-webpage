/**
 * Admin Route wrapper component
 * Protects routes that require admin role
 */

import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../services/authStore';

export interface AdminRouteProps {
  children: React.ReactNode;
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated || !user) {
    // Not authenticated, redirect to login
    return <Navigate to="/login" replace />;
  }

  if (user.role !== 'admin') {
    // Not an admin, redirect to home
    return <Navigate to="/" replace />;
  }

  // User is authenticated and is admin
  return <>{children}</>;
};
