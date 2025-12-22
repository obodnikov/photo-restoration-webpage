/**
 * useHistory hook
 * Manages history state and operations
 */

import { useState, useEffect } from 'react';
import { fetchHistory, deleteImage } from '../services/historyService';
import type { HistoryItem } from '../types';

export type SessionFilter = 'all' | 'current';

export interface UseHistoryResult {
  items: HistoryItem[];
  loading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
  pageSize: number;
  sessionFilter: SessionFilter;
  currentSessionStart: string | null;
  loadHistory: () => Promise<void>;
  changePage: (page: number) => void;
  removeItem: (imageId: string) => Promise<void>;
  setPageSize: (size: number) => void;
  setSessionFilter: (filter: SessionFilter) => void;
}

export function useHistory(initialPageSize: number = 20): UseHistoryResult {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [allHistoryItems, setAllHistoryItems] = useState<HistoryItem[]>([]); // Store ALL history items for filtering
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [sessionFilter, setSessionFilter] = useState<SessionFilter>('all');
  const [currentSessionStart, setCurrentSessionStart] = useState<string | null>(null);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('[useHistory] Loading history:', {
        sessionFilter,
        currentPage,
        pageSize
      });

      // If filtering by current session, fetch ALL items to filter client-side
      // Otherwise, use normal pagination
      if (sessionFilter === 'current') {
        console.log('[useHistory] Fetching all items for current session filter');

        // Fetch all items (use large limit to get everything)
        const response = await fetchHistory(1000, 0);

        console.log('[useHistory] All history loaded for filtering:', {
          totalItems: response.items.length,
        });

        // Store all items for filtering
        setAllHistoryItems(response.items);
        setTotal(response.items.length);
      } else {
        // Normal pagination - fetch only current page
        const offset = (currentPage - 1) * pageSize;
        const response = await fetchHistory(pageSize, offset);

        console.log('[useHistory] Page loaded:', {
          itemCount: response.items.length,
          total: response.total
        });

        // Store current page items and set total from backend
        setAllHistoryItems(response.items);
        setTotal(response.total);
      }
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

  // Get current session start time from localStorage (token creation time)
  useEffect(() => {
    const authStorage = localStorage.getItem('auth-storage');
    if (!authStorage) {
      console.warn('[useHistory] No auth-storage found in localStorage');
      return;
    }

    try {
      const authData = JSON.parse(authStorage);

      // Validate expected structure
      if (!authData) {
        console.warn('[useHistory] auth-storage is null or undefined');
        return;
      }

      if (!authData.state) {
        console.warn('[useHistory] auth-storage missing state property');
        return;
      }

      if (!authData.state.loginTime) {
        console.warn('[useHistory] auth-storage.state missing loginTime property');
        return;
      }

      // Validate loginTime is a valid date string
      const loginTime = authData.state.loginTime;
      const testDate = new Date(loginTime);
      if (isNaN(testDate.getTime())) {
        console.warn('[useHistory] loginTime is not a valid date:', loginTime);
        return;
      }

      setCurrentSessionStart(loginTime);
      console.log('[useHistory] Session start time loaded:', loginTime);
    } catch (e) {
      console.error('[useHistory] Error parsing auth storage:', e);
      console.error('[useHistory] auth-storage content:', authStorage);
    }
  }, []);

  // Apply client-side filtering when filter changes or items load
  useEffect(() => {
    if (sessionFilter === 'all') {
      // Clear any previous filter-related errors
      if (error?.includes('Unable to filter by current session')) {
        setError(null);
      }
      // Show all loaded items (paginated)
      setItems(allHistoryItems);
    } else if (sessionFilter === 'current') {
      // Check if we have session start time
      if (!currentSessionStart) {
        console.warn('[useHistory] Current session filter selected but no session start time available');
        setError('Unable to filter by current session. Session information not available.');
        setItems(allHistoryItems); // Fallback to showing all
        return;
      }

      // Filter items created after current session started
      try {
        const sessionStartTime = new Date(currentSessionStart).getTime();

        // Validate session start time
        if (isNaN(sessionStartTime)) {
          console.warn('[useHistory] Invalid session start time, showing all items');
          setItems(allHistoryItems);
          return;
        }

        const filtered = allHistoryItems.filter((item) => {
          // Validate item created_at date
          if (!item.created_at) {
            console.warn('[useHistory] Item missing created_at field:', item.id);
            return false; // Exclude items without valid dates
          }

          const itemTime = new Date(item.created_at).getTime();

          // Check if date parsing was successful
          if (isNaN(itemTime)) {
            console.warn('[useHistory] Invalid created_at date for item:', item.id, item.created_at);
            return false; // Exclude items with invalid dates
          }

          return itemTime >= sessionStartTime;
        });

        setItems(filtered);
        setTotal(filtered.length); // Update total to reflect filtered count
        console.log('[useHistory] Filtered to current session:', {
          total: allHistoryItems.length,
          filtered: filtered.length,
          sessionStart: currentSessionStart,
        });
      } catch (err) {
        console.error('[useHistory] Error filtering by session:', err);
        // Fallback to showing all items if filtering fails
        setItems(allHistoryItems);
      }
    } else {
      // If current session filter selected but no session start time, show all
      setItems(allHistoryItems);
    }
  }, [sessionFilter, allHistoryItems, currentSessionStart]);

  // Load history when page, pageSize, or filter changes
  useEffect(() => {
    loadHistory();
  }, [currentPage, pageSize, sessionFilter]);

  return {
    items,
    loading,
    error,
    total,
    currentPage,
    pageSize,
    sessionFilter,
    currentSessionStart,
    loadHistory,
    changePage,
    removeItem,
    setPageSize,
    setSessionFilter,
  };
}
