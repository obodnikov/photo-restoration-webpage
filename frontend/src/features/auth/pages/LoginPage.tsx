/**
 * Login page with sqowe branding.
 */

import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../../services/authStore';
import { LoginForm } from '../components/LoginForm';
import '../../../styles/components/auth.css';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Get success message from navigation state (e.g., after password change)
  const successMessage = location.state?.message as string | undefined;

  // Redirect to home if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">Photo Restoration</h1>
          <p className="login-subtitle">
            Sign in to restore your precious memories
          </p>
        </div>

        {successMessage && (
          <div className="success-message">
            {successMessage}
          </div>
        )}

        <LoginForm />
      </div>
    </div>
  );
}
