/**
 * useHistory hook
 * Manages history state and operations
 */

import { useState, useEffect } from 'react';
import { fetchHistory, deleteImage } from '../services/historyService';
import type { HistoryItem } from '../types';

export interface UseHistoryResult {
  items: HistoryItem[];
  loading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
  pageSize: number;
  loadHistory: () => Promise<void>;
  changePage: (page: number) => void;
  removeItem: (imageId: string) => Promise<void>;
  setPageSize: (size: number) => void;
}

export function useHistory(initialPageSize: number = 20): UseHistoryResult {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const offset = (currentPage - 1) * pageSize;
      console.log('[useHistory] Loading history:', { pageSize, offset, currentPage });

      const response = await fetchHistory(pageSize, offset);

      console.log('[useHistory] History loaded successfully:', {
        itemCount: response.items.length,
        total: response.total
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (err: any) {
      console.error('[useHistory] Error loading history:', err);
      console.error('[useHistory] Error details:', {
        message: err.message,
        status: err.status,
        name: err.name,
      });

      // Provide more specific error messages
      if (err.status === 401) {
        setError('Authentication failed. Please log in again.');
      } else if (err.message && err.message.includes('Authentication')) {
        setError('Authentication required. Please log in again.');
      } else {
        setError('Failed to load history. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const changePage = (page: number) => {
    setCurrentPage(page);
  };

  const removeItem = async (imageId: string) => {
    try {
      await deleteImage(imageId);

      // Reload history after deletion
      await loadHistory();
    } catch (err: any) {
      console.error('Error deleting image:', err);
      setError('Failed to delete image. Please try again.');
      throw err;
    }
  };

  // Load history when page or pageSize changes
  useEffect(() => {
    loadHistory();
  }, [currentPage, pageSize]);

  return {
    items,
    loading,
    error,
    total,
    currentPage,
    pageSize,
    loadHistory,
    changePage,
    removeItem,
    setPageSize,
  };
}
