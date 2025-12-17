/**
 * HistoryCard component
 * Displays individual history item with thumbnail and actions
 */

import React from 'react';
import type { HistoryItem } from '../types';
import { Button } from '../../../components/Button';
import { config } from '../../../config/config';

export interface HistoryCardProps {
  item: HistoryItem;
  onView: (item: HistoryItem) => void;
  onDelete: (item: HistoryItem) => void;
  onDownload: (item: HistoryItem) => void;
}

export const HistoryCard: React.FC<HistoryCardProps> = ({
  item,
  onView,
  onDelete,
  onDownload,
}) => {
  const baseUrl = config.apiBaseUrl.replace('/api/v1', '');
  const thumbnailUrl = `${baseUrl}${item.processed_url}`;

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="history-card">
      <div className="history-card-image" onClick={() => onView(item)}>
        <img src={thumbnailUrl} alt={item.original_filename} />
        <div className="history-card-overlay">
          <span className="view-icon">👁️</span>
        </div>
      </div>

      <div className="history-card-content">
        <h4 className="history-card-title">{item.original_filename}</h4>
        <div className="history-card-meta">
          <span className="history-meta-item">
            <strong>Model:</strong> {item.model_id}
          </span>
          <span className="history-meta-item">
            <strong>Date:</strong> {formatDate(item.created_at)}
          </span>
        </div>

        <div className="history-card-actions">
          <Button
            variant="secondary"
            size="small"
            onClick={() => onView(item)}
          >
            View
          </Button>
          <Button
            variant="primary"
            size="small"
            onClick={() => onDownload(item)}
          >
            Download
          </Button>
          <Button
            variant="secondary"
            size="small"
            onClick={() => onDelete(item)}
          >
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
};
