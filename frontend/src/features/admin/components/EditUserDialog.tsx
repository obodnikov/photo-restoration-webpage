/**
 * Edit User Dialog component
 */

import React, { useState, useEffect } from 'react';
import { Modal } from '../../../components/Modal';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';
import type { AdminUser, UpdateUserRequest } from '../types';

export interface EditUserDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (userId: number, userData: UpdateUserRequest) => Promise<void>;
  user: AdminUser | null;
  isLoading?: boolean;
}

export const EditUserDialog: React.FC<EditUserDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  user,
  isLoading = false,
}) => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'admin' | 'user'>('user');
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Populate form when user changes
  useEffect(() => {
    if (user) {
      setEmail(user.email);
      setFullName(user.full_name);
      setRole(user.role);
      setIsActive(user.is_active);
      setError(null);
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!user) return;

    try {
      // Only include changed fields
      const updates: UpdateUserRequest = {};

      if (email !== user.email) {
        updates.email = email;
      }

      if (fullName !== user.full_name) {
        updates.full_name = fullName;
      }

      if (role !== user.role) {
        updates.role = role;
      }

      if (isActive !== user.is_active) {
        updates.is_active = isActive;
      }

      // Check if anything changed
      if (Object.keys(updates).length === 0) {
        setError('No changes detected');
        return;
      }

      await onSubmit(user.id, updates);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update user';
      setError(message);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setError(null);
      onClose();
    }
  };

  if (!user) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Edit User: ${user.username}`}
      closeOnOverlayClick={!isLoading}
      closeOnEscape={!isLoading}
    >
      <form onSubmit={handleSubmit} className="admin-form">
        {error && <ErrorMessage message={error} />}

        <div className="form-group">
          <label className="form-label">Username</label>
          <input
            type="text"
            className="form-input"
            value={user.username}
            disabled
            readOnly
          />
          <p className="form-help">Username cannot be changed</p>
        </div>

        <div className="form-group">
          <label htmlFor="edit-email" className="form-label">
            Email *
          </label>
          <input
            id="edit-email"
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="edit-fullname" className="form-label">
            Full Name *
          </label>
          <input
            id="edit-fullname"
            type="text"
            className="form-input"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            maxLength={255}
            disabled={isLoading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="edit-role" className="form-label">
            Role *
          </label>
          <select
            id="edit-role"
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
            id="edit-is-active"
            type="checkbox"
            className="form-checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            disabled={isLoading}
          />
          <label htmlFor="edit-is-active" className="checkbox-label">
            Account is active
          </label>
          <p className="form-help">
            Inactive users cannot log in
          </p>
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
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  );
};
