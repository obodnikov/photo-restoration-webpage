/**
 * HistoryList component
 * Displays grid of history items with pagination
 */

import React from 'react';
import type { HistoryItem } from '../types';
import { HistoryCard } from './HistoryCard';
import { Button } from '../../../components/Button';
import { Loader } from '../../../components/Loader';

export interface HistoryListProps {
  items: HistoryItem[];
  loading: boolean;
  total: number;
  currentPage: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onView: (item: HistoryItem) => void;
  onDelete: (item: HistoryItem) => void;
  onDownload: (item: HistoryItem) => void;
}

export const HistoryList: React.FC<HistoryListProps> = ({
  items,
  loading,
  total,
  currentPage,
  pageSize,
  onPageChange,
  onView,
  onDelete,
  onDownload,
}) => {
  const totalPages = Math.ceil(total / pageSize);
  const hasNextPage = currentPage < totalPages;
  const hasPrevPage = currentPage > 1;

  if (loading) {
    return <Loader text="Loading history..." size="large" />;
  }

  if (items.length === 0) {
    return (
      <div className="history-empty">
        <div className="empty-icon">📷</div>
        <h3>No History Yet</h3>
        <p>Start by restoring your first image!</p>
      </div>
    );
  }

  return (
    <div className="history-list">
      <div className="history-grid">
        {items.map((item) => (
          <HistoryCard
            key={item.id}
            item={item}
            onView={onView}
            onDelete={onDelete}
            onDownload={onDownload}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="history-pagination">
          <Button
            variant="secondary"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={!hasPrevPage}
          >
            Previous
          </Button>

          <span className="pagination-info">
            Page {currentPage} of {totalPages} ({total} total)
          </span>

          <Button
            variant="secondary"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!hasNextPage}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};
