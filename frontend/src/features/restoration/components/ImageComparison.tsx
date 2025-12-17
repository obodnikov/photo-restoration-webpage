/**
 * ImageComparison component
 * Side-by-side view with three modes: original, processed, both
 */

import React from 'react';
import type { ImageViewMode } from '../types';
import { Button } from '../../../components/Button';

export interface ImageComparisonProps {
  originalUrl: string;
  processedUrl: string;
  viewMode: ImageViewMode;
  onViewModeChange: (mode: ImageViewMode) => void;
  onDownload?: () => void;
}

export const ImageComparison: React.FC<ImageComparisonProps> = ({
  originalUrl,
  processedUrl,
  viewMode,
  onViewModeChange,
  onDownload,
}) => {
  return (
    <div className="image-comparison">
      <div className="comparison-controls">
        <div className="view-mode-buttons">
          <button
            type="button"
            className={`view-mode-btn ${viewMode === 'original' ? 'active' : ''}`}
            onClick={() => onViewModeChange('original')}
          >
            Original
          </button>
          <button
            type="button"
            className={`view-mode-btn ${viewMode === 'processed' ? 'active' : ''}`}
            onClick={() => onViewModeChange('processed')}
          >
            Restored
          </button>
          <button
            type="button"
            className={`view-mode-btn ${viewMode === 'both' ? 'active' : ''}`}
            onClick={() => onViewModeChange('both')}
          >
            Compare
          </button>
        </div>

        {onDownload && (
          <Button variant="gradient" onClick={onDownload}>
            Download Restored
          </Button>
        )}
      </div>

      <div className={`comparison-viewer mode-${viewMode}`}>
        {(viewMode === 'original' || viewMode === 'both') && (
          <div className="image-panel">
            <div className="image-header">
              <h4>Original</h4>
            </div>
            <div className="image-container">
              <img src={originalUrl} alt="Original" />
            </div>
          </div>
        )}

        {(viewMode === 'processed' || viewMode === 'both') && (
          <div className="image-panel">
            <div className="image-header">
              <h4>Restored</h4>
            </div>
            <div className="image-container">
              <img src={processedUrl} alt="Restored" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
