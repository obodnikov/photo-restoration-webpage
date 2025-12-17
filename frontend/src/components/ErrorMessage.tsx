/**
 * ErrorMessage component for displaying user-friendly error messages
 */

import React from 'react';

export interface ErrorMessageProps {
  message: string;
  title?: string;
  onClose?: () => void;
  className?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  title = 'Error',
  onClose,
  className = '',
}) => {
  return (
    <div className={`error-message ${className}`}>
      <div className="error-message-content">
        <div className="error-message-header">
          <h4 className="error-message-title">{title}</h4>
          {onClose && (
            <button
              className="error-message-close"
              onClick={onClose}
              aria-label="Close error message"
            >
              &times;
            </button>
          )}
        </div>
        <p className="error-message-text">{message}</p>
      </div>
    </div>
  );
};
