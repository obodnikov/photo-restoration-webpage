/**
 * Main App component with routing and authentication.
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { initializeAuthStore, setupTokenExpiryCheck } from '../services/authStore';
import { LoginPage } from '../features/auth/pages/LoginPage';
import { ForcePasswordChangePage } from '../features/auth/pages/ForcePasswordChangePage';
import { RestorationPage } from '../features/restoration/pages/RestorationPage';
import { HistoryPage } from '../features/history/pages/HistoryPage';
import { ProfilePage } from '../features/profile/pages/ProfilePage';
import { AdminUsersPage } from '../features/admin/pages/AdminUsersPage';
import { AdminModelConfigPage } from '../features/admin/pages/AdminModelConfigPage';
import { ProtectedRoute } from './ProtectedRoute';
import { AdminRoute } from '../components/AdminRoute';
import { RequirePasswordChangeRoute } from '../components/RequirePasswordChangeRoute';
import { Layout } from '../components/Layout';
import '../styles/base.css';
import '../styles/layout.css';
import '../styles/components/shared.css';
import '../styles/components/auth.css';
import '../styles/components/restoration.css';
import '../styles/components/history.css';
import '../styles/components/profile.css';
import '../styles/components/admin.css';
import '../styles/components/modelConfig.css';
import '../styles/components/force-password-change.css';

export function App() {
  // Initialize auth store from localStorage on app start
  useEffect(() => {
    initializeAuthStore();
    setupTokenExpiryCheck();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes - no Layout wrapper */}
        <Route path="/login" element={<LoginPage />} />

        {/* Force password change route - special protected route */}
        <Route
          path="/change-password"
          element={
            <RequirePasswordChangeRoute>
              <ForcePasswordChangePage />
            </RequirePasswordChangeRoute>
          }
        />

        {/* Protected routes - with Layout wrapper */}
        <Route
          path="/"
          element={
            <Layout>
              <ProtectedRoute>
                <RestorationPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/history"
          element={
            <Layout>
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/profile"
          element={
            <Layout>
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/admin/users"
          element={
            <Layout>
              <AdminRoute>
                <AdminUsersPage />
              </AdminRoute>
            </Layout>
          }
        />
        <Route
          path="/admin/models"
          element={
            <Layout>
              <AdminRoute>
                <AdminModelConfigPage />
              </AdminRoute>
            </Layout>
          }
        />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
