/**
 * SessionsList component - displays active sessions with remote logout
 */

import React, { useState } from 'react';
import type { Session } from '../types';
import { Card } from '../../../components/Card';
import { Button } from '../../../components/Button';
import { Modal } from '../../../components/Modal';
import { ErrorMessage } from '../../../components/ErrorMessage';

interface SessionsListProps {
  sessions: Session[];
  onDeleteSession: (sessionId: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

export const SessionsList: React.FC<SessionsListProps> = ({
  sessions,
  onDeleteSession,
  isLoading = false,
  error = null,
}) => {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const handleDeleteClick = (sessionId: string) => {
    setSelectedSessionId(sessionId);
  };

  const handleConfirmDelete = async () => {
    if (!selectedSessionId) return;

    setIsDeleting(true);
    try {
      await onDeleteSession(selectedSessionId);
      setSelectedSessionId(null);
    } catch (err) {
      console.error('Failed to delete session:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setSelectedSessionId(null);
  };

  // Show error state if sessions failed to load
  if (error) {
    return (
      <Card variant="light">
        <div className="sessions-list">
          <h2>Active Sessions</h2>
          <p className="form-description">
            Manage your active sessions across different devices.
          </p>
          <ErrorMessage
            message={error}
            title="Failed to Load Sessions"
          />
        </div>
      </Card>
    );
  }

  // Show empty state only if there are no sessions AND no error
  if (sessions.length === 0) {
    return (
      <Card variant="light">
        <div className="sessions-list">
          <h2>Active Sessions</h2>
          <p className="empty-state">No active sessions found.</p>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card variant="light">
        <div className="sessions-list">
          <div className="sessions-header">
            <h2>Active Sessions</h2>
            <span className="sessions-count">{sessions.length} session(s)</span>
          </div>

          <p className="form-description">
            Manage your active sessions across different devices. You can log out from
            other devices remotely for security.
          </p>

          <div className="sessions-items">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${session.is_current ? 'current' : ''}`}
              >
                <div className="session-info">
                  <div className="session-meta">
                    {session.is_current && (
                      <span className="current-badge">Current Session</span>
                    )}
                    <div className="session-dates">
                      <div className="session-field">
                        <span className="session-label">Created:</span>
                        <span className="session-value">{formatDate(session.created_at)}</span>
                      </div>
                      <div className="session-field">
                        <span className="session-label">Last Active:</span>
                        <span className="session-value">
                          {formatDate(session.last_accessed)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {!session.is_current && (
                  <div className="session-actions">
                    <Button
                      variant="secondary"
                      size="small"
                      onClick={() => handleDeleteClick(session.id)}
                      disabled={isLoading}
                    >
                      Logout
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Modal
        isOpen={selectedSessionId !== null}
        onClose={handleCancelDelete}
        title="Confirm Logout"
      >
        <p>
          Are you sure you want to log out from this session? This action will
          immediately end the session on that device.
        </p>

        <div className="modal-actions">
          <Button
            variant="secondary"
            onClick={handleCancelDelete}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleConfirmDelete}
            loading={isDeleting}
            disabled={isDeleting}
          >
            Confirm Logout
          </Button>
        </div>
      </Modal>
    </>
  );
};
