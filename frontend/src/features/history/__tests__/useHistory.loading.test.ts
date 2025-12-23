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

describe('useHistory - Loading and Errors', () => {
  const mockHistoryItems = [
    {
      id: '1',
      original_filename: 'image1.jpg',
      model_id: 'swin2sr-2x',
      created_at: '2024-12-22T10:00:00Z',
      original_url: '/uploads/image1.jpg',
      processed_url: '/processed/image1.jpg',
    },
    {
      id: '2',
      original_filename: 'image2.jpg',
      model_id: 'swin2sr-4x',
      created_at: '2024-12-22T11:00:00Z',
      original_url: '/uploads/image2.jpg',
      processed_url: '/processed/image2.jpg',
    },
  ];

  const mockAuthStorage = {
    state: {
      loginTime: '2024-12-22T09:00:00Z',
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

  describe('Normal History Loading', () => {
    it('loads history on mount for "all" filter', async () => {
      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(fetchHistory).toHaveBeenCalledWith(20, 0);
      });

      await waitFor(() => {
        expect(result.current.items).toEqual(mockHistoryItems);
        expect(result.current.total).toBe(2);
        expect(result.current.loading).toBe(false);
      });
    });

    it('handles loading state correctly', async () => {
      let resolveFetch: (value: any) => void;
      const fetchPromise = new Promise((resolve) => {
        resolveFetch = resolve;
      });
      vi.mocked(fetchHistory).mockReturnValue(fetchPromise as Promise<any>);

      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.loading).toBe(true);
      });

      resolveFetch!({ items: mockHistoryItems, total: 2, limit: 20, offset: 0 });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('handles fetch errors with user-friendly messages', async () => {
      vi.mocked(fetchHistory).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to load history. Please try again.');
        expect(result.current.loading).toBe(false);
      });
    });

    it('handles 401 authentication errors specifically', async () => {
      const authError = new Error('Unauthorized');
      (authError as any).status = 401;
      vi.mocked(fetchHistory).mockRejectedValue(authError);

      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.error).toBe('Authentication failed. Please log in again.');
      });
    });
  });
});