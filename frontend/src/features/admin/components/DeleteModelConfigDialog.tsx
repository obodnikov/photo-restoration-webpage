/**
 * Delete Model Configuration Confirmation Dialog
 */

import React, { useState } from 'react';
import { Modal } from '../../../components/Modal';
import { Button } from '../../../components/Button';
import { ErrorMessage } from '../../../components/ErrorMessage';
import type { ModelConfigListItem } from '../types';

export interface DeleteModelConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (modelId: string) => Promise<void>;
  config: ModelConfigListItem | null;
  isLoading?: boolean;
}

export const DeleteModelConfigDialog: React.FC<DeleteModelConfigDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  config,
  isLoading = false,
}) => {
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    if (!config) return;

    // Prevent deletion of non-local configs
    if (config.source !== 'local') {
      setError('Only local configurations can be deleted. Default configurations are read-only.');
      return;
    }

    setError(null);

    try {
      await onConfirm(config.id);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete configuration';
      setError(message);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setError(null);
      onClose();
    }
  };

  if (!config) return null;

  const canDelete = config.source === 'local';

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Confirm Delete Model Configuration"
      closeOnOverlayClick={!isLoading}
      closeOnEscape={!isLoading}
    >
      <div className="delete-dialog-content">
        {error && <ErrorMessage message={error} />}

        {canDelete ? (
          <>
            <div className="warning-message">
              <div className="warning-icon">⚠️</div>
              <p>
                Are you sure you want to delete the model configuration{' '}
                <strong>{config.name}</strong>?
              </p>
            </div>

            <div className="warning-details">
              <p>
                <strong>This action cannot be undone.</strong>
              </p>
              <p>This will permanently delete:</p>
              <ul>
                <li>Model ID: {config.id}</li>
                <li>Configuration from local.json</li>
                <li>All custom settings for this model</li>
              </ul>
              <p>
                Note: Default configurations will still be available after deletion.
              </p>
            </div>

            <div className="modal-actions">
              <Button type="button" variant="secondary" onClick={handleClose} disabled={isLoading}>
                Cancel
              </Button>
              <Button
                type="button"
                variant="danger"
                onClick={handleConfirm}
                loading={isLoading}
              >
                Delete Configuration
              </Button>
            </div>
          </>
        ) : (
          <>
            <div className="info-message">
              <p>
                <strong>Cannot Delete Default Configuration</strong>
              </p>
              <p>
                The model configuration <strong>{config.name}</strong> (source: {config.source})
                is a default configuration and cannot be deleted.
              </p>
              <p>
                You can only delete configurations that were created in local.json. Default
                configurations are read-only and serve as fallback values.
              </p>
            </div>

            <div className="modal-actions">
              <Button type="button" variant="primary" onClick={handleClose}>
                Close
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};
