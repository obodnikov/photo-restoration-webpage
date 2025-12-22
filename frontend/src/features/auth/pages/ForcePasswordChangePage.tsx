/**
 * Force Password Change Page
 *
 * This page is shown when a user logs in with password_must_change flag set to true.
 * The user cannot access other parts of the application until they change their password.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/Button';
import { Card } from '../../../components/Card';
import { ErrorMessage } from '../../../components/ErrorMessage';
import { useAuthStore } from '../../../services/authStore';
import * as api from '../../../services/apiClient';

export const ForcePasswordChangePage: React.FC = () => {
  const navigate = useNavigate();
  const clearAuth = useAuthStore((state) => state.clearAuth);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate passwords
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('All fields are required');
      return;
    }

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(newPassword)) {
      setError('New password must contain at least one uppercase letter');
      return;
    }

    if (!/[a-z]/.test(newPassword)) {
      setError('New password must contain at least one lowercase letter');
      return;
    }

    if (!/\d/.test(newPassword)) {
      setError('New password must contain at least one digit');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword === currentPassword) {
      setError('New password must be different from current password');
      return;
    }

    setIsLoading(true);

    try {
      // Call the password change endpoint
      await api.put('/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      // Password changed successfully - the old JWT still has password_must_change=true
      // We need to force logout and redirect to login to get a fresh token
      // Alternative: We could re-login automatically, but forcing manual re-login is more secure
      clearAuth();

      // Redirect to login with success message
      navigate('/login', {
        state: {
          message: 'Password changed successfully! Please login with your new password.'
        }
      });
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to change password. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  return (
    <div className="force-password-change-page">
      <div className="container">
        <Card variant="dark" className="force-password-change-card">
          <div className="force-password-change-header">
            <h1>Password Change Required</h1>
            <p className="warning-text">
              For security reasons, you must change your password before accessing the application.
            </p>
          </div>

          {error && <ErrorMessage message={error} />}

          <form onSubmit={handleSubmit} className="force-password-change-form">
            <div className="form-group">
              <label htmlFor="currentPassword">Current Password</label>
              <input
                type="password"
                id="currentPassword"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                disabled={isLoading}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <input
                type="password"
                id="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                disabled={isLoading}
              />
              <small className="form-hint">
                Must be at least 8 characters with uppercase, lowercase, and digits
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="form-actions">
              <Button
                type="submit"
                variant="gradient"
                loading={isLoading}
                disabled={isLoading}
                className="submit-button"
              >
                Change Password
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleLogout}
                disabled={isLoading}
              >
                Logout
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
