import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useHistory } from '../hooks/useHistory';
import { fetchHistory, deleteImage } from '../services/historyService';

// Mock the history service
vi.mock('../services/historyService', () => ({
  fetchHistory: vi.fn(),
  deleteImage: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useHistory - Session Filtering', () => {
  const mockHistoryItems = [
    {
      id: '1',
      original_filename: 'image1.jpg',
      model_id: 'swin2sr-2x',
      created_at: '2024-12-22T10:00:00Z', // After session start
      original_url: '/uploads/image1.jpg',
      processed_url: '/processed/image1.jpg',
    },
    {
      id: '2',
      original_filename: 'image2.jpg',
      model_id: 'swin2sr-4x',
      created_at: '2024-12-22T11:00:00Z', // After session start
      original_url: '/uploads/image2.jpg',
      processed_url: '/processed/image2.jpg',
    },
    {
      id: '3',
      original_filename: 'image3.jpg',
      model_id: 'qwen-edit',
      created_at: '2024-12-21T15:00:00Z', // Before session start
      original_url: '/uploads/image3.jpg',
      processed_url: '/processed/image3.jpg',
    },
  ];

  const mockAuthStorage = {
    state: {
      loginTime: '2024-12-22T09:00:00Z', // Session started before items 1 & 2, after item 3
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchHistory).mockResolvedValue({
      items: mockHistoryItems,
      total: mockHistoryItems.length,
      limit: 20,
      offset: 0,
    });
    vi.mocked(deleteImage).mockResolvedValue({
      message: 'Deleted',
      deleted_id: '1'
    });
    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockAuthStorage));
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Session Filtering', () => {
    it('shows all items when filter is "all"', async () => {
      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.sessionFilter).toBe('all');
        expect(result.current.items).toEqual(mockHistoryItems);
        expect(result.current.total).toBe(3);
      });
    });

    it('filters to current session items when filter is "current"', async () => {
      const { result } = renderHook(() => useHistory());

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        // Should filter to items created after session start (2024-12-22T09:00:00Z)
        // Items 1 & 2 are after, item 3 is before
        expect(result.current.items).toHaveLength(2);
        expect(result.current.total).toBe(2);
        expect(result.current.sessionFilter).toBe('current');
      });
    });

    it('resets to page 1 when changing filter', async () => {
      const { result } = renderHook(() => useHistory());

      act(() => {
        result.current.changePage(3);
      });

      await waitFor(() => {
        expect(result.current.currentPage).toBe(3);
      });

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(result.current.currentPage).toBe(1);
      });
    });

    it('handles missing session start time gracefully', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => useHistory());

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Unable to filter by current session. Session information not available.');
        expect(result.current.items).toEqual(mockHistoryItems); // Fallback to all
      });
    });

    it('handles invalid session start time gracefully', async () => {
      const invalidAuthStorage = {
        state: {
          loginTime: 'invalid-date',
        },
      };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(invalidAuthStorage));

      const { result } = renderHook(() => useHistory());

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(result.current.items).toEqual(mockHistoryItems); // Fallback to all
      });
    });
  });

  describe('In-Memory Pagination', () => {
    it('paginates filtered results correctly', async () => {
      const { result } = renderHook(() => useHistory(1)); // Page size 1

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(result.current.items).toHaveLength(1); // Only first item of filtered results
        expect(result.current.total).toBe(2); // Total filtered items
        expect(result.current.currentPage).toBe(1);
      });

      act(() => {
        result.current.changePage(2);
      });

      await waitFor(() => {
        expect(result.current.items).toHaveLength(1); // Second item
        expect(result.current.currentPage).toBe(2);
      });
    });

    it('clamps page to valid range', async () => {
      const { result } = renderHook(() => useHistory());

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(result.current.total).toBe(2);
      });

      act(() => {
        result.current.changePage(10); // Invalid page
      });

      await waitFor(() => {
        expect(result.current.currentPage).toBe(1); // Clamped to max valid page
      });
    });
  });

  describe('Filter State Management', () => {
    it('clears filter-related errors when switching to "all"', async () => {
      const { result } = renderHook(() => useHistory());

      // Set an error first
      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Unable to filter by current session. Session information not available.');
      });

      // Switch back to all
      act(() => {
        result.current.setSessionFilter('all');
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });

    it('skips reload when switching pages in current session mode with data', async () => {
      const { result } = renderHook(() => useHistory());

      act(() => {
        result.current.setSessionFilter('current');
      });

      await waitFor(() => {
        expect(fetchHistory).toHaveBeenCalledTimes(1);
      });

      // Clear call count
      vi.mocked(fetchHistory).mockClear();

      // Change page - should not trigger reload
      act(() => {
        result.current.changePage(2);
      });

      await waitFor(() => {
        expect(fetchHistory).not.toHaveBeenCalled();
      });
    });
  });
});