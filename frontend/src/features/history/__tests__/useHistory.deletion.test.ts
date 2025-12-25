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

describe('useHistory - Item Deletion', () => {
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

  describe('Item Deletion', () => {
    it('deletes item and reloads history', async () => {
      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.items).toHaveLength(2);
      });

      await act(async () => {
        await result.current.removeItem('1');
      });

      expect(deleteImage).toHaveBeenCalledWith('1');
      expect(fetchHistory).toHaveBeenCalledTimes(2); // Initial + reload after delete
    });

    it('handles deletion errors gracefully', async () => {
      vi.mocked(deleteImage).mockRejectedValue(new Error('Delete failed'));

      const { result } = renderHook(() => useHistory());

      await expect(result.current.removeItem('1')).rejects.toThrow('Delete failed');

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to delete image. Please try again.');
      });
    });

    it('handles 401 authentication errors during deletion', async () => {
      const authError = new Error('Unauthorized');
      (authError as any).status = 401;
      vi.mocked(deleteImage).mockRejectedValue(authError);

      const { result } = renderHook(() => useHistory());

      await expect(result.current.removeItem('1')).rejects.toThrow('Unauthorized');

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to delete image. Please try again.');
      });
    });

    it('handles network errors during deletion', async () => {
      vi.mocked(deleteImage).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useHistory());

      await expect(result.current.removeItem('1')).rejects.toThrow('Network error');

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to delete image. Please try again.');
      });
    });

    it('handles non-Error exceptions during deletion', async () => {
      vi.mocked(deleteImage).mockRejectedValue('String error');

      const { result } = renderHook(() => useHistory());

      await expect(result.current.removeItem('1')).rejects.toThrow('String error');

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to delete image. Please try again.');
      });
    });

    it('reloads history after successful deletion', async () => {
      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.items).toHaveLength(2);
      });

      // Clear initial call count
      vi.mocked(fetchHistory).mockClear();

      await act(async () => {
        await result.current.removeItem('1');
      });

      // Should reload history after deletion
      expect(fetchHistory).toHaveBeenCalledTimes(1);
    });

    it('does not reload history if deletion fails', async () => {
      vi.mocked(deleteImage).mockRejectedValue(new Error('Delete failed'));

      const { result } = renderHook(() => useHistory());

      await waitFor(() => {
        expect(result.current.items).toHaveLength(2);
      });

      // Clear initial call count
      vi.mocked(fetchHistory).mockClear();

      try {
        await result.current.removeItem('1');
      } catch {
        // Expected to throw
      }

      // Should not reload history if deletion fails
      expect(fetchHistory).not.toHaveBeenCalled();
    });

    it('maintains current filter and pagination after deletion reload', async () => {
      const { result } = renderHook(() => useHistory());

      // Set filter and page
      act(() => {
        result.current.setSessionFilter('current');
        result.current.changePage(2);
      });

      await waitFor(() => {
        expect(result.current.sessionFilter).toBe('current');
        expect(result.current.currentPage).toBe(1); // Reset due to filter change
      });

      // Clear call counts
      vi.mocked(fetchHistory).mockClear();

      await act(async () => {
        await result.current.removeItem('2');
      });

      // Should reload with current filter settings
      expect(fetchHistory).toHaveBeenCalledWith(20, 0); // Page 1, current filter triggers bulk fetch
    });
  });
});