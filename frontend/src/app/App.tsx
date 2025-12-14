/**
 * Main App component with routing and authentication.
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { initializeAuthStore, setupTokenExpiryCheck } from '../services/authStore';
import { LoginPage } from '../features/auth/pages/LoginPage';
import { ProtectedRoute } from './ProtectedRoute';
import '../styles/base.css';
import '../styles/layout.css';

// Placeholder home page (will be implemented in Phase 1.7)
function HomePage() {
  return (
    <div className="container">
      <h1>Welcome to Photo Restoration</h1>
      <p>Home page - Image restoration feature coming in Phase 1.7</p>
    </div>
  );
}

export function App() {
  // Initialize auth store from localStorage on app start
  useEffect(() => {
    initializeAuthStore();
    setupTokenExpiryCheck();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          }
        />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
