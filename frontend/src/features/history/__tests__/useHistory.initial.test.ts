import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
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

describe('useHistory - Initial State', () => {
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

  describe('Initial State', () => {
    it('initializes with correct default state', () => {
      const { result } = renderHook(() => useHistory());

      expect(result.current.items).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.total).toBe(0);
      expect(result.current.currentPage).toBe(1);
      expect(result.current.pageSize).toBe(20);
      expect(result.current.sessionFilter).toBe('all');
      expect(result.current.currentSessionStart).toBeNull();
    });

    it('loads session start time from localStorage on mount', async () => {
      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(localStorageMock.getItem).toHaveBeenCalledWith('auth-storage');
      });

      await waitFor(() => {
        expect(result.current.currentSessionStart).toBe('2024-12-22T09:00:00Z');
      });
    });

    it('handles missing auth storage gracefully', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.currentSessionStart).toBeNull();
      });
    });

    it('handles invalid auth storage JSON gracefully', async () => {
      localStorageMock.getItem.mockReturnValue('invalid json');

      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.currentSessionStart).toBeNull();
      });
    });
  });
});