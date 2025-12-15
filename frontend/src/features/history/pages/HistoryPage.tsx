/**
 * HistoryPage - Page for viewing restoration history
 */

import React, { useState } from 'react';
import { useHistory } from '../hooks/useHistory';
import { HistoryList } from '../components/HistoryList';
import type { HistoryItem } from '../types';
import { ErrorMessage } from '../../../components/ErrorMessage';
import { ImageComparison } from '../../restoration/components/ImageComparison';
import type { ImageViewMode } from '../../restoration/types';
import { config } from '../../../config/config';

export const HistoryPage: React.FC = () => {
  const {
    items,
    loading,
    error,
    total,
    currentPage,
    pageSize,
    changePage,
    removeItem,
  } = useHistory(20);

  const [viewingItem, setViewingItem] = useState<HistoryItem | null>(null);
  const [viewMode, setViewMode] = useState<ImageViewMode>('both');
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleView = (item: HistoryItem) => {
    setViewingItem(item);
    setViewMode('both');
  };

  const handleDelete = async (item: HistoryItem) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${item.original_filename}"?`
    );

    if (!confirmed) return;

    try {
      setDeleteError(null);
      await removeItem(item.id);

      // Close viewer if viewing deleted item
      if (viewingItem?.id === item.id) {
        setViewingItem(null);
      }
    } catch (err) {
      setDeleteError('Failed to delete image. Please try again.');
    }
  };

  const handleDownload = (item: HistoryItem) => {
    const baseUrl = config.apiBaseUrl.replace('/api/v1', '');
    const downloadUrl = `${baseUrl}/api/v1/restore/${item.id}/download`;

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `restored-${item.original_filename}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadViewing = () => {
    if (viewingItem) {
      handleDownload(viewingItem);
    }
  };

  const baseUrl = config.apiBaseUrl.replace('/api/v1', '');

  return (
    <div className="history-page">
      <div className="container">
        <div className="page-header">
          <h1>Restoration History</h1>
          <p className="page-subtitle">
            View, download, or delete your restored images
          </p>
        </div>

        {error && (
          <ErrorMessage
            message={error}
            title="History Error"
          />
        )}

        {deleteError && (
          <ErrorMessage
            message={deleteError}
            title="Delete Error"
            onClose={() => setDeleteError(null)}
          />
        )}

        {viewingItem ? (
          <>
            <section className="history-section">
              <div className="viewer-header">
                <h2>{viewingItem.original_filename}</h2>
                <button
                  className="btn btn-secondary"
                  onClick={() => setViewingItem(null)}
                >
                  ← Back to History
                </button>
              </div>

              <ImageComparison
                originalUrl={`${baseUrl}${viewingItem.original_path}`}
                processedUrl={`${baseUrl}${viewingItem.processed_path}`}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                onDownload={handleDownloadViewing}
              />
            </section>
          </>
        ) : (
          <section className="history-section">
            <HistoryList
              items={items}
              loading={loading}
              total={total}
              currentPage={currentPage}
              pageSize={pageSize}
              onPageChange={changePage}
              onView={handleView}
              onDelete={handleDelete}
              onDownload={handleDownload}
            />
          </section>
        )}
      </div>
    </div>
  );
};
