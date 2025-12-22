/**
 * Delete User Confirmation Dialog component
 */

import React, { useState } from 'react';
import { Modal } from '../../../components/Modal';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';
import type { AdminUser } from '../types';

export interface DeleteUserDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (userId: number) => Promise<void>;
  user: AdminUser | null;
  isLoading?: boolean;
}

export const DeleteUserDialog: React.FC<DeleteUserDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  user,
  isLoading = false,
}) => {
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    if (!user) return;

    setError(null);

    try {
      await onConfirm(user.id);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete user';
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
      title="Confirm Delete User"
      closeOnOverlayClick={!isLoading}
      closeOnEscape={!isLoading}
    >
      <div className="delete-dialog-content">
        {error && <ErrorMessage message={error} />}

        <div className="warning-message">
          <div className="warning-icon">⚠️</div>
          <p>
            Are you sure you want to delete the user <strong>{user.username}</strong>?
          </p>
        </div>

        <div className="warning-details">
          <p><strong>This action cannot be undone.</strong></p>
          <p>This will permanently delete:</p>
          <ul>
            <li>User account ({user.email})</li>
            <li>All user sessions</li>
            <li>All processed images</li>
            <li>All associated data</li>
          </ul>
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
          <Button
            type="button"
            variant="danger"
            onClick={handleConfirm}
            loading={isLoading}
          >
            Delete User
          </Button>
        </div>
      </div>
    </Modal>
  );
};
