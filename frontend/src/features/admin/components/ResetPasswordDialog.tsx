/**
 * Reset Password Dialog component
 */

import React, { useState } from 'react';
import { Modal } from '../../../components/Modal';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';
import { generateRandomPassword } from '../services/adminService';
import type { AdminUser, ResetPasswordRequest } from '../types';

export interface ResetPasswordDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (userId: number, passwordData: ResetPasswordRequest) => Promise<void>;
  user: AdminUser | null;
  isLoading?: boolean;
}

export const ResetPasswordDialog: React.FC<ResetPasswordDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  user,
  isLoading = false,
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [passwordMustChange, setPasswordMustChange] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleGeneratePassword = () => {
    try {
      const password = generateRandomPassword(12);
      setNewPassword(password);
      setShowPassword(true); // Show so admin can copy it
      setError(null); // Clear any previous errors
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate password';
      setError(message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!user) return;

    // Validate password strength
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(newPassword)) {
      setError('Password must contain at least one uppercase letter');
      return;
    }

    if (!/[a-z]/.test(newPassword)) {
      setError('Password must contain at least one lowercase letter');
      return;
    }

    if (!/\d/.test(newPassword)) {
      setError('Password must contain at least one digit');
      return;
    }

    try {
      await onSubmit(user.id, {
        new_password: newPassword,
        password_must_change: passwordMustChange,
      });

      // Reset form
      setNewPassword('');
      setPasswordMustChange(true);
      setShowPassword(false);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reset password';
      setError(message);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setError(null);
      setNewPassword('');
      setPasswordMustChange(true);
      setShowPassword(false);
      onClose();
    }
  };

  if (!user) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Reset Password: ${user.username}`}
      closeOnOverlayClick={!isLoading}
      closeOnEscape={!isLoading}
    >
      <form onSubmit={handleSubmit} className="admin-form">
        {error && <ErrorMessage message={error} />}

        <div className="info-message">
          <p>
            Reset the password for <strong>{user.username}</strong> ({user.email})
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="reset-new-password" className="form-label">
            New Temporary Password *
          </label>
          <div className="password-input-group">
            <input
              id="reset-new-password"
              type={showPassword ? 'text' : 'password'}
              className="form-input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              disabled={isLoading}
              autoComplete="new-password"
            />
            <Button
              type="button"
              variant="secondary"
              size="small"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isLoading}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? 'Hide' : 'Show'}
            </Button>
            <Button
              type="button"
              variant="primary"
              size="small"
              onClick={handleGeneratePassword}
              disabled={isLoading}
            >
              Generate
            </Button>
          </div>
          <p className="form-help">
            Min 8 characters, must include uppercase, lowercase, and digit
          </p>
        </div>

        <div className="form-group checkbox-group">
          <input
            id="reset-password-must-change"
            type="checkbox"
            className="form-checkbox"
            checked={passwordMustChange}
            onChange={(e) => setPasswordMustChange(e.target.checked)}
            disabled={isLoading}
          />
          <label htmlFor="reset-password-must-change" className="checkbox-label">
            Require password change on next login
          </label>
          <p className="form-help">
            User will be forced to change this password when they log in
          </p>
        </div>

        <div className="warning-message">
          <div className="warning-icon">⚠️</div>
          <p><strong>Important:</strong> Make sure to securely share this password with the user.</p>
        </div>

        <div className="modal-actions">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={isLoading}>
            Reset Password
          </Button>
        </div>
      </form>
    </Modal>
  );
};
