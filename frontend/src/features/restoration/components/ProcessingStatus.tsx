/**
 * ProcessingStatus component
 * Displays processing state with progress bar
 */

import React from 'react';
import { Loader } from '../../../components/Loader';

export interface ProcessingStatusProps {
  isProcessing: boolean;
  progress: number;
  message?: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  isProcessing,
  progress,
  message = 'Processing your image...',
}) => {
  if (!isProcessing) {
    return null;
  }

  return (
    <div className="processing-status">
      <Loader size="large" />
      <div className="processing-info">
        <p className="processing-message">{message}</p>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="processing-progress">{progress}%</p>
      </div>
    </div>
  );
};
