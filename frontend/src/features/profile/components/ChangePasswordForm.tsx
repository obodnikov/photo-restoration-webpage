/**
 * ChangePasswordForm component - allows user to change their password
 */

import React, { useState } from 'react';
import { Card } from '../../../components/Card';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';

interface ChangePasswordFormProps {
  onSubmit: (currentPassword: string, newPassword: string) => Promise<void>;
  isLoading?: boolean;
}

export const ChangePasswordForm: React.FC<ChangePasswordFormProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const validatePassword = (password: string): string | null => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one digit';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    // Validation
    if (!currentPassword) {
      setError('Current password is required');
      return;
    }

    if (!newPassword) {
      setError('New password is required');
      return;
    }

    const passwordError = validatePassword(newPassword);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (currentPassword === newPassword) {
      setError('New password must be different from current password');
      return;
    }

    try {
      await onSubmit(currentPassword, newPassword);
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      // Distinguish between different error types
      if (err instanceof Error) {
        // Check for network errors
        if (err.message.includes('network') || err.message.includes('fetch')) {
          setError('Network error. Please check your connection and try again.');
        } else if (err.message.includes('401') || err.message.includes('unauthorized')) {
          setError('Current password is incorrect. Please try again.');
        } else if (err.message.includes('400') || err.message.includes('validation')) {
          setError('Password validation failed. Please ensure it meets all requirements.');
        } else {
          setError(err.message);
        }
      } else {
        setError('Failed to change password. Please try again.');
      }
    }
  };

  return (
    <Card variant="light">
      <div className="change-password-form">
        <h2>Change Password</h2>
        <p className="form-description">
          Update your password to keep your account secure. Your password must be at least
          8 characters long and contain uppercase, lowercase, and numeric characters.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="currentPassword">Current Password</label>
            <input
              type="password"
              id="currentPassword"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              disabled={isLoading}
              required
              autoComplete="current-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              type="password"
              id="newPassword"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={isLoading}
              required
              autoComplete="new-password"
            />
            <small className="form-help">
              At least 8 characters with uppercase, lowercase, and digits
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm New Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              required
              autoComplete="new-password"
            />
          </div>

          {error && <ErrorMessage message={error} />}

          {success && (
            <div className="success-message">
              <span>Password changed successfully!</span>
              <button
                type="button"
                className="success-dismiss"
                onClick={() => setSuccess(false)}
                aria-label="Dismiss success message"
              >
                ×
              </button>
            </div>
          )}

          <div className="form-actions">
            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
              loading={isLoading}
            >
              Change Password
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
};
