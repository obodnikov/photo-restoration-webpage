/**
 * Main App component with routing and authentication.
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { initializeAuthStore, setupTokenExpiryCheck } from '../services/authStore';
import { LoginPage } from '../features/auth/pages/LoginPage';
import { RestorationPage } from '../features/restoration/pages/RestorationPage';
import { HistoryPage } from '../features/history/pages/HistoryPage';
import { ProtectedRoute } from './ProtectedRoute';
import { Layout } from '../components/Layout';
import '../styles/base.css';
import '../styles/layout.css';
import '../styles/components/shared.css';
import '../styles/components/auth.css';
import '../styles/components/restoration.css';
import '../styles/components/history.css';

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

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
