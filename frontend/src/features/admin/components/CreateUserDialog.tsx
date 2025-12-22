/**
 * Create User Dialog component
 */

import React, { useState } from 'react';
import { Modal } from '../../../components/Modal';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';
import { generateRandomPassword } from '../services/adminService';
import type { CreateUserRequest } from '../types';

export interface CreateUserDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (userData: CreateUserRequest) => Promise<void>;
  isLoading?: boolean;
}

export const CreateUserDialog: React.FC<CreateUserDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'admin' | 'user'>('user');
  const [passwordMustChange, setPasswordMustChange] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleGeneratePassword = () => {
    try {
      const newPassword = generateRandomPassword(12);
      setPassword(newPassword);
      setShowPassword(true); // Show password so admin can copy it
      setError(null); // Clear any previous errors
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate password';
      setError(message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate password strength
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(password)) {
      setError('Password must contain at least one uppercase letter');
      return;
    }

    if (!/[a-z]/.test(password)) {
      setError('Password must contain at least one lowercase letter');
      return;
    }

    if (!/\d/.test(password)) {
      setError('Password must contain at least one digit');
      return;
    }

    try {
      await onSubmit({
        username,
        email,
        full_name: fullName,
        password,
        role,
        password_must_change: passwordMustChange,
      });

      // Reset form
      setUsername('');
      setEmail('');
      setFullName('');
      setPassword('');
      setRole('user');
      setPasswordMustChange(true);
      setShowPassword(false);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create user';
      setError(message);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      // Clear all form state to prevent leaking sensitive data
      setUsername('');
      setEmail('');
      setFullName('');
      setPassword('');
      setRole('user');
      setPasswordMustChange(true);
      setShowPassword(false);
      setError(null);
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create New User"
      closeOnOverlayClick={!isLoading}
      closeOnEscape={!isLoading}
    >
      <form onSubmit={handleSubmit} className="admin-form">
        {error && <ErrorMessage message={error} />}

        <div className="form-group">
          <label htmlFor="create-username" className="form-label">
            Username *
          </label>
          <input
            id="create-username"
            type="text"
            className="form-input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
            maxLength={50}
            pattern="[A-Za-z0-9_-]+"
            title="Username can only contain letters, numbers, underscores, and hyphens"
            disabled={isLoading}
            autoComplete="off"
          />
          <p className="form-help">
            3-50 characters, letters, numbers, underscores, hyphens only
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="create-email" className="form-label">
            Email *
          </label>
          <input
            id="create-email"
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="off"
          />
        </div>

        <div className="form-group">
          <label htmlFor="create-fullname" className="form-label">
            Full Name *
          </label>
          <input
            id="create-fullname"
            type="text"
            className="form-input"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            maxLength={255}
            disabled={isLoading}
            autoComplete="off"
          />
        </div>

        <div className="form-group">
          <label htmlFor="create-password" className="form-label">
            Temporary Password *
          </label>
          <div className="password-input-group">
            <input
              id="create-password"
              type={showPassword ? 'text' : 'password'}
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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

        <div className="form-group">
          <label htmlFor="create-role" className="form-label">
            Role *
          </label>
          <select
            id="create-role"
            className="form-select"
            value={role}
            onChange={(e) => setRole(e.target.value as 'admin' | 'user')}
            disabled={isLoading}
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <div className="form-group checkbox-group">
          <input
            id="create-password-must-change"
            type="checkbox"
            className="form-checkbox"
            checked={passwordMustChange}
            onChange={(e) => setPasswordMustChange(e.target.checked)}
            disabled={isLoading}
          />
          <label htmlFor="create-password-must-change" className="checkbox-label">
            Require password change on first login
          </label>
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
            Create User
          </Button>
        </div>
      </form>
    </Modal>
  );
};
